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
from http_spammer.main import HttpRequest, LoadTest


def test_http_loadtest_get(test_url: str, load_test: LoadTest):
    message = HttpRequest(method='GET')
    rps = 25
    result = load_test.run(test_url,
                           messages=[message] * 100,
                           requests_per_second=rps)
    assert result.metrics.server_requests_per_second / rps > 0.85


def test_http_loadtest_post(test_url: str, load_test: LoadTest):
    message = HttpRequest(method='POST', data={'key': 'value'})
    rps = 25
    result = load_test.run(test_url,
                           messages=[message] * 100,
                           requests_per_second=rps)
    assert result.metrics.server_requests_per_second / rps > 0.85


def test_http_loadtest_put(test_url: str, load_test: LoadTest):
    message = HttpRequest(method='PUT', data={'key': 'value'})
    rps = 25
    result = load_test.run(test_url,
                           messages=[message] * 100,
                           requests_per_second=rps)
    assert result.metrics.server_requests_per_second / rps > 0.85


def test_http_loadtest_patch(test_url: str, load_test: LoadTest):
    message = HttpRequest(method='PATCH', data={'key': 'value'})
    rps = 25
    result = load_test.run(test_url,
                           messages=[message] * 100,
                           requests_per_second=rps)
    assert result.metrics.server_requests_per_second / rps > 0.85


def test_http_loadtest_delete(test_url: str, load_test: LoadTest):
    message = HttpRequest(method='DELETE', data={'key': 'value'})
    rps = 25
    result = load_test.run(test_url,
                           messages=[message] * 100,
                           requests_per_second=rps)
    assert result.metrics.server_requests_per_second / rps > 0.85
