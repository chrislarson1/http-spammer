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
from io import open
from setuptools import setup, find_packages


setup(
    name="http-spammer",
    version="0.1.1-rc6",
    author="Chris Larson",
    author_email="chris7larson@gmail.com",
    description="asyncronous http load testing tool",
    long_description=open("README.md", "r", encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    keywords='http loadtest load test',
    license='Apache Version 2.0',
    python_requires='>=3.6.6',
    url="https://github.com/chrislarson1/http-spammer.git",
    packages=find_packages(exclude=[
        "*.data",
        "*.data.*",
        "data.*",
        "data",
        ".local/",
        "tests/"
    ]),
    install_requires=[
        'aiosonic==0.9.7',
        'chardet==4.0.0',
        'numpy>=1.18.1',
        'orjson>=3.0.2',
        'pydantic==1.8.1',
        'pyyaml==5.4.1',
        'requests==2.25.1',
        'uvloop==0.14.0',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Testing :: Traffic Generation',
    ]
)
