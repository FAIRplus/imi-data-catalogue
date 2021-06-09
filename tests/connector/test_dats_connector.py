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
import json
import os

from tests.base_test import BaseTest
from datacatalog.connector.dats_connector import DATSConnector

__author__ = 'Danielle Welter'

from datacatalog.models.dataset import Dataset
from datacatalog.models.project import Project
from datacatalog.models.study import Study


class TestJSONConnector(BaseTest):
    def test_build_all_datasets(self):
        project_count = 0
        dataset_count = 0
        study_count = 0
        for file in os.listdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/imi_projects')):
            if file.endswith(".json"):
                project_count += 1
                with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                       '../../data/imi_projects' + "/" + file)) as json_file:
                    data = json.load(json_file)
                    if 'projectAssets' in data:
                        for asset in data['projectAssets']:
                            if asset['@type'] == 'Dataset':
                                dataset_count += 1
                            elif asset['@type'] == 'Study' and 'output' in asset:
                                study_count += 1
                                for dataset in asset['output']:
                                    dataset_count += 1

        dats_datasets_connector = DATSConnector(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/imi_projects'), Dataset)
        datasets = list(dats_datasets_connector.build_all_entities())
        self.assertEqual(dataset_count, len(datasets))

        dats_projects_connector = DATSConnector(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/imi_projects'), Project)
        projects = list(dats_projects_connector.build_all_entities())
        self.assertEqual(project_count, len(projects))

        dats_studies_connector = DATSConnector(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/imi_projects'), Study)
        studies = list(dats_studies_connector.build_all_entities())
        self.assertEqual(study_count, len(studies))
