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
from dataclasses import dataclass, asdict
from typing import List, Union

import uvloop
import orjson as json
from aiosonic import HeadersType, Timeouts, SSLContext, HTTPClient
from aiosonic.types import DataType, ParamsType

from http_spammer.timing import CLOCK, async_now
from http_spammer.metrics import LoadTestMetrics, LoadTestResult


__all__ = ['LoadTest', 'HttpRequest']


MAX_RPS = 5000
MIN_REQ = 100


@dataclass()
class HttpRequest:

    method: str
    headers: HeadersType = None
    params: ParamsType = None
    data: DataType = None
    verify: bool = False
    ssl: SSLContext = None
    timeouts: Timeouts = None

    def dict(self):
        return asdict(self)


class LoadTestTask:
    start_time: float
    end_time: float
    response: Union[asyncio.Future, dict]


class LoadTest:

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
        self.client.shutdown()
        self.loop.close()

    async def __send(self,
                     url,
                     message: HttpRequest):
        task = LoadTestTask()
        task.start_time = async_now(self.loop)
        if message.method.lower() != 'get':
            response = await self.methods[message.method.lower()](
                url,
                data=message.data,
                params=message.params,
                headers=message.headers,
                verify=message.verify,
                ssl=message.ssl,
                timeouts=message.timeouts)
            task.response = json.loads(await response.content())
        else:
            response = await self.methods['get'](
                url,
                params=message.params,
                headers=message.headers,
                verify=message.verify,
                ssl=message.ssl,
                timeouts=message.timeouts)
            task.response = json.loads(await response.content())
        task.end_time = async_now(self.loop)
        self._tasks.append(task)

    def __flush(self, n_messages: int):
        self._n_messages = n_messages
        self._n_recv = 0
        self._tasks = []

    def __wait(self, start_t, index, num_messages, duration):
        messages_fraction = index / num_messages
        time_fraction = (async_now(self.loop) - start_t) / duration
        return messages_fraction > time_fraction

    async def __collect(self):
        while len(self._tasks) < self._n_messages:
            await asyncio.sleep(CLOCK)

    async def __run_async(self, url, messages, load_duration):
        start_t = async_now(self.loop)
        for idx, message in enumerate(messages):
            while self.__wait(start_t, idx, self._n_messages, load_duration):
                await asyncio.sleep(CLOCK)
            asyncio.ensure_future(
                self.__send(url, message))
        await self.__collect()

    def run(self,
            url: str,
            messages: List[HttpRequest],
            requests_per_second: int = MAX_RPS) -> LoadTestResult:
        assert len(messages) >= MIN_REQ
        self.__flush(len(messages))
        load_duration = len(messages) / requests_per_second
        self.loop.run_until_complete(
            asyncio.ensure_future(
                self.__run_async(url, messages, load_duration)))
        responses, timestamps = zip(*sorted(
            [(task.response, (task.start_time, task.end_time))
             for task in self._tasks],
            key=lambda tup: tup[1][0]))
        metrics = LoadTestMetrics.build(timestamps)
        return LoadTestResult.build(metrics=metrics, responses=responses)
