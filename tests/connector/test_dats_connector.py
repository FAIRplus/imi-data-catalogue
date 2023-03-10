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

from datacatalog.connector.dats_connector import DATSConnector
from tests.base_test import BaseTest, get_resource_path

__author__ = "Danielle Welter"

from datacatalog.models.dataset import Dataset
from datacatalog.models.project import Project
from datacatalog.models.study import Study


class TestDatsConnector(BaseTest):
    def test_build_all_datasets(self):
        project_count = 0
        dataset_count = 0
        study_count = 0
        base_folder = get_resource_path("imi_projects_test")
        for file in os.listdir(base_folder):
            if file.endswith(".json"):
                project_count += 1
                with open(
                    os.path.join(
                        base_folder,
                        file,
                    )
                ) as json_file:
                    data = json.load(json_file)
                    if "projectAssets" in data:
                        for asset in data["projectAssets"]:
                            if asset["@type"] == "Dataset":
                                dataset_count += 1
                            elif asset["@type"] == "Study":
                                study_count += 1
                                if "output" in asset:
                                    for _ in asset["output"]:
                                        dataset_count += 1

        dats_datasets_connector = DATSConnector(
            base_folder,
            Dataset,
        )
        datasets = list(dats_datasets_connector.build_all_entities())

        self.assertEqual(dataset_count, len(datasets))
        for dataset in datasets:
            if dataset.id == "6bd9243b-0368-4cc9-bc92-d00ba1d40b75":
                self.assertTrue(dataset.hosted)
            else:
                self.assertFalse(dataset.hosted)
            self.assertFalse(dataset.e2e)
        dats_projects_connector = DATSConnector(
            base_folder,
            Project,
        )
        projects = list(dats_projects_connector.build_all_entities())
        self.assertEqual(project_count, len(projects))

        dats_studies_connector = DATSConnector(
            base_folder,
            Study,
        )
        studies = list(dats_studies_connector.build_all_entities())
        self.assertEqual(study_count, len(studies))
