# -*- coding: utf-8 -*-
#
# Copyright 2016 dpa-infocom GmbH
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
import sys, os

version = '0.18.2'

setup(name='livebridge',
      version=version,
      description="Keep content in-sync across services. Or simply syndicate content to multiple services. Based on asyncio.",
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
        ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords=['liveticker','liveblog','syndication', "async", "asyncio"],
      author='dpa-infocom GmbH',
      maintainer='Martin Borho',
      maintainer_email='martin@borho.net',
      url='https://github.com/dpa-newslab/livebridge',
      license='Apache Software License (http://www.apache.org/licenses/LICENSE-2.0)',
      packages=find_packages(exclude=['tests', 'htmlcov', 'dist',]),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'aiohttp==1.0.5',
        'asynctest==0.9.0',
        'bleach==1.4.3',
        'PyYAML==3.12',
        'aiobotocore==0.0.5',
        'boto3==1.3.1',
        'websockets==3.2',
        'sqlalchemy-aio==0.1b1',
        'python-dateutil==2.5.3',
      ],
      entry_points="""
      [console_scripts]  
      livebridge = livebridge.run:main
      """,       
      )

