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

from tests.base_test import BaseTest, get_resource_path
from tests.dats import dats_model

__author__ = "Danielle Welter"


class TestDatsJson(BaseTest):
    def test_validate_all_projects(self):
        base_folder = get_resource_path("imi_projects_test")
        for file in os.listdir(base_folder):
            if file.endswith(".json"):
                with self.subTest(file=file):
                    with open(
                        os.path.join(
                            base_folder,
                            file,
                        )
                    ) as json_file:
                        data = json.load(json_file)
                        validation = dats_model.validate_project(
                            base_folder,
                            file,
                            data,
                            0,
                        )
                        self.assertTrue(validation)
