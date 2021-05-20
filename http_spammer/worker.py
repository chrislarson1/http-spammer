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
from multiprocessing import Process, Pipe, cpu_count
from typing import List, Union

import numpy as np

from http_spammer.spammer import LoadSpammer, LatencySpamer
from http_spammer.requests import GetRequest, BodyRequest
from http_spammer.metrics import get_result

__all__ = ['spam_runner']


RequestType = Union[GetRequest, BodyRequest]


def run(pipe, requests_batch, rps, spammer):
    responses, timestamps = spammer().run(
        requests_batch, requests_per_second=rps)
    pipe.send((responses, timestamps))
    pipe.close()


def spam_runner(num_workers: int,
                requests: List[RequestType],
                requests_per_second: int):

    test_duration = len(requests) / requests_per_second

    # Latency requests
    num_lat_requests = max(10, int(0.05 * len(requests)))
    latency_requests = []
    latency_idxs = []
    for _ in range(num_lat_requests):
        idx = np.random.choice(list(range(len(requests))), size=1)[0]
        latency_requests.append(requests.pop(idx))
        latency_idxs.append(idx)
    latency_wrkr_rps = num_lat_requests / test_duration

    # Load requests
    if num_workers >= cpu_count() - 1:
        num_workers = cpu_count() - 2
    load_wrkr_rps = (len(requests) / test_duration) / num_workers
    req_per_wrkr = len(requests) // num_workers
    load_requests = []
    for i in range(num_workers):
        N = req_per_wrkr
        if i == num_workers - 1:
            N += len(requests) % num_workers
        load_requests.append([requests.pop() for _ in range(N)])

    processes = []
    connections = []
    for idx in range(num_workers):
        parent_conn, child_conn = Pipe()
        proc = Process(target=run,
                       args=(child_conn,
                             load_requests.pop(0),
                             load_wrkr_rps,
                             LoadSpammer))
        proc.start()
        processes.append(proc)
        connections.append(parent_conn)

    parent_conn, child_conn = Pipe()
    proc = Process(target=run,
                   args=(child_conn,
                         latency_requests,
                         latency_wrkr_rps,
                         LatencySpamer))
    proc.start()

    pending = list(range(len(processes)))
    load_responses = [[]] * len(pending)
    load_timestamps = [[]] * len(pending)
    while all((processes, connections)):
        for i, (proc, conn) in enumerate(zip(processes, connections)):
            if conn.poll():
                idx = pending.pop(i)
                responses, timestamps = conn.recv()
                load_responses[idx] = responses
                load_timestamps[idx] = timestamps
                processes.pop(i).join()
                connections.pop(i).close()
                break

    latency_responses, latency_timestamps = parent_conn.recv()
    proc.join()
    parent_conn.close()

    responses = []
    for resp in load_responses:
        responses.extend(resp)
    latency_responses = list(latency_responses)
    for idx in latency_idxs[::-1]:
        responses.insert(idx, latency_responses.pop())
    timestamps = []
    for ts in load_timestamps:
        timestamps.extend(ts)
    timestamps.extend(latency_timestamps)
    timestamps = list(sorted(timestamps,
                             key=lambda tup: tup[0]))

    return get_result(responses, timestamps, latency_timestamps)
