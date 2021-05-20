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
from multiprocessing import Process, Pipe
from typing import List, Union

import numpy as np

from http_spammer.spammer import LoadSpammer, LatencySpammer
from http_spammer.request import GetRequest, BodyRequest
from http_spammer.metrics import get_result

__all__ = ['spam_runner', 'LAT_RPS']


LAT_RPS = 1.0


RequestType = Union[GetRequest, BodyRequest]


def run(pipe, requests_batch, duration, rps_start, rps_end, spammer):
    responses, timestamps = spammer().run(
        requests_batch, duration, rps_start, rps_end)
    pipe.send((responses, timestamps))
    pipe.close()


def spam_runner(num_workers: int,
                requests: List[RequestType],
                duration: float,
                rps_start: int,
                rps_end: int):

    requests_total = len(requests)

    # Latency samples
    num_lat_requests = int(LAT_RPS * duration)
    latency_requests = []
    latency_idxs = []
    for _ in range(num_lat_requests):
        idx = np.random.choice(list(range(len(requests))), size=1)[0]
        latency_requests.append(requests.pop(idx))
        latency_idxs.append(idx)

    # Throughput samples
    load_wrkr_rps_start = ((len(requests) / requests_total) * rps_start) / num_workers
    load_wrkr_rps_end = ((len(requests) / requests_total) * rps_end) / num_workers
    req_per_wrkr = len(requests) // num_workers
    load_requests = []
    for i in range(num_workers):
        if i < num_workers - 1:
            N = req_per_wrkr
        else:
            N = len(requests)
        load_requests.append([requests.pop() for _ in range(N)])

    processes = []
    connections = []
    for idx in range(num_workers):
        parent_conn, child_conn = Pipe()
        proc = Process(target=run,
                       args=(child_conn,
                             load_requests.pop(0),
                             duration,
                             load_wrkr_rps_start,
                             load_wrkr_rps_end,
                             LoadSpammer))
        proc.start()
        processes.append(proc)
        connections.append(parent_conn)

    parent_conn, child_conn = Pipe()
    proc = Process(target=run,
                   args=(child_conn,
                         latency_requests,
                         duration,
                         LAT_RPS,
                         LAT_RPS,
                         LatencySpammer))
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
