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

from base_test import BaseTest, get_resource_path
from datacatalog import app
from datacatalog.connector.dats_connector import DATSConnector
from datacatalog.connector.geostudies_connector import GEOStudiesConnector
from datacatalog.connector.json_connector import JSONConnector
from datacatalog.importer.entities_importer import EntitiesImporter
from datacatalog.models.dataset import Dataset
from datacatalog.models.project import Project
from datacatalog.models.study import Study

__author__ = 'Valentin Grouès'


class TestSolrORM(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.solr_orm = app.config['_solr_orm']
        cls.solr_orm.delete_fields()
        cls.solr_orm.create_fields()

    def test_import_entities(self):
        self.solr_orm.delete(query='*:*')
        connector = [JSONConnector(os.path.join(get_resource_path('records.json')),
                                   Dataset),
                     GEOStudiesConnector(get_resource_path('geo_studies_test'), Study),
                     DATSConnector(get_resource_path('imi_studies_test'), Project)]
        entities_importer = EntitiesImporter(connector)
        entities_importer.import_all()
        dataset = Dataset.query.all()
        self.assertEqual(78, len(dataset))
        study = Study.query.all()
        self.assertEqual(2, len(study))
        project = Project.query.all()
        self.assertEqual(2, len(project))

    def tearDown(self):
        app.config['_solr_orm'].delete(query='*:*')
        app.config['_solr_orm'].commit()
