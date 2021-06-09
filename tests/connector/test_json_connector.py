# coding=utf-8

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

import os

from tests.base_test import BaseTest
from datacatalog.connector.json_connector import JSONConnector

__author__ = 'Valentin Grouès'

from datacatalog.models.dataset import Dataset


class TestJSONConnector(BaseTest):
    def test_build_all_datasets(self):
        json_connector = JSONConnector(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data', 'records.json'), Dataset)
        datasets = list(json_connector.build_all_entities())
        self.assertEqual(78, len(datasets))
