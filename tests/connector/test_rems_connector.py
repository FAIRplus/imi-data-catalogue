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

import shutil
import tempfile
import unittest
from os import path

from datacatalog import app
from datacatalog.acces_handler.rems_handler import FieldBuilder
from datacatalog.connector.rems_connector import RemsConnector
from datacatalog.models.dataset import Dataset
from tests.base_test import BaseTest

__author__ = "Nirmeen Sallam"


class TestRemsConnector(BaseTest):
    def setUp(self):
        self.assertTrue(self.app.testing)
        title = "Great dataset!"
        self.dataset = Dataset(title)
        self.dataset.e2e = True
        self.dataset_id = self.dataset.id
        self.rems_connector = RemsConnector(
            app.config.get("REMS_API_USER"),
            app.config.get("REMS_API_KEY"),
            app.config.get("REMS_URL"),
            app.config.get("REMS_FORM_ID"),
            app.config.get("REMS_WORKFLOW_ID"),
            app.config.get("REMS_ORGANIZATION_ID"),
            app.config.get("REMS_LICENSES"),
            app.config.get("REMS_VERIFY_SSL"),
        )

    def test_create_application(self):
        self.rems_connector.export_entities([self.dataset])
        catalogue_item = self.rems_connector.get_catalogue_item(self.dataset_id)
        response_id = self.rems_connector.create_application([catalogue_item.id])
        self.assertIsNotNone(response_id)

    def test_save_application_draft(self):
        self.rems_connector.export_entities([self.dataset])
        catalogue_item = self.rems_connector.get_catalogue_item(self.dataset.id)
        rems_form = self.rems_connector.get_form_for_catalogue_item(
            catalogue_item.formid
        )
        field_values = {}
        # create application
        application_id = self.rems_connector.create_application([catalogue_item.id])
        for field in rems_form.formfields:
            rems_field_id = field.fieldid
            wtf_field = FieldBuilder.build_field_builder(field)
            flask_form_value = "test"
            field_values[rems_field_id] = wtf_field.transform_value(
                flask_form_value, self.rems_connector, application_id
            )
        # save draftFormTemplate
        response = self.rems_connector.save_application_draft(
            application_id, rems_form.formid, field_values
        )
        self.assertTrue(response)

    def test_export_entities_already_exported(self):
        self.rems_connector.export_entities([self.dataset])
        catalogue_item = self.rems_connector.get_catalogue_item(self.dataset_id)
        self.rems_connector.export_entities([self.dataset])
        catalogue_item_2 = self.rems_connector.get_catalogue_item(self.dataset_id)
        self.assertEqual(catalogue_item.resid, catalogue_item_2.resid)

    def test_load_resources(self):
        self.rems_connector.export_entities([self.dataset])
        resources_ids = self.rems_connector.load_resources()
        self.assertIsNotNone(resources_ids)

    def test_get_catalogue_item(self):
        self.rems_connector.export_entities([self.dataset])
        catalogue_item = self.rems_connector.get_catalogue_item(self.dataset_id)
        self.assertEqual(catalogue_item.resid, self.dataset_id)

    def test_get_resource(self):
        self.rems_connector.export_entities([self.dataset])
        catalogue_item = self.rems_connector.get_catalogue_item(self.dataset_id)
        resource = self.rems_connector.get_resource(catalogue_item.resource_id)
        self.assertEqual(resource.resid, catalogue_item.resid)

    def test_get_form_for_catalogue_item(self):
        self.rems_connector.export_entities([self.dataset])
        catalogue_item = self.rems_connector.get_catalogue_item(self.dataset.id)
        form = self.rems_connector.get_form_for_catalogue_item(catalogue_item.formid)
        self.assertIsNotNone(form)

    def test_accept_license(self):
        self.rems_connector.export_entities([self.dataset])
        catalogue_item = self.rems_connector.get_catalogue_item(self.dataset.id)
        application_id = self.rems_connector.create_application([catalogue_item.id])
        resource_id = catalogue_item.resource_id
        resource = self.rems_connector.get_resource(resource_id)
        licenses = resource.licenses
        license_ids = []
        for license in licenses:
            license_id = license.id
            license_ids.append(license_id)

        applications = self.rems_connector.applications(
            ("applicationid", application_id)
        )
        self.assertFalse(applications[0].applicationaccepted_licenses)

        self.rems_connector.accept_license(application_id, license_ids)

        applications = self.rems_connector.applications(
            ("applicationid", application_id)
        )
        self.assertTrue(applications[0].applicationaccepted_licenses)

    def test_submit_application(self):
        self.rems_connector.export_entities([self.dataset])
        catalogue_item = self.rems_connector.get_catalogue_item(self.dataset.id)
        rems_form = self.rems_connector.get_form_for_catalogue_item(
            catalogue_item.formid
        )
        # create application
        application_id = self.rems_connector.create_application([catalogue_item.id])
        # save draftFormTemplate
        self.rems_connector.save_application_draft(
            application_id, rems_form.formid, {"fld1": "test"}
        )

        resource_id = catalogue_item.resource_id
        resource = self.rems_connector.get_resource(resource_id)
        licenses = resource.licenses
        license_ids = []
        for license in licenses:
            license_id = license.id
            license_ids.append(license_id)

        applications = self.rems_connector.applications(
            ("applicationid", application_id)
        )
        self.assertIsNone(applications[0].applicationfirst_submitted)

        self.rems_connector.accept_license(application_id, license_ids)
        self.rems_connector.submit_application(application_id)

        applications = self.rems_connector.applications(
            ("applicationid", application_id)
        )
        self.assertIsNotNone(applications[0].applicationfirst_submitted)

    def test_my_applications(self):
        result = self.rems_connector.my_applications()
        self.assertIsNotNone(result)

    def test_applications(self):
        applications = self.rems_connector.applications("")
        self.assertIsNotNone(applications)

    def test_create_user(self):
        response = self.rems_connector.create_user(
            app.config.get("REMS_API_USER"), "test", "test@lcsb.lu"
        )
        self.assertTrue(response.success)

    @unittest.skip("attachments not working with last rems version")
    def test_add_attachment(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

        open(path.join(self.test_dir, "test.pdf"), "w").close()
        self.rems_connector.export_entities([self.dataset])
        catalogue_item = self.rems_connector.get_catalogue_item(self.dataset.id)
        application_id = self.rems_connector.create_application([catalogue_item.id])
        response_id = self.rems_connector.add_attachment(
            application_id, path.join(self.test_dir, "test.pdf")
        )
        self.assertIsNotNone(response_id)

        # Remove the directory after the test
        shutil.rmtree(self.test_dir)
