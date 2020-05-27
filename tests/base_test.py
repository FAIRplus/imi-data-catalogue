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

from flask_testing import TestCase

from datacatalog import app, configure_solr_orm


def get_resource_path(filename):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)


class BaseTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.configure_test_app()

    @classmethod
    def configure_test_app(cls):
        os.environ['DATACATALOG_ENV'] = 'test'
        app.config.from_object('datacatalog.settings.TestConfig')
        configure_solr_orm(app)

    def create_app(self):
        BaseTest.configure_test_app()
        return app

    def setUp(self):
        pass

    def tearDown(self):
        pass
