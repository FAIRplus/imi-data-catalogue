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
import re
import shutil
import tempfile
import unittest
from os import path

import datacatalog
from unittest.mock import MagicMock, patch
from datacatalog.models.user import User
from tests.base_test import BaseTest, get_resource_path
from datacatalog.controllers.web_controllers import *
import datacatalog.controllers.login_controllers
from datacatalog.connector.dats_connector import DATSConnector
from datacatalog.connector.geostudies_connector import GEOStudiesConnector
from datacatalog.connector.json_connector import JSONConnector
from datacatalog.importer.entities_importer import EntitiesImporter
from datacatalog.models.dataset import Dataset
from datacatalog.models.project import Project
from datacatalog.models.study import Study


__author__ = 'Nirmeen Sallam'


class TestWebControllers(BaseTest):

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
        self.dataset_length = len(Dataset.query.all())

        self.project_length = len(Project.query.all())
        self.study_length = len(Study.query.all())

    def test_make_key(self):
        self.assertIsNotNone(make_key())

    def test_csrf_error(self):
        response = csrf_error('CSRF validation failed.')
        self.assertIn('Error 400 - CSRF validation failed.', response[0])

    def test_authentication_errors(self):
        response = authentication_errors(AuthenticationException("Invalid Credentials"))
        self.assertIn('Invalid Credentials', response[0])

    def test_page_not_found(self):
        response = page_not_found(Exception("Page not found"))
        self.assertIn('Page not found', response[0])

    def test_entities_search(self):
        with self.client as client:
            entities = client.get("/datasets")
            self.assertIn(f'{self.dataset_length} datasets found', re.sub(r'\s+', " ", entities.data.decode('utf-8')))

    def test_home(self):
        with self.client as client:
            landing_page = client.get("/")
            self.assertEqual(landing_page.status_code, 200)
            cleanrgex = re.compile('<.*?>')
            landing_cleantext = re.sub(cleanrgex, ' ', landing_page.data.decode('utf-8'))
            landing_cleantext = re.sub(r'\s+', ' ', landing_cleantext)
            self.assertIn('Data Catalog - Home', landing_cleantext)
            self.assertIn(f'Datasets {self.dataset_length}', landing_cleantext)
            self.assertIn(f'Projects {self.project_length}', landing_cleantext)
            self.assertIn(f'Studies {self.study_length}', landing_cleantext)

    def test_no_landing(self):
        with app.app_context():
            app.config['NO_LANDING'] = True
        with self.client as client:
            landing_page = client.get("/")

        self.assertIn('Data Catalog - Home', landing_page.data.decode('utf-8'))
        self.assertIn(f'{self.dataset_length} datasets found', re.sub(r'\s+', " ", landing_page.data.decode('utf-8')))

    def test_search(self):
        with self.client as client:
            search_result = client.get("/search")

            self.assertIn('Data Catalog - Home', search_result.data.decode('utf-8'))
            self.assertIn(f'{self.dataset_length} datasets found', re.sub(r'\s+', " ", search_result.data.decode('utf-8')))

    def test_entity_details(self):
        datasets = Dataset.query.all()
        if len(datasets) > 0:
            with self.client as client:
                entity = client.get(f'/e/dataset/{datasets[0].id}')
            cleanrgex = re.compile('<.*?>')
            entity_cleantext = re.sub(cleanrgex, ' ', entity.data.decode('utf-8'))
            entity_cleantext = re.sub(r'\s+', ' ', entity_cleantext)
            self.assertIn(datasets[0].title, entity_cleantext)

    @patch('flask_login.utils._get_user')
    def test_entity_details_authenticated_user(self, current_user):
        user = User('test', 'test', 'test')
        current_user.return_value = user
        client = app.test_client()

        datasets = Dataset.query.all()
        if len(datasets) > 0:
            entity = client.get(f'/e/dataset/{datasets[0].id}')
            cleanrgex = re.compile('<.*?>')
            entity_cleantext = re.sub(cleanrgex, ' ', entity.data.decode('utf-8'))
            entity_cleantext = re.sub(r'\s+', ' ', entity_cleantext)
            self.assertIn(datasets[0].title, entity_cleantext)

    def test_get_entity(self):
        datasets = Dataset.query.all()
        if len(datasets) > 0:
            entity = get_entity('dataset', datasets[0].id)
            self.assertEqual(datasets[0].title, entity.title)

    def test_about(self):
        with self.client as client:
            about_page = client.get('/about')
            self.assertIn('Data Catalog - About', about_page.data.decode('utf-8'))

    def test_help(self):
        with self.client as client:
            help_page = client.get('/help')
            self.assertIn('Data Catalog - Help', help_page.data.decode('utf-8'))

    def test_export_dats_entity(self):
        datasets = Dataset.query.all()
        if len(datasets) > 0:
            with self.client as client:
                export_response = client.get(f'/export_dats_entity/dataset/{datasets[0].id}')
                data = export_response.data.decode('utf-8')
                self.assertIn(datasets[0].id, data)

    def test_request_access_require_login(self):
        app.config["ACCESS_HANDLERS"] = {'dataset': 'Rems'}
        datasets = Dataset.query.all()
        if len(datasets) > 0:
            with self.client as client:
                request_access_response = client.get(url_for('request_access',entity_name="dataset",
                                                             entity_id=datasets[0].id))
                self.assertIn(url_for('login'), request_access_response.location)

    @unittest.skip('rems request access not used in production')
    @patch('flask_login.utils._get_user')
    def test_request_access_get(self, current_user):
        user = User('test', 'test', 'test')
        current_user.return_value = user
        client = app.test_client()

        datasets = Dataset.query.all()
        if len(datasets) > 0:
            request_access_response = client.get(url_for('request_access',entity_name="dataset",
                                                             entity_id=datasets[0].id))
            cleanregex = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
            request_access_response = re.sub(cleanregex, ' ', request_access_response.data.decode('utf-8'))
            request_access_response = re.sub(r'\s+', ' ', request_access_response)
            self.assertIn(f'Request access to {datasets[0].title}', request_access_response)

    def test_request_access_no_access_handler(self):
        datasets = Dataset.query.all()
        if len(datasets) > 0:
            app.config["ACCESS_HANDLERS"] = {'dataset': None}

            with self.client as client:
                datacatalog.get_access_handler = MagicMock()
                datacatalog.get_access_handler.return_value = {}
                request_access_response = client.get(url_for('request_access',entity_name="dataset",
                                                             entity_id=datasets[0].id))
                self.assertIn('Error 400 - No compatible request handlers for this entity', request_access_response.data.decode('utf-8'))

    @unittest.skip('rems request access not used in production')
    @patch('flask_login.utils._get_user')
    def test_request_access_invalid_form(self, current_user):
        user = User('test', 'test', 'test')
        current_user.return_value = user
        client = app.test_client()

        datasets = Dataset.query.all()
        if len(datasets) > 0:
            request_access_response = client.post(url_for('request_access',entity_name="dataset",
                                                             entity_id=datasets[0].id))
            cleanregex = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
            request_access_response = re.sub(cleanregex, ' ', request_access_response.data.decode('utf-8'))
            request_access_response = re.sub(r'\s+', ' ', request_access_response)
            self.assertIn(f'Request access to {datasets[0].title}', request_access_response)

    @unittest.skip('rems request access not used in production')
    @patch('flask_login.utils._get_user')
    def test_request_access_success(self, current_user):
        app.config["ACCESS_HANDLERS"] = {'dataset': 'Rems'}
        user = User('test', 'test', 'test')
        current_user.return_value = user
        client = app.test_client()

        datasets = Dataset.query.all()
        if len(datasets) > 0:
            request_access_response = client.post(url_for('request_access',entity_name="dataset",
                                                             entity_id=datasets[0].id),
                                                      data={"fld3":"test","license_2":"on"})
            self.assertRedirects(request_access_response, url_for('search'))

    def test_custom_static(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

        open(path.join(self.test_dir, 'test.pdf'), 'w').close()

        with self.client as client:
            response = client.get(f'/static_plugin/{path.join(self.test_dir, "test.pdf")}')
        self.assertEqual(response.status_code, 404)
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    @patch('flask_login.utils._get_user')
    def test_my_applications(self, current_user):
        app.config["ACCESS_HANDLERS"] = {'dataset': 'Rems'}
        user = User('test', 'test', 'test')
        current_user.return_value = user
        client = app.test_client()
        applications = client.get("/user/my_applications/dataset")
        cleanrgex = re.compile('<.*?>')
        applications_cleantext = re.sub(cleanrgex, ' ', applications.data.decode('utf-8'))
        applications_cleantext = re.sub(r'\s+', ' ', applications_cleantext)
        self.assertIn('My applications', applications_cleantext)

    def tearDown(self):
        app.config['_solr_orm'].delete(query='*:*')
        app.config['_solr_orm'].commit()
