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
from datacatalog.models.dataset import Dataset
from datacatalog.models.project import Project
from datacatalog.models.study import Study
from datacatalog.connector.dats_connector import DATSConnector
from datacatalog.exporter.dats_exporter import DATSExporter

__author__ = 'Nirmeen Sallam'


class TestDATSExporter(BaseTest):
    def test_build_all_datasets(self):

        dats_exporter = DATSExporter()

        dats_datasets_connector = DATSConnector(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/imi_projects'), Dataset)
        datasets = list(dats_datasets_connector.build_all_entities())
        for dataset in datasets:
            dats_entity = dats_exporter.export_dats_entity(dataset)
            self.assertEqual(dats_entity["projectAssets"][0]["title"], dataset.title)

        dats_projects_connector = DATSConnector(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/imi_projects'), Project)
        projects = list(dats_projects_connector.build_all_entities())
        for project in projects:
            dats_entity = dats_exporter.export_dats_entity(project)
            self.assertEqual(dats_entity["title"], project.title)

        dats_studies_connector = DATSConnector(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/imi_projects'), Study)
        studies = list(dats_studies_connector.build_all_entities())
        for study in studies:
            dats_entity = dats_exporter.export_dats_entity(study)
            self.assertEqual(dats_entity["projectAssets"][0]["name"], study.title)
