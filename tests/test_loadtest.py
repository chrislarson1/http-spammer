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
from http_spammer import LoadTest


def test_loadtest(test_file, latency_threshold):
    load_test = LoadTest(test_file)
    results = []
    for result in load_test.run():
        results.append(result)
    assert len(results) == len(load_test.config.segments)
    for result in results:
        assert result.metrics.server_requests_per_second / \
               result.metrics.client_requests_per_second >= \
               latency_threshold
