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
from dataclasses import dataclass, asdict
from typing import List, Union

import numpy as np

from http_spammer.timing import Timestamp

__all__ = ['get_result', 'LoadTestResult']


@dataclass()
class LoadTestMetrics:

    num_requests: int
    test_duration_seconds: float
    client_requests_per_second: float
    server_requests_per_second: float
    server_latency_mean_seconds: float
    server_latency_std_seconds: float
    server_latency_max_seconds: float
    server_latency_p50_seconds: float
    server_latency_p90_seconds: float
    server_latency_p95_seconds: float
    server_latency_p99_seconds: float
    server_latency_p99p9_seconds: float
    server_latency_p99p99_seconds: float

    def dict(self):
        return asdict(self)

    @classmethod
    def build_from_dict(cls, metrics_dict: dict):
        return cls(**metrics_dict)

    @classmethod
    def build(cls,
              timestamps: List[Timestamp],
              latency_timestamps: List[Timestamp]):
        num_requests = len(timestamps)
        send_duration = round(float(timestamps[-1][0] - timestamps[0][0]), 5)
        test_duration = round(float(timestamps[-1][1] - timestamps[0][0]), 5)
        client_load_measured = round(num_requests / send_duration, 5)
        latencies = [tstamp[1] - tstamp[0] for tstamp in latency_timestamps]
        return cls(
            test_duration_seconds=test_duration,
            num_requests=num_requests,
            client_requests_per_second=client_load_measured,
            server_requests_per_second=round(num_requests / test_duration, 5),
            server_latency_mean_seconds=round(np.mean(latencies), 9),
            server_latency_std_seconds=round(np.std(latencies), 9),
            server_latency_max_seconds=round(max(latencies), 9),
            server_latency_p50_seconds=round(np.percentile(latencies, 50), 9),
            server_latency_p90_seconds=round(np.percentile(latencies, 90), 9),
            server_latency_p95_seconds=round(np.percentile(latencies, 95), 9),
            server_latency_p99_seconds=round(np.percentile(latencies, 99), 9),
            server_latency_p99p9_seconds=round(np.percentile(latencies, 99.9), 9),
            server_latency_p99p99_seconds=round(np.percentile(latencies, 99.99), 9)
        )


@dataclass()
class LoadTestResult:

    metrics: LoadTestMetrics
    responses: List[dict]
    num_errors: int

    @classmethod
    def build(cls, metrics, responses):
        num_errors = len([resp for resp in responses
                          if isinstance(resp, (Exception, str))])
        return cls(metrics=metrics,
                   responses=responses,
                   num_errors=num_errors)

    def dict(self):
        _dict = {
            'metrics': asdict(self.metrics),
            'responses': self.responses,
            'num_errors': self.num_errors
        }
        return _dict

    @classmethod
    def build_from_dict(cls, result_dict: dict):
        metrics = LoadTestMetrics.build_from_dict(
            result_dict['metrics'])
        return cls(metrics=metrics,
                   responses=result_dict['responses'],
                   num_errors=result_dict['num_errors'])


def get_result(responses: List[Union[dict, str]],
               timestamps: List[Timestamp],
               latency_timestamps: List[Timestamp]):
    metrics = LoadTestMetrics.build(timestamps,
                                    latency_timestamps)
    return LoadTestResult.build(metrics=metrics, responses=responses)
