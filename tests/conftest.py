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

from http_spammer import TestConfig, load_from_file
from http_spammer.spammer import LoadSpammer, LatencySpammer
from http_spammer.request import GetRequest, BodyRequest


@pytest.fixture(autouse=True)
def num_requests():
    return 100


@pytest.fixture(autouse=True)
def rps_static():
    return 50


@pytest.fixture(autouse=True)
def rps_start(rps_static):
    return rps_static - 25


@pytest.fixture(autouse=True)
def rps_end(rps_static):
    return rps_static + 25


@pytest.fixture(autouse=True)
def duration(num_requests, rps_static):
    return num_requests / rps_static


@pytest.fixture(autouse=True)
def latency_threshold():
    return 0.7


@pytest.fixture(autouse=True)
def num_workers():
    return 1


@pytest.fixture(autouse=False)
def load_spammer():
    return LoadSpammer()


@pytest.fixture(autouse=False)
def latency_spammer():
    return LatencySpammer()


@pytest.fixture(autouse=True)
def test_url():
    return 'http://httpbin.org/anything'


@pytest.fixture(autouse=True)
def test_file():
    return 'tests/test-config.yaml'


@pytest.fixture(autouse=True)
def test_file_url():
    return 'https://raw.githubusercontent.com/chrislarson1/http-spammer/main/tests/test-config.yaml'


@pytest.fixture(autouse=False)
def test_config_dict(test_file):
    return load_from_file(test_file)


@pytest.fixture(autouse=False)
def test_config(test_config_dict):
    return TestConfig(**test_config_dict)


@pytest.fixture(autouse=False)
def get_request(test_url):
    return GetRequest(url=test_url,
                      headers={'Content-type': 'text/plain'})


@pytest.fixture(autouse=False)
def body_request(test_url):
    return BodyRequest(url=test_url,
                       headers={'Content-type': 'application/json'},
                       data={'foo': 'bar'})
