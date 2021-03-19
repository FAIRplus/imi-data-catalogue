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
from unittest.case import TestCase

from datacatalog.converter.entities_splitter import split_entities

__author__ = 'Valentin Grouès'


class TestConverter(TestCase):

    def test_split_entities(self):
        base_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
        records_file_path = os.path.join(base_folder, 'records.json')
        datasets_file_path = os.path.join(base_folder, 'datasets_new.json')
        studies_file_path = os.path.join(base_folder, 'studies_new.json')
        projects_file_path = os.path.join(base_folder, 'projects_new.json')
        with open(records_file_path) as records_file, open(datasets_file_path, 'w') as datasets_file, open(
                studies_file_path, 'w') as studies_file, open(projects_file_path, 'w') as projects_file:
            split_entities(records_file, datasets_file, studies_file, projects_file)
