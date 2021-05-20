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
import numpy as np

from http_spammer.worker import spam_runner


def test_spam_runner(num_workers,
                     get_request,
                     body_request,
                     num_requests,
                     requests_per_second,
                     latency_threshold):
    requests = []
    for i in range(num_requests):
        req = np.random.choice((get_request, body_request))
        if getattr(req, 'data', None):
            req.method = np.random.choice(('PUT', 'POST', 'PATCH', 'DELETE'))
        requests.append(req)
    result = spam_runner(num_workers, requests, requests_per_second)
    assert result.metrics.server_requests_per_second / \
           requests_per_second >= latency_threshold
    assert len(result.responses) == num_requests
