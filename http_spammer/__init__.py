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
import copy
from typing import List, Tuple, Union, Generator
from multiprocessing import cpu_count

import requests
import numpy as np
from pydantic import BaseModel

from http_spammer.request import GetRequest, BodyRequest
from http_spammer.contraints import MAX_WRKR_RPS, MIN_RPS, \
    MIN_SEG_DUR, MIN_SEG_REQ
from http_spammer.worker import spam_runner, LAT_RPS
from http_spammer.metrics import LoadTestResult

__all__ = ['TestConfig', 'LoadTest', 'LoadTestResult',
           'load_from_file', 'load_from_url']


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


def load_from_file(fp: str):
    return yaml.load(open(fp, 'r'), Loader=yaml.FullLoader)


def load_from_url(url: str):
    return yaml.load(requests.get(url).text, Loader=yaml.FullLoader)


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


def parse_constructor_args(test_spec):
    if type(test_spec) == str:
        is_url = re.match(url_pattern, test_spec)
        if is_url:
            test_spec = load_from_url(test_spec)
        else:
            test_spec = load_from_file(test_spec)
    if type(test_spec) == dict:
        config = TestConfig(**test_spec)
    else:
        assert isinstance(test_spec, TestConfig)
        config = test_spec
    validate_test_config(config)
    return config


class LoadTest:

    def __init__(self, test_spec: Union[str, dict, TestConfig]):
        self.config = parse_constructor_args(test_spec)
        self.segments = self.generate_requests()

    def generate_requests(self):
        requests = []
        for i, segment in enumerate(self.config.segments):
            N = int(((segment.startRps + segment.endRps) / 2) * segment.duration)
            _requests = np.random.choice(self.config.requests, size=N).tolist()
            rate = (segment.endRps - segment.startRps) / segment.duration
            end_rps = segment.startRps
            if rate == 0.:
                num_subsegs = segment.duration // MIN_SEG_DUR
                subseg_size = len(_requests) // num_subsegs
                while _requests:
                    seg_requests = [_requests.pop() for _ in range(subseg_size)]
                    duration = MIN_SEG_DUR
                    num_remaining = len(_requests)
                    if num_remaining < MIN_SEG_REQ:
                        duration += duration * (num_remaining / MIN_SEG_REQ)
                        seg_requests.extend([_requests.pop() for _ in range(len(_requests))])
                    requests.append((i, seg_requests, end_rps, end_rps, duration))
            else:
                while _requests:
                    start_rps = end_rps
                    end_rps = start_rps + MIN_SEG_DUR * rate
                    mean_rps = (end_rps + start_rps) / 2
                    is_last_subseg = (end_rps > segment.endRps) \
                        if rate > 0 else (end_rps < segment.endRps)
                    if not is_last_subseg:
                        seg_requests = [_requests.pop(0)
                                        for _ in range(int(MIN_SEG_DUR * mean_rps))]
                        duration = MIN_SEG_DUR
                        if len(_requests) < MIN_SEG_REQ:
                            seg_requests.extend([_requests.pop(0)
                                                 for _ in range(len(_requests))])
                            end_rps = segment.endRps
                            mean_rps = (end_rps + start_rps) / 2
                            duration = len(seg_requests) / mean_rps
                    else:
                        seg_requests = [_requests.pop(0) for _ in range(len(_requests))]
                        duration = len(seg_requests) / mean_rps
                    requests.append((i, seg_requests, start_rps, end_rps, duration))
        return requests

    def run(self) -> Generator[Tuple[int, int, LoadTestResult], None, None]:
        for cycle in range(self.config.cycles):
            for segment, requests, start_rps, end_rps, duration in self.segments:
                yield cycle, segment, spam_runner(self.config.numClients,
                                                  copy.deepcopy(requests),
                                                  duration,
                                                  start_rps,
                                                  end_rps)
