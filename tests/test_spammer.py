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

from http_spammer.spammer import LoadSpammer, LatencySpammer, throttle
from http_spammer.timing import now
from http_spammer import LAT_RPS


def test_throttle_static_load_no_wait():
    wait = throttle(now() - 5, 5, 10, 1, 1)
    assert not wait


def test_throttle_static_load_wait():
    wait = throttle(now() - 5 + 0.001, 5, 10, 1, 1)
    assert wait


def test_throttle_dynamic_load_no_wait():
    wait = throttle(now() - 5, 2.5, 10, 0, 2)
    assert not wait


def test_throttle_dynamic_load_wait():
    wait = throttle(now() - 5 + 0.001, 2.5, 10, 0, 2)
    assert wait


def test_load_get(get_request,
                  num_requests,
                  duration,
                  rps_static,
                  rps_start,
                  rps_end,
                  latency_threshold,
                  load_spammer: LoadSpammer):
    responses, timestamps = load_spammer.run(requests=[get_request] * num_requests,
                                             duration=duration,
                                             rps_start=rps_static,
                                             rps_end=rps_static)
    rps = len(responses) / (timestamps[-1][1] - timestamps[0][0])
    assert rps / rps_static >= latency_threshold
    responses, timestamps = load_spammer.run(requests=[get_request] * num_requests,
                                             duration=duration,
                                             rps_start=rps_start,
                                             rps_end=rps_end)
    rps = len(responses) / (timestamps[-1][1] - timestamps[0][0])
    assert rps / rps_static >= latency_threshold


@pytest.mark.parametrize('method', ('POST', 'PUT', 'PATCH', 'DELETE'))
def test_load_with_body(method,
                        body_request,
                        num_requests,
                        duration,
                        rps_static,
                        rps_start,
                        rps_end,
                        latency_threshold,
                        load_spammer: LoadSpammer):
    request = body_request
    request.method = method
    responses, timestamps = load_spammer.run(requests=[request] * num_requests,
                                             duration=duration,
                                             rps_start=rps_static,
                                             rps_end=rps_static)
    rps_measured = len(responses) / (timestamps[-1][1] - timestamps[0][0])
    assert rps_measured / rps_static >= latency_threshold
    responses, timestamps = load_spammer.run(requests=[request] * num_requests,
                                             duration=duration,
                                             rps_start=rps_start,
                                             rps_end=rps_end)
    rps_measured = len(responses) / (timestamps[-1][1] - timestamps[0][0])
    assert rps_measured / rps_static >= latency_threshold


def test_latency_get(get_request,
                     duration,
                     latency_threshold,
                     latency_spammer: LatencySpammer):
    responses, timestamps = latency_spammer.run(requests=[get_request] * 10,
                                                duration=duration,
                                                rps_start=LAT_RPS,
                                                rps_end=LAT_RPS)
    rps = len(responses) / (timestamps[-1][1] - timestamps[0][0])
    assert rps / LAT_RPS >= latency_threshold


@pytest.mark.parametrize('method', ('POST', 'PUT', 'PATCH', 'DELETE'))
def test_latency_with_body(method,
                           body_request,
                           duration,
                           latency_threshold,
                           latency_spammer: LatencySpammer):
    request = body_request
    request.method = method
    responses, timestamps = latency_spammer.run(requests=[request] * 2,
                                                duration=duration,
                                                rps_start=LAT_RPS,
                                                rps_end=LAT_RPS)
    rps = len(responses) / (timestamps[-1][1] - timestamps[0][0])
    assert rps / LAT_RPS >= latency_threshold
