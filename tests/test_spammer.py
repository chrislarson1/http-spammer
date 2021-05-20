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


def test_load_get(get_request,
                  num_requests,
                  requests_per_second,
                  latency_threshold,
                  load_test: LoadSpammer):
    responses, timestamps = load_test.run(requests=[get_request] * num_requests,
                                          requests_per_second=requests_per_second)
    rps = len(responses) / (timestamps[-1][1] - timestamps[0][0])
    assert rps / requests_per_second >= latency_threshold


@pytest.mark.parametrize('method', ('POST', 'PUT', 'PATCH', 'DELETE'))
def test_load_with_body(method,
                        body_request,
                        num_requests,
                        requests_per_second,
                        latency_threshold,
                        load_test: LoadSpammer):
    request = body_request
    request.method = method
    responses, timestamps = load_test.run(requests=[request] * num_requests,
                                          requests_per_second=requests_per_second)
    rps = len(responses) / (timestamps[-1][1] - timestamps[0][0])
    assert rps / requests_per_second >= latency_threshold


def test_latency_get(get_request,
                     num_requests,
                     requests_per_second,
                     latency_threshold,
                     latency_test: LatencySpamer):
    responses, timestamps = latency_test.run(requests=[get_request] * num_requests,
                                             requests_per_second=requests_per_second)
    rps = len(responses) / (timestamps[-1][1] - timestamps[0][0])
    assert rps / requests_per_second >= latency_threshold


@pytest.mark.parametrize('method', ('POST', 'PUT', 'PATCH', 'DELETE'))
def test_load_with_body(method,
                        body_request,
                        num_requests,
                        requests_per_second,
                        latency_threshold,
                        latency_test: LatencySpamer):
    request = body_request
    request.method = method
    responses, timestamps = latency_test.run(requests=[request] * num_requests,
                                             requests_per_second=requests_per_second)
    rps = len(responses) / (timestamps[-1][1] - timestamps[0][0])
    assert rps / requests_per_second >= latency_threshold
