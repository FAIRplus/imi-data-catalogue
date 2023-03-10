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
import requests

from datacatalog import app
from tests.base_test import BaseTest

__author__ = "Nirmeen Sallam"


class TestModels(BaseTest):
    def setUp(self):
        self.solr_orm = app.config["_solr_orm"]
        self.solr_orm.delete_fields()
        self.solr_orm.commit()

    def test_initialize_solr_query_fields(self):
        self.solr_orm.create_fields()
        self.solr_query_fields = app.config.get(
            "SOLR_QUERY_TEXT_FIELD",
            {
                "project": ["datasets_metadata", "studies_metadata"],
                "dataset": ["title", "studies_metadata", "projects_metadata"],
                "study": ["title", "datasets_metadata", "projects_metadata"],
            },
        )
        if app.config.get("SOLR_QUERY_SEARCH_EXTENDED"):
            self.assertIn("datasets_metadata", self.solr_query_fields.get("project"))
            self.assertIn("studies_metadata", self.solr_query_fields.get("project"))
            if not app.config.get("SOLR_QUERY_SEARCH_EXTENDED_2_WAY_INDEX"):
                self.assertIn("datasets_metadata", self.solr_query_fields.get("study"))
            if app.config.get("SOLR_QUERY_SEARCH_EXTENDED_2_WAY_INDEX"):
                self.assertIn("datasets_metadata", self.solr_query_fields.get("study"))
                self.assertIn("projects_metadata", self.solr_query_fields.get("study"))

                self.assertIn("studies_metadata", self.solr_query_fields.get("dataset"))
                self.assertIn(
                    "projects_metadata", self.solr_query_fields.get("dataset")
                )

    def test_create_field(self):
        self.solr_orm.indexer_schema.create_field(
            "dataset_test", "string", False, False, False
        )
        self.assertIn(
            "dataset_test",
            requests.get(self.solr_orm.indexer_schema.url + "/fields").content.decode(
                "utf-8"
            ),
        )
        self.solr_orm.indexer_schema.delete_field("dataset_test")
        self.solr_orm.commit()

    def test_update_field(self):
        self.solr_orm.indexer_schema.create_field(
            "dataset_test", "string", False, False, False
        )
        self.solr_orm.indexer_schema.update_field(
            "dataset_test", "text_en", False, False, False
        )
        self.assertIn(
            "text_en",
            requests.get(
                self.solr_orm.indexer_schema.url + "/fields/dataset_test"
            ).content.decode("utf-8"),
        )
        self.solr_orm.indexer_schema.delete_field("dataset_test")
        self.solr_orm.commit()

    def test_delete_field(self):
        self.solr_orm.indexer_schema.create_field(
            "dataset_test", "string", False, False, False
        )
        self.solr_orm.indexer_schema.delete_field("dataset_test")
        class_attributes = requests.get(
            self.solr_orm.indexer_schema.url + "/fields"
        ).content.decode("utf-8")
        self.assertNotIn("dataset_test", class_attributes)
        self.solr_orm.commit()

    def tearDown(self):
        self.solr_orm.delete_fields()
        self.solr_orm.commit()
