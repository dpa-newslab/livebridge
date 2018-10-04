# -*- coding: utf-8 -*-
#
# Copyright 2016, 2017 dpa-infocom GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from setuptools import setup, find_packages

with open('./README.md') as f:
    long_description = f.read()

version = '0.26.0'

setup(
    name='livebridge',
    version=version,
    description="Keep content in-sync across services. Or simply syndicate content to multiple services. " +
                "Based on asyncio.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        "Programming Language :: Python :: 3.5",
        "Topic :: Communications :: Chat",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Other Audience",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
    ],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords=["liveticker", "liveblog", "syndication", "async", "asyncio", "realtime"],
    author='dpa-infocom GmbH',
    maintainer='Martin Borho',
    maintainer_email='martin@borho.net',
    url='https://github.com/dpa-newslab/livebridge',
    license='Apache Software License (http://www.apache.org/licenses/LICENSE-2.0)',
    packages=find_packages(exclude=['tests', 'htmlcov', 'dist']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "aiobotocore==0.9.4",
        "aiohttp==3.4.4",
        "bleach==2.1.4",
        "dsnparse==0.1.12",
        "pymongo>=3.6.0",
        "motor==2.0.0",
        "python-dateutil==2.7.3",
        "PyYAML==3.13",
        "sqlalchemy-aio==0.13.0",
        "websockets==6.0",
    ],
    entry_points="""
    [console_scripts]
    livebridge = livebridge.run:main
    """,
)
