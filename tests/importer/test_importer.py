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

from datacatalog import app
from datacatalog.connector.dats_connector import DATSConnector
from datacatalog.connector.geostudies_connector import GEOStudiesConnector
from datacatalog.connector.json_connector import JSONConnector
from datacatalog.importer.entities_importer import EntitiesImporter
from datacatalog.models.dataset import Dataset
from datacatalog.models.project import Project
from datacatalog.models.study import Study
from datacatalog.solr.solr_orm_fields import SolrJsonField
from tests.base_test import BaseTest, get_resource_path

__author__ = "Valentin Grouès"


class TestSolrORM(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.solr_orm = app.config["_solr_orm"]
        cls.solr_orm.delete_fields()
        cls.solr_orm.create_fields()

    def test_import_entities(self):
        self.solr_orm.delete(query="*:*")
        connector = [
            JSONConnector(os.path.join(get_resource_path("records.json")), Dataset),
            GEOStudiesConnector(get_resource_path("geo_studies_test"), Study),
            DATSConnector(get_resource_path("imi_projects_test"), Project),
        ]
        entities_importer = EntitiesImporter(connector)
        entities_importer.import_all()
        dataset = Dataset.query.all()
        self.assertEqual(78, len(dataset))
        study = Study.query.all()
        self.assertEqual(2, len(study))
        project = Project.query.all()
        self.assertEqual(7, len(project))

    def test_check_schema(self):
        self.assertTrue(self.solr_orm.check_schema("study"))
        self.assertTrue(self.solr_orm.check_schema("project"))
        self.assertTrue(self.solr_orm.check_schema("dataset"))

    def test_field_type_mismatch(self):
        self.assertFalse(self.solr_orm.field_type_mismatch("study"))
        self.assertFalse(self.solr_orm.field_type_mismatch("project"))
        self.assertFalse(self.solr_orm.field_type_mismatch("dataset"))

    def test_check_fields_existence(self):
        self.assertTrue(self.solr_orm.check_fields_existence())

    def test_deserialize_instance(self):
        connector = [
            JSONConnector(os.path.join(get_resource_path("records.json")), Dataset),
            GEOStudiesConnector(get_resource_path("geo_studies_test"), Study),
            DATSConnector(get_resource_path("imi_projects_test"), Project),
        ]
        entities_importer = EntitiesImporter(connector)
        entities_importer.import_all()
        for entity_name in app.config["entities"]:
            entity_class = app.config["entities"][entity_name]
            results = self.solr_orm.indexer.search(
                q="type:" + entity_name, rows=1000000
            )
            for result in results:
                for attribute_name, field in entity_class._solr_fields.items():
                    solr_value = result.get(entity_name + "_" + field.name, None)
                    if solr_value is not None and isinstance(field, SolrJsonField):
                        if field.model:
                            for count, value in enumerate(solr_value):
                                data = json.loads(value)
                                self.assertIsInstance(
                                    field.model.from_json(data), field.model
                                )
                        self.assertTrue(solr_value)

    def test_serialize_instance(self):
        base_folder = get_resource_path("imi_projects_test")
        for entity_name in app.config["entities"]:
            dats_entity_connector = DATSConnector(
                base_folder,
                app.config["entities"][entity_name],
            )
            entities = dats_entity_connector.build_all_entities()
            for entity in entities:
                for attribute_name, field in entity._solr_fields.items():
                    attribute_value = getattr(entity, attribute_name, None)
                    if isinstance(field, SolrJsonField):
                        if field.model:
                            if attribute_value is not None:
                                for count, value in enumerate(attribute_value):
                                    print(value, " ATTRIBUTE VALUE ")
                                    self.assertIsInstance(value, field.model)

    def tearDown(self):
        app.config["_solr_orm"].delete(query="*:*")
        app.config["_solr_orm"].commit()
