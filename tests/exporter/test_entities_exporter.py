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

from tests.base_test import BaseTest
from datacatalog import app
from datacatalog.models.dataset import Dataset
from datacatalog.exporter.entities_exporter import EntitiesExporter
from datacatalog.connector.rems_connector import RemsConnector

__author__ = 'Nirmeen Sallam'


class TestEntitiesExporter(BaseTest):

    def test_entities_exporter(self):
        title = "Great dataset!"
        dataset = Dataset(title)
        connector = RemsConnector(api_username=app.config.get('REMS_API_USER'),
                                  api_key=app.config.get('REMS_API_KEY'),
                                  host=app.config.get('REMS_URL'),
                                  verify_ssl=app.config.get('REMS_VERIFY_SSL', True)
                                  )
        exporter = EntitiesExporter([connector])
        exporter.export_all([dataset])
        catalogue_item = connector.get_catalogue_item(dataset.id)
        self.assertEqual(catalogue_item.resid, dataset.id)

