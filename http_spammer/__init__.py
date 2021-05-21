# -------------------------------------------------------------------
# Copyright 2021 http-spammer authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.
# -------------------------------------------------------------------
import re
import yaml
from typing import List, Union
from multiprocessing import cpu_count

import requests
import numpy as np
from pydantic import BaseModel

from http_spammer.request import GetRequest, BodyRequest
from http_spammer.contraints import MAX_WRKR_RPS, MIN_RPS, \
    MIN_SEG_DUR, MIN_SEG_REQ
from http_spammer.worker import spam_runner, LAT_RPS
from http_spammer.metrics import LoadTestResult


class SegmentType(BaseModel):
    startRps: int
    endRps: int
    duration: int


class TestConfig(BaseModel):
    name: str
    cycles: int
    segments: List[SegmentType]
    requests: List[Union[GetRequest, BodyRequest]]
    numClients: int = 1


url_pattern = "(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]" \
              "\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?" \
              ":\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"


def validate_test_config(config: TestConfig):
    if config.numClients > cpu_count() - 1:
        raise RuntimeError(f'numClient exceeds available cpus '
                           f'({config.numClients} vs. {cpu_count()})')
    max_rps = max([max(seg.startRps, seg.endRps) / config.numClients
                   for seg in config.segments])
    if max_rps > MAX_WRKR_RPS:
        raise RuntimeError(
            f'max segment RPS exceeds max allowable ({max_rps} vs {MAX_WRKR_RPS})')
    if min([seg.duration for seg in config.segments]) < MIN_SEG_DUR:
        raise RuntimeError(f'segment duration must be >= {MIN_SEG_DUR})')


def load_from_file(fp: str):
    return yaml.load(open(fp, 'r'), Loader=yaml.FullLoader)


def load_from_url(url: str):
    return yaml.load(requests.get(url).text, Loader=yaml.FullLoader)


class LoadTest:

    def __init__(self, test_file_or_url: str):
        is_url = re.match(url_pattern, test_file_or_url)
        if is_url:
            spec = load_from_url(test_file_or_url)
        else:
            spec = load_from_file(test_file_or_url)
        self.config = TestConfig(**spec)
        validate_test_config(self.config)

    def run(self) -> List[LoadTestResult]:
        segment_requests = []
        for segment in self.config.segments:
            N = int(((segment.startRps + segment.endRps) / 2) * segment.duration)
            segment_requests.append(
                np.random.choice(self.config.requests, size=N).tolist())
        results = []
        for segment, requests in zip(self.config.segments, segment_requests):
            results.append(
                spam_runner(self.config.numClients,
                            requests,
                            segment.duration,
                            segment.startRps,
                            segment.endRps)
            )
        return results
