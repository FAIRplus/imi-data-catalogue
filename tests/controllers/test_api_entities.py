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
from datacatalog import app
from tests.base_test import BaseTest, get_resource_path
from datacatalog.controllers.api_entities import api_entity, api_entities
from datacatalog.connector.dats_connector import DATSConnector
from datacatalog.connector.geostudies_connector import GEOStudiesConnector
from datacatalog.connector.json_connector import JSONConnector
from datacatalog.importer.entities_importer import EntitiesImporter
from datacatalog.models.dataset import Dataset
from datacatalog.models.project import Project
from datacatalog.models.study import Study

__author__ = 'Nirmeen Sallam'


class TestApiEntities(BaseTest):
    connector = [JSONConnector(os.path.join(get_resource_path('records.json')),
                               Dataset),
                 GEOStudiesConnector(get_resource_path('geo_studies_test'), Study),
                 DATSConnector(get_resource_path('imi_studies_test'), Project)]
    entities_importer = EntitiesImporter(connector)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.solr_orm = app.config['_solr_orm']
        cls.solr_orm.delete_fields()
        cls.solr_orm.create_fields()

    def setUp(self):
        self.solr_orm.delete(query='*:*')
        self.entities_importer.import_all()

    def test_api_entity(self):
        dataset = Dataset.query.all()
        study = Study.query.all()
        project = Project.query.all()
        self.assert200(api_entity('dataset', dataset[0].id))
        self.assert200(api_entity('study', study[0].id))
        self.assert200(api_entity('project', project[0].id))

    def test_api_entities(self):
        self.assertIsNotNone(api_entities('dataset').data)
        self.assert200(api_entities('dataset'))
        self.assert200(api_entities('study'))
        self.assert200(api_entities('project'))

    def tearDown(self):
        app.config['_solr_orm'].delete(query='*:*')
        app.config['_solr_orm'].commit()

