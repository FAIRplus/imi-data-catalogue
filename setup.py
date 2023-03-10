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
    "Flask==1.1.4",
    "Flask-Assets==2.0",
    "Flask-Script==2.0.6",
    "Jinja2==2.11.3",
    "werkzeug==0.16.1",
    "closure==20191111",
    "markupsafe==2.0.1",
    "cssmin==0.2.0",
    "webassets==2.0",
    "Flask-Testing==0.8.1",
    "requests==2.26.0",
    "GEOparse==2.0.3",
    "Flask-Caching==1.10.1",
    "python-ldap==3.3.1",
    "wtforms==2.3.3",
    "Flask-Login==0.5.0",
    "Flask-WTF==0.15.1",
    "pysolr==3.8.1",
    "ckanapi==4.6",
    "Flask-Mail==0.9.1",
    "flask-reverse-proxy-fix==0.2.1",
    "email-validator==1.1.3",
    "oic==1.3.0",
    "jsonpath-ng==1.5.3",
    "python-slugify==5.0.2",
    "jsonschema==4.4.0",
]

test_requirements = ["coverage==5.5"]

setup(
    name="datacatalog",
    version="0.0.1",
    description="Data catalog",
    author="Valentin Grouès",
    author_email="valentin.groues@uni.lu",
    url="https://git-r3lab.uni.lu/core-services/data-catalog",
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    package_dir={"datacatalog": "datacatalog"},
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords=["data catalog", "lcsb"],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        # 'Intended Audience :: Developers',
        # 'License :: OSI Approved :: ISC License (ISCL)',
        "Natural Language :: English",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    test_suite="tests",
    tests_require=test_requirements,
    package_data={"datacatalog": ["datacatalog/resources/*"]},
)
