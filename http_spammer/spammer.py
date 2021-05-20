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
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Union, List, Tuple

import uvloop
import orjson as json
from aiosonic import Timeouts, HTTPClient

from http_spammer.requests import SYNC_REQUEST_FN, GetRequest, BodyRequest
from http_spammer.timing import now, CLOCK, Timestamp

__all__ = ['LoadSpammer', 'LatencySpamer']


MAX_RPS = 5000
MIN_REQ = 100


class LoadTestTask:
    start_time: float
    end_time: float
    response: Union[asyncio.Future, dict]


def wait(start_t, index, num_requests, test_duration):
    requests_ratio = index / num_requests
    time_ratio = (now() - start_t) / test_duration
    return requests_ratio > time_ratio


class Spammer(ABC):
    @abstractmethod
    def run(self,
            requests: List[Union[GetRequest, BodyRequest]],
            requests_per_second: float
            ) -> Tuple[List[dict], List[Timestamp]]:
        pass


class LoadSpammer:

    def __init__(self):
        uvloop.install()
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        self.loop = uvloop.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.client = HTTPClient()
        self.methods = dict(
            get=self.client.get,
            post=self.client.post,
            put=self.client.put,
            patch=self.client.patch,
            delete=self.client.delete
        )

    def __del__(self):
        self.loop.run_until_complete(self.client.shutdown())
        self.loop.close()

    async def __send(self, request: Union[GetRequest, BodyRequest]):
        task = LoadTestTask()
        task.start_time = now()
        if request.timeouts:
            request.timeouts = Timeouts(sock_connect=request.timeouts[0],
                                        sock_read=request.timeouts[1])
        args = request.dict()
        for arg in ('method', 'num_queries'):
            args.pop(arg, None)
        response = await self.methods[request.method.lower()](**args)
        task.response = json.loads(await response.content())
        task.end_time = now()
        self._tasks.append(task)

    def __flush(self, n_requests: int):
        self._n_requests = n_requests
        self._n_recv = 0
        self._tasks = []

    async def __collect(self):
        while len(self._tasks) < self._n_requests:
            await asyncio.sleep(CLOCK)

    async def __run_async(self, requests, load_duration):
        start_t = now()
        for idx, request in enumerate(requests):
            while wait(start_t, idx, self._n_requests, load_duration):
                await asyncio.sleep(CLOCK)
            asyncio.ensure_future(
                self.__send(request))
        await self.__collect()

    def run(self, requests, requests_per_second):
        self.__flush(len(requests))
        load_duration = len(requests) / requests_per_second
        self.loop.run_until_complete(
            asyncio.ensure_future(
                self.__run_async(requests, load_duration)))
        responses, timestamps = zip(*sorted(
            [(task.response, (task.start_time, task.end_time))
             for task in self._tasks],
            key=lambda tup: tup[1][0]))
        return responses, timestamps


class LatencySpamer:

    def run(self, requests, requests_per_second):
        t = now()
        test_duration = len(requests) / requests_per_second
        tasks = []
        while requests:
            request = requests.pop()
            task = LoadTestTask()
            args = request.dict()
            for arg in ('method', 'num_queries'):
                args.pop(arg, None)
            args['timeout'] = args.pop('timeouts')
            while wait(t, len(tasks), len(tasks) + len(requests), test_duration):
                time.sleep(CLOCK)
            task.start_time = now()
            response = SYNC_REQUEST_FN[request.method.lower()](**args)
            task.end_time = now()
            task.response = json.loads(response.content)
            tasks.append(task)
        responses, timestamps = zip(*sorted(
            [(task.response, (task.start_time, task.end_time))
             for task in tasks],
            key=lambda tup: tup[1][0]))
        return responses, timestamps
