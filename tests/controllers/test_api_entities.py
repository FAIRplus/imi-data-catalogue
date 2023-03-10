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
import random
from unittest.mock import patch

from flask import url_for

from datacatalog import app
from datacatalog.connector.dats_connector import DATSConnector
from datacatalog.connector.geostudies_connector import GEOStudiesConnector
from datacatalog.connector.json_connector import JSONConnector
from datacatalog.controllers.api_entities import (
    api_entity,
    api_entities,
    api_search_autocomplete_entities,
    api_entity_attachments,
)
from datacatalog.importer.entities_importer import EntitiesImporter
from datacatalog.models.dataset import Dataset
from datacatalog.models.project import Project
from datacatalog.models.study import Study
from datacatalog.models.user import User
from datacatalog.storage_handler.download_handler import DownloadHandler
from tests.base_test import BaseTest, get_resource_path

__author__ = "Nirmeen Sallam"


class FakeStorageHandler(DownloadHandler):
    @staticmethod
    def can_handle(storage):
        return True

    def get_links(self, user, dataset):
        return []

    def create_link(self, user, dataset):
        return {"absolute_url": "fake"}


class TestApiEntities(BaseTest):
    connector = [
        JSONConnector(os.path.join(get_resource_path("records.json")), Dataset),
        GEOStudiesConnector(get_resource_path("geo_studies_test"), Study),
        DATSConnector(get_resource_path("imi_projects_test"), Project),
    ]
    entities_importer = EntitiesImporter(connector)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.solr_orm = app.config["_solr_orm"]
        cls.solr_orm.delete_fields()
        cls.solr_orm.create_fields()

    def setUp(self):
        self.solr_orm.delete(query="*:*")
        self.entities_importer.import_all()

    def test_api_entity(self):
        dataset = Dataset.query.all()
        study = Study.query.all()
        project = Project.query.all()
        self.assert200(api_entity("dataset", dataset[0].id))
        self.assert200(api_entity("study", study[0].id))
        self.assert200(api_entity("project", project[0].id))

    def test_api_entities(self):
        self.assertIsNotNone(api_entities("dataset").data)
        self.assert200(api_entities("dataset"))
        self.assert200(api_entities("study"))
        self.assert200(api_entities("project"))

    @patch("datacatalog.solr.solr_orm_entity.SolrEntity.list_attached_files")
    def test_api_entity_attachment(self, mock_list):
        dataset = Dataset.query.all()
        study = Study.query.all()
        project = Project.query.all()
        self.assertIsNotNone(api_entity_attachments("dataset", dataset[0].id).data)
        self.assertIsNotNone(api_entity_attachments("study", study[0].id).data)
        self.assertIsNotNone(api_entity_attachments("project", project[0].id).data)
        self.assert200(api_entity_attachments("dataset", dataset[0].id))
        self.assert200(api_entity_attachments("study", study[0].id))
        self.assert200(api_entity_attachments("project", project[0].id))

    def test_download_link_not_logged_in(self):
        with self.client as client:
            response = client.post(url_for("download_link"))
            self.assertEqual(
                302,
                response.status_code,
                "endpoint should not be available when not logged in",
            )
            self.assertIn(url_for("login"), response.location)

    @patch("flask_login.utils._get_user")
    def test_download_link_no_body(self, current_user):
        with self.client as client:
            app.config["ACCESS_HANDLERS"] = {"dataset": "Rems"}
            user = User("test", "test", "test")
            current_user.return_value = user
            response = client.post(url_for("download_link"))
            self.assertEqual(
                400,
                response.status_code,
                "endpoint should return 400 when no request body is sent",
            )
            self.assertIn("message", response.json)

    @patch("flask_login.utils._get_user")
    def test_download_link_wrong_dataset(self, current_user):
        with self.client as client:
            app.config["ACCESS_HANDLERS"] = {"dataset": "Rems"}
            user = User("test", "test", "test")
            current_user.return_value = user
            response = client.post(
                url_for("download_link"),
                data=json.dumps({"entityId": 2}),
                content_type="application/json",
            )
            self.assertEqual(
                404,
                response.status_code,
                "endpoint should return 404 when dataset doesn't exist",
            )
            self.assertIn("message", response.json)

    @patch("flask_login.utils._get_user")
    def test_download_link_no_access(self, current_user):
        random_dataset = random.choice(Dataset.query.all())

        with self.client as client:
            app.config["ACCESS_HANDLERS"] = {"dataset": "RemsOidc"}
            user = User("test", "test", "test")
            current_user.return_value = user
            response = client.post(
                url_for("download_link"),
                data=json.dumps({"entityId": random_dataset.id}),
                content_type="application/json",
            )
            self.assertEqual(
                403,
                response.status_code,
                "endpoint should return 403 when user has no access to the dataset",
            )
            self.assertIn("message", response.json)

    @patch(
        "datacatalog.authentication.pyoidc_authentication.PyOIDCAuthentication.refresh_user"
    )
    @patch("datacatalog.controllers.api_entities.get_downloads_handler")
    @patch("flask_login.utils._get_user")
    def test_download_link_access(self, current_user, get_handler, refresh_user):
        random_dataset = random.choice(Dataset.query.all())
        with self.client as client:
            app.config["ACCESS_HANDLERS"] = {"dataset": "RemsOidc"}
            app.config["DOWNLOADS_HANDLER"] = "LFT"
            user = User("test", "test", "test", accesses=[random_dataset.id])
            current_user.return_value = user
            refresh_user.return_value = user
            get_handler.return_value = FakeStorageHandler()
            response = client.post(
                url_for("download_link"),
                data=json.dumps({"entityId": random_dataset.id}),
                content_type="application/json",
            )
            self.assertEqual(
                200,
                response.status_code,
                "endpoint should return 200 if the dataset exist and the user has access",
            )
            self.assertIn("data", response.json)

    def test_api_search_autocomplete_entities(self):
        app.config["_solr_orm"].solr_config_update()
        self.assertIsNotNone(api_search_autocomplete_entities("dataset", "a").data)
        self.assertIsNotNone(api_search_autocomplete_entities("study", "a").data)
        self.assertIsNotNone(api_search_autocomplete_entities("project", "a").data)

    def tearDown(self):
        app.config["_solr_orm"].delete(query="*:*")
        app.config["_solr_orm"].commit()
