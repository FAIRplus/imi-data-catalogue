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

from datacatalog.connector.geostudies_connector import GEOStudiesConnector
from tests.base_test import BaseTest, get_resource_path
from datacatalog.connector.dats_connector import DATSConnector

__author__ = 'Valentin Grouès'

from datacatalog.models.dataset import Dataset
from datacatalog.models.project import Project
from datacatalog.models.study import Study


class TestGeoConnector(BaseTest):
    def test_build_studies_json(self):
        geo_connector = GEOStudiesConnector(get_resource_path('geo_studies_test'), Study)
        studies = geo_connector.build_all_entities()
        count = 0
        for study in studies:
            self.assertIsInstance(study, Study)
            count += 1
        self.assertEqual(2, count)

    def test_build_project_json(self):
        geo_connector = GEOStudiesConnector(get_resource_path('geo_studies_test'), Project)
        projects = geo_connector.build_all_entities()
        count = 0
        for project in projects:
            self.assertIsInstance(project, Project)
            count += 1
        self.assertEqual(2, count)

    def test_build_datasets_json(self):
        geo_connector = GEOStudiesConnector(get_resource_path('geo_studies_test'), Dataset)
        datasets = geo_connector.build_all_entities()
        count = 0
        for dataset in datasets:
            self.assertIsInstance(dataset, Dataset)
            count += 1
        self.assertEqual(2, count)

    def test_build_datasets_tsv(self):
        geo_connector = GEOStudiesConnector(get_resource_path('geo_studies_test'), Dataset)
        datasets = geo_connector.build_all_entities()
        count = 0
        for dataset in datasets:
            self.assertIsInstance(dataset, Dataset)
            count += 1
        self.assertEqual(2, count)

