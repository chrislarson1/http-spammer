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

from http_spammer.request import SYNC_REQUEST_FN, GetRequest, BodyRequest
from http_spammer.timing import now, CLOCK, Timestamp

__all__ = ['LoadSpammer', 'LatencySpammer']


class LoadTestTask:
    start_time: float
    end_time: float
    response: Union[asyncio.Future, dict, None] = None


def throttle(start_t, index, duration, rps_start, rps_end):
    t = now()
    rps_target = rps_start + \
                 (rps_end - rps_start) * ((t - start_t) / duration)
    requests_target = (t - start_t) * (rps_start + rps_target) / 2
    return index > requests_target


class Spammer(ABC):
    @abstractmethod
    def run(self,
            requests: List[Union[GetRequest, BodyRequest]],
            duration: float,
            rps_start: float,
            rps_end: float,
            ) -> Tuple[List[dict], List[Timestamp]]:
        pass


class LoadSpammer(Spammer):

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
        args = request.dict()
        args.pop('method')
        args['timeouts'] = Timeouts(sock_read=args.pop('timeout'))
        task = LoadTestTask()
        try:
            task.start_time = now()
            response = await (
                await self.methods[request.method.lower()](**args)
            ).content()
        except Exception as exc:
            task.response = exc
        task.end_time = now()
        if task.response is None:
            task.response = json.loads(response)
        self._tasks.append(task)

    def __flush(self, n_requests: int):
        self._n_requests = n_requests
        self._n_recv = 0
        self._tasks = []

    async def __collect(self):
        while len(self._tasks) < self._n_requests:
            await asyncio.sleep(CLOCK)

    async def __run_async(self, requests, duration, rps_start, rps_end):
        start_t = now()
        for idx, request in enumerate(requests):
            while throttle(start_t, idx, duration, rps_start, rps_end):
                await asyncio.sleep(CLOCK)
            asyncio.ensure_future(
                self.__send(request))
        await self.__collect()

    def run(self, requests, duration, rps_start, rps_end):
        self.__flush(len(requests))
        self.loop.run_until_complete(
            asyncio.ensure_future(
                self.__run_async(requests, duration, rps_start, rps_end)))
        responses, timestamps = zip(
            *sorted([(task.response, (task.start_time, task.end_time))
                     for task in self._tasks],
                    key=lambda tup: tup[1][0])
        )
        return responses, timestamps


class LatencySpammer(Spammer):

    def run(self, requests, duration, rps_start, rps_end):
        t = now()
        tasks = []
        while requests:
            request = requests.pop()
            args = request.dict()
            args.pop('method')
            while throttle(t, len(tasks), duration, rps_start, rps_end):
                time.sleep(CLOCK)
            task = LoadTestTask()
            try:
                task.start_time = now()
                response = SYNC_REQUEST_FN[request.method.lower()](**args).content
            except Exception as exc:
                task.response = exc
            task.end_time = now()
            if task.response is None:
                task.response = json.loads(response)
            tasks.append(task)
        responses, timestamps = zip(*sorted(
            [(task.response, (task.start_time, task.end_time))
             for task in tasks],
            key=lambda tup: tup[1][0]))
        return responses, timestamps
