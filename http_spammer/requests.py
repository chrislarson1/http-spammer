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
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Union

import requests as Requests


SYNC_REQUEST_FN = dict(
        get=Requests.get,
        put=Requests.put,
        post=Requests.post,
        patch=Requests.patch,
        delete=Requests.delete)


class HttpGetMethod(str, Enum):
    GET = 'GET'
    get = GET


class HttpBodyMethod(str, Enum):
    PUT = 'PUT'
    put = PUT
    POST = 'POST'
    post = POST
    PATCH = 'PATCH'
    patch = PATCH
    DELETE = 'DELETE'
    delete = DELETE


@dataclass()
class BaseRequest:
    url: str
    headers: Dict[str, str] = None
    params: Dict[str, str] = None
    verify: bool = False
    timeouts: List[float] = None

    def dict(self):
        return asdict(self)


@dataclass()
class GetRequest(BaseRequest):
    method: HttpGetMethod = 'GET'


@dataclass()
class BodyRequest(BaseRequest):
    method: HttpBodyMethod = 'POST'
    data: Union[dict, list, str, bytes] = None
    num_queries: int = None
