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
import re
from multiprocessing import cpu_count

import pytest

from http_spammer import url_pattern
from http_spammer.contraints import MAX_WRKR_RPS
from http_spammer import TestConfig, load_from_url, validate_test_config


def test_url_match():
    urls = ('http://x.com',
            'http://www.x.com'
            'https://x.com',
            'https://www.x.com',
            'www.x.com')
    for url in urls:
        assert re.match(url_pattern, url)


def test_no_url_match():
    urls = ('f.yaml',
            '/x/f.yaml'
            '~/f.yaml',
            '~/x/f.yaml',
            '../f.yaml')
    for url in urls:
        assert not re.match(url_pattern, url)


def test_load_config_from_url(test_file_url):
    TestConfig(**load_from_url(test_file_url))


def test_config_validation(test_config):
    validate_test_config(test_config)


@pytest.mark.skipif(cpu_count() < 3,
                    reason="insufficient cores")
def test_config_meets_max_rps(test_config):
    test_config.numClients = 2
    test_config.segments[0].startRps = MAX_WRKR_RPS * 2
    validate_test_config(test_config)


@pytest.mark.skipif(cpu_count() < 3,
                    reason="insufficient cores")
def test_config_exceeds_max_rps(test_config):
    test_config.segments[0].startRps = \
        MAX_WRKR_RPS * test_config.numClients + 1
    with pytest.raises(RuntimeError):
        validate_test_config(test_config)
    test_config.numClients += 1
    test_config.segments[0].startRps = \
        MAX_WRKR_RPS * test_config.numClients + 1
    with pytest.raises(RuntimeError):
        validate_test_config(test_config)


def test_config_exceeds_cpu_count(test_config):
    test_config.numClients = cpu_count()
    with pytest.raises(RuntimeError):
        validate_test_config(test_config)
