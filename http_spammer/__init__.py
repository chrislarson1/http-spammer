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
import sys
import yaml
from typing import List, Union

import requests
from pydantic import BaseModel

from http_spammer.request import GetRequest, BodyRequest


class SegmentType(BaseModel):
    startRps: int
    endRps: int
    duration: int


class TestConfig(BaseModel):
    name: str
    cycles: int
    segments: List[SegmentType]
    requests: List[Union[GetRequest, BodyRequest]]



url_pattern = "(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]" \
              "\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?" \
              ":\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"


class LoadTest:

    def __init__(self, test_file_or_url: str):
        is_url = re.match(url_pattern, test_file_or_url)
        print(is_url)
        if is_url:
            try:
                spec = yaml.load(requests.get(test_file_or_url).text,
                                 Loader=yaml.FullLoader)
            except Exception as exc:
                print(exc)
                sys.exit(1)
        else:
            try:
                spec = yaml.load(open(test_file_or_url, 'r'),
                                 Loader=yaml.FullLoader)
            except Exception as exc:
                print(exc)
                sys.exit(1)
        self.config = TestConfig(**spec)

    def run(self):
        pass
