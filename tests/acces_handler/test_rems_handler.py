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

import datetime

from tests.base_test import BaseTest
from unittest.mock import MagicMock

from flask_login import current_user
from werkzeug.datastructures import ImmutableMultiDict


from datacatalog import app
from datacatalog.models.dataset import Dataset
from datacatalog.acces_handler.rems_handler import RemsAccessHandler
from datacatalog.acces_handler.access_handler import ApplicationState

__author__ = 'Nirmeen Sallam'

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class TestRemsAccessHandler(BaseTest):

    def setUp(self):
        self.assertTrue(self.app.testing)
        title = "Great dataset!"
        self.dataset = Dataset(title)
        self.dataset_id = self.dataset.id

        self.remsaccesshandler = RemsAccessHandler(current_user,
                                              app.config.get('REMS_API_USER'),
                                              app.config.get('REMS_API_KEY'),
                                              app.config.get('REMS_URL'))

    def test_requires_logged_in_user(self):
        self.assertTrue(self.remsaccesshandler.requires_logged_in_user())

    def test_supports_listing_accesses(self):
        self.assertTrue(self.remsaccesshandler.supports_listing_accesses())

    def test_has_access_application_none(self):
        self.remsaccesshandler.rems_connector.applications = MagicMock()
        self.remsaccesshandler.rems_connector.applications.return_value = []
        result = self.remsaccesshandler.has_access(self.dataset)
        self.assertFalse(result)

    def test_has_access_application_userid_not_equal_api_username(self):
        applications = [{
         'applicationapplicant': {'email': 'test@lcsb.lu',
                                  'name': 'test',
                                  'notification_email': None,
                                  'organization': None,
                                  'userid': 'test'},
         'applicationfirst_submitted': None,
         'applicationstate': 'application.state/draft'}]

        applications[0] = dotdict(applications[0])
        applications[0].applicationapplicant = dotdict(applications[0].applicationapplicant)

        self.remsaccesshandler.rems_connector.applications = MagicMock()
        self.remsaccesshandler.rems_connector.applications.return_value = applications
        result = self.remsaccesshandler.has_access(self.dataset)
        self.assertFalse(result)

    def test_has_access_application_approved(self):
        applications = [{
         'applicationapplicant': {'email': 'test@lcsb.lu',
                                  'name': 'test',
                                  'notification_email': None,
                                  'organization': None,
                                  'userid': app.config.get('REMS_API_USER')},
         'applicationfirst_submitted': None,
         'applicationstate': 'application.state/approved'}]

        applications[0] = dotdict(applications[0])
        applications[0].applicationapplicant = dotdict(applications[0].applicationapplicant)

        self.remsaccesshandler.rems_connector.applications = MagicMock()
        self.remsaccesshandler.rems_connector.applications.return_value = applications
        result = self.remsaccesshandler.has_access(self.dataset)
        self.assertEqual(result.value, ApplicationState.approved.value)

    def test_has_access_application_draft(self):
        applications = [{
         'applicationapplicant': {'email': 'test@lcsb.lu',
                                  'name': 'test',
                                  'notification_email': None,
                                  'organization': None,
                                  'userid': app.config.get('REMS_API_USER')},
         'applicationfirst_submitted': None,
         'applicationstate': 'application.state/draft'}]

        applications[0] = dotdict(applications[0])
        applications[0].applicationapplicant = dotdict(applications[0].applicationapplicant)

        self.remsaccesshandler.rems_connector.applications = MagicMock()
        self.remsaccesshandler.rems_connector.applications.return_value = applications
        result = self.remsaccesshandler.has_access(self.dataset)
        self.assertFalse(result)

    def test_my_applications(self):
        result = self.remsaccesshandler.my_applications()
        self.assertIsNotNone(result)

    def test_apply_and_has_access_submitted_application(self):
        self.remsaccesshandler.rems_connector.export_entities([self.dataset])
        form_data = ImmutableMultiDict([('fld3', 'test'), ('license_2', 'on'), ('submit', 'Send'), (
        'csrf_token', 'test')])
        form = self.remsaccesshandler.create_form(self.dataset, form_data)
        self.remsaccesshandler.apply(self.dataset, form)

        result = self.remsaccesshandler.has_access(self.dataset)
        self.assertEqual(result.value, ApplicationState.submitted.value)

    def test_get_datasets(self):
        pass

    def test_create_form(self):
        self.remsaccesshandler.rems_connector.export_entities([self.dataset])
        form_data = ImmutableMultiDict([('fld3', 'test'), ('license_2', 'on'), ('submit', 'Send'), (
            'csrf_token', 'test')])
        result = self.remsaccesshandler.create_form(self.dataset, form_data)
        self.assertEqual("FormClass", type(result).__name__)

    def test_build_application(self):
        application = {
         'applicationstate': 'application.state/draft',
         'applicationcreated': datetime.datetime(2021, 4, 2, 8, 34, 35, 587000),
         'applicationresources': [{'catalogue_itemtitle': {'en': 'Great dataset!'},
                                  'resourceext_id': '224b4550-9386-11eb-b0ff-acde48001122'}]
        }
        application = dotdict(application)
        application.applicationresources[0] = dotdict(application.applicationresources[0])

        built_application = RemsAccessHandler.build_application(application)
        self.assertEqual(built_application.state.value,'draft')

    def test_build_application_state_value_error(self):
        application = {
         'applicationstate': 'application.state/test_state_error',
         'applicationcreated': datetime.datetime(2021, 4, 2, 8, 34, 35, 587000),
         'applicationresources': [{'catalogue_itemtitle': {'en': 'Great dataset!'},
                                  'resourceext_id': '224b4550-9386-11eb-b0ff-acde48001122'}]
        }
        application = dotdict(application)
        application.applicationresources[0] = dotdict(application.applicationresources[0])

        built_application = RemsAccessHandler.build_application(application)
        self.assertIsNone(built_application.state)


