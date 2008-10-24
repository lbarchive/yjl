#!/usr/bin/python
#
# Copyright (C) 2008 Yu-Jie Lin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from setuptools import setup, find_packages


setup(
    name='twitter_client',
    version='0.1a1',
    packages=find_packages('src'),
    install_requires=['gdata.py>=1.2.0'],
    description='Python client library for Twitter APIs',
    long_description = """\
Python client library for Twitter APIs. Currently supports
 - Search API
""",
    author='Yu-Jie Lin',
    author_email='livibetter@gmail.com',
    license='Apache 2.0',
    keywords='twitter atom gdata',
    url='http://makeyjl.blogspot.com/',
    package_dir = {'':'src'},
)
