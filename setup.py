#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

#  DataCatalog
#  Copyright (C) 2020  University of Luxembourg
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

requirements = [
    'Flask>=0.10.1', 'Flask-Assets==0.12', 'Flask-Script', 'Jinja2', 'SQLAlchemy', 'werkzeug==0.16.1', 'closure',
    'cssmin', 'webassets', 'Flask-Testing', 'requests', 'GEOparse',
    'Flask-Caching', 'python-ldap',
    'Flask-Login', 'Flask-WTF', 'pysolr==3.8.1', 'ckanapi', 'Flask-Mail==0.9.1', 'flask_wtf', 'wtforms',
    'flask-reverse-proxy-fix', 'email_validator', 'oic', 'jsonpath_ng'
]

test_requirements = [
    'coverage'
]

setup(
    name='datacatalog',
    version='0.0.1',
    description="Data catalog",
    author="Valentin Grouès",
    author_email='valentin.groues@uni.lu',
    url='https://git-r3lab.uni.lu/core-services/data-catalog',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    package_dir={'datacatalog':
                     'datacatalog'},
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords=['data catalog', 'lcsb'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        # 'Intended Audience :: Developers',
        # 'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    package_data={
        'datacatalog': ['datacatalog/resources/*']
    }
)
