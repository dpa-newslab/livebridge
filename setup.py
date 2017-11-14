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

version = '0.23.0'

setup(
    name='livebridge',
    version=version,
    description="Keep content in-sync across services. Or simply syndicate content to multiple services. " +
                "Based on asyncio.",
    long_description="""\
        See https://github.com/dpa-newslab/livebridge for more infos.
    """,
    classifiers=[
        "Programming Language :: Python :: 3.5",
        "Topic :: Communications :: Chat",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Other Audience",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
    ],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords=['liveticker', 'liveblog', 'syndication', "async", "asyncio"],
    author='dpa-infocom GmbH',
    maintainer='Martin Borho',
    maintainer_email='martin@borho.net',
    url='https://github.com/dpa-newslab/livebridge',
    license='Apache Software License (http://www.apache.org/licenses/LICENSE-2.0)',
    packages=find_packages(exclude=['tests', 'htmlcov', 'dist']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'aiobotocore==0.3.3',
        'aiohttp==2.1.0',
        'asynctest==0.10.0',
        'bleach==2.0.0',
        'PyYAML==3.12',
        'websockets==3.3',
        'sqlalchemy-aio==0.11.0',
        'python-dateutil==2.6.0',
        'dsnparse==0.1.4',
        'motor==1.1',
    ],
    entry_points="""
    [console_scripts]
    livebridge = livebridge.run:main
    """,
)
