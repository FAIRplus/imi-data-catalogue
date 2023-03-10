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
from datacatalog.connector.dats_connector import DATSConnector
from datacatalog.connector.geostudies_connector import GEOStudiesConnector
from datacatalog.connector.json_connector import JSONConnector
from datacatalog.controllers.sitemap_generator import (
    generate_sitemap,
    get_single_arg_url,
    get_multi_arg_url,
    get_dynamic_url,
)
from datacatalog.importer.entities_importer import EntitiesImporter
from datacatalog.models.dataset import Dataset
from datacatalog.models.project import Project
from datacatalog.models.study import Study
from tests.base_test import BaseTest, get_resource_path

__author__ = "Abetare Shabani"


class TestSitemapGenerator(BaseTest):
    connector = [
        JSONConnector(os.path.join(get_resource_path("records.json")), Dataset),
        GEOStudiesConnector(get_resource_path("geo_studies_test"), Study),
        DATSConnector(get_resource_path("imi_projects_test"), Project),
    ]
    entities_importer = EntitiesImporter(connector)
    host_base = app.config["BASE_URL"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.solr_orm = app.config["_solr_orm"]
        cls.solr_orm.delete_fields()
        cls.solr_orm.create_fields()

    def setUp(self):
        self.solr_orm.delete(query="*:*")
        self.entities_importer.import_all()

    def test_generate_sitemap(self):
        self.assertIsNotNone(generate_sitemap())
        self.assertTrue(generate_sitemap())

    def test_get_dynamic_url(self):
        for rule in app.url_map.iter_rules():
            if (
                not str(rule).startswith("/user")
                and "pyoidc" not in str(rule)
                and "static" not in str(rule)
            ):
                if len(rule.arguments) != 0:
                    self.assertIsNotNone(get_dynamic_url(rule, self.host_base))
                    self.assertTrue(get_dynamic_url(rule, self.host_base))

    def test_get_single_argument_url(self):
        for entity_name in app.config["entities"].keys():
            entity_class = app.config["entities"][entity_name]
            for rule in app.url_map.iter_rules():
                if (
                    len(rule.arguments) == 1
                    and not str(rule).startswith("/user")
                    and "pyoidc" not in str(rule)
                    and "static" not in str(rule)
                ):
                    self.assertIsNotNone(
                        get_single_arg_url(rule, entity_class, self.host_base)
                    )
                    self.assertTrue(
                        get_single_arg_url(rule, entity_class, self.host_base)
                    )

    def test_get_multi_arg_url(self):
        for entity_name in app.config["entities"].keys():
            entity_class = app.config["entities"][entity_name]
            for rule in app.url_map.iter_rules():
                if (
                    len(rule.arguments) > 1
                    and not str(rule).startswith("/user")
                    and "pyoidc" not in str(rule)
                    and "static" not in str(rule)
                    and "slug_name" not in rule.arguments
                    and "query" not in str(rule.arguments)
                ):
                    self.assertIsNotNone(
                        get_multi_arg_url(rule, entity_class, self.host_base)
                    )
                    self.assertTrue(
                        get_multi_arg_url(rule, entity_class, self.host_base)
                    )

    def tearDown(self):
        app.config["_solr_orm"].delete(query="*:*")
        app.config["_solr_orm"].commit()
