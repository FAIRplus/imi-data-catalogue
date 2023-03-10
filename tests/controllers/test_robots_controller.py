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

# coding='utf-8'

from flask import url_for

from tests.base_test import BaseTest

__author__ = "Abetare Shabani"


class TestRobotsController(BaseTest):
    def test_robots(self):
        with self.client:
            response = self.client.get(url_for("generate_robots"))

            # check if robots.txt was generated
            self.assertEquals(response.status_code, 200)

            # check if data is empty
            data = response.data.decode("utf-8").replace("\n", "")
            self.assertTrue(data)
