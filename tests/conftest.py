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
import pytest

from http_spammer.spammer import LoadSpammer, LatencySpamer
from http_spammer.requests import GetRequest, BodyRequest


@pytest.fixture(autouse=True)
def num_requests():
    return 100


@pytest.fixture(autouse=True)
def requests_per_second():
    return 25


@pytest.fixture(autouse=True)
def latency_threshold():
    return 0.5


@pytest.fixture(autouse=True)
def num_workers():
    return 3


@pytest.fixture(autouse=True)
def load_test():
    return LoadSpammer()


@pytest.fixture(autouse=True)
def latency_test():
    return LatencySpamer()


@pytest.fixture(autouse=True)
def test_url():
    return 'http://httpbin.org/anything'


@pytest.fixture(autouse=True)
def get_request(test_url):
    return GetRequest(url=test_url,
                      headers={'Content-type': 'text/plain'})


@pytest.fixture(autouse=True)
def body_request(test_url):
    return BodyRequest(url=test_url,
                       headers={'Content-type': 'application/json'},
                       data={'foo': 'bar'})
