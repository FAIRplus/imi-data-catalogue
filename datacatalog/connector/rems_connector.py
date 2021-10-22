#  coding=utf-8
#   DataCatalog
#   Copyright (C) 2020  University of Luxembourg
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
from typing import List

import remsclient
from flask import url_for
from remsclient import WriteCatalogueItemLocalizations
from remsclient.rest import ApiException

from .entities_connector import ExportEntitiesConnector
from .. import app
from ..exceptions import CouldNotCloseApplicationException
from ..solr.solr_orm_entity import SolrEntity

logger = logging.getLogger(__name__)


class UserDoesntExistException(Exception):
    pass


class CatalogueItemDoesntExistException(Exception):
    pass


class RemsConnector(ExportEntitiesConnector):

    def __init__(self, api_username, api_key, host, verify_ssl=True, admin_user=None):
        self.rems_configuration = remsclient.Configuration()
        self.rems_configuration.api_key = api_key
        self.rems_configuration.api_username = api_username
        self.rems_configuration.verify_ssl = verify_ssl
        self.rems_configuration.host = host
        self.rems_client = remsclient.ApiClient(configuration=self.rems_configuration)
        self.authentication_kwargs = {
            "x_rems_api_key": self.rems_configuration.api_key,
            "x_rems_user_id": self.rems_configuration.api_username
        }
        if admin_user:
            self.authentication_kwargs_admin = {
                "x_rems_api_key": self.rems_configuration.api_key,
                "x_rems_user_id": admin_user
            }
        else:
            self.authentication_kwargs_admin = self.authentication_kwargs
        self.resource_ids = self.load_resources()
        self.form_id = 6
        self.wfid = 4

    def create_application(self, items):
        rems_applications = remsclient.ApplicationsApi(self.rems_client)
        body = remsclient.CreateApplicationCommand(catalogue_item_ids=items)
        response = rems_applications.api_applications_create_post(body, **self.authentication_kwargs)
        return response.application_id

    def save_application_draft(self, application_id, form_id, fields):
        rems_applications = remsclient.ApplicationsApi(self.rems_client)
        field_values = []
        for field_name, value in fields.items():
            field_values.append(remsclient.SaveDraftCommandFieldValues(form=form_id, field=field_name, value=value))
        body = remsclient.SaveDraftCommand(application_id=application_id, field_values=field_values)
        response = rems_applications.api_applications_save_draft_post(body, **self.authentication_kwargs)
        return response.success

    def export_entities(self, entities: List[SolrEntity]):

        rems_catalogue = remsclient.CatalogueItemsApi(self.rems_client)
        rems_resource = remsclient.ResourcesApi(self.rems_client)

        for entity in entities:
            entity_name = type(entity).__name__.lower()
            res_id = entity.id
            # resource
            if res_id in self.resource_ids:
                res_id_int = self.resource_ids[res_id]
            else:
                body_resource = remsclient.CreateResourceCommand(resid=res_id, organization="LCSB", licenses=[2])
                result = rems_resource.api_resources_create_post(body_resource, **self.authentication_kwargs)
                res_id_int = result.id
            # catalogue item
            localizations = WriteCatalogueItemLocalizations({
                "en": {
                    "title": entity.title,
                    "infourl": app.config.get('BASE_URL', '') + url_for('entity_details', entity_name=entity_name,
                                                                        entity_id=entity.id)
                }
            })
            if res_id in self.resource_ids:
                # check if there is a corresponding catalogue entry
                items = rems_catalogue.api_catalogue_items_get(resource=res_id, **self.authentication_kwargs)
                if items:
                    item = items[0]
                    # if catalogue entry already exist, we update it
                    if item.formid == self.form_id and item.wfid == self.wfid:
                        body_item = remsclient.EditCatalogueItemCommand(item.id, localizations=localizations)
                        rems_catalogue.api_catalogue_items_edit_put(body_item, **self.authentication_kwargs)
                        continue
                    else:
                        # form id or wfid changed, we archive the old item
                        body = remsclient.ArchivedCommand(item.id, archived=True)
                        rems_catalogue.api_catalogue_items_archived_put(body, **self.authentication_kwargs)

            # if resource is new or catalogue entry doesn't exist, we create it

            body_item = remsclient.CreateCatalogueItemCommand(resid=res_id_int, form=self.form_id, wfid=self.wfid,
                                                              enabled=True, localizations=localizations)
            rems_catalogue.api_catalogue_items_create_post(body_item, **self.authentication_kwargs)

    def load_resources(self):
        rems_resources = remsclient.ResourcesApi(self.rems_client)
        all_resources = rems_resources.api_resources_get(**self.authentication_kwargs_admin)
        resources_ids = dict()
        for r in all_resources:
            if not r.archived and r.enabled:
                resources_ids[r.resid] = r.id
        return resources_ids

    def get_catalogue_item(self, dataset_id):
        rems_catalogue = remsclient.CatalogueItemsApi(self.rems_client)
        items = rems_catalogue.api_catalogue_items_get(resource=dataset_id, **self.authentication_kwargs)
        if len(items) == 0:
            raise CatalogueItemDoesntExistException(f"no catalogue item found for resource {dataset_id}")
        return items[0]

    def get_resource(self, resource_id):
        rems_resource = remsclient.ResourcesApi(self.rems_client)
        resource = rems_resource.api_resources_resource_id_get(resource_id, **self.authentication_kwargs_admin)
        return resource

    def get_form_for_catalogue_item(self, form_id):
        api_instance = remsclient.FormsApi(self.rems_client)
        return api_instance.api_forms_form_id_get(form_id, **self.authentication_kwargs_admin)

    def accept_license(self, application_id, license_ids):
        rems_applications = remsclient.ApplicationsApi(self.rems_client)
        body = remsclient.AcceptLicensesCommand(application_id, license_ids)
        rems_applications.api_applications_accept_licenses_post(body, **self.authentication_kwargs)

    def submit_application(self, application_id):
        rems_applications = remsclient.ApplicationsApi(self.rems_client)
        body = remsclient.SubmitCommand(application_id)
        rems_applications.api_applications_submit_post(body, **self.authentication_kwargs)

    def close_application(self, application_id):
        rems_applications = remsclient.ApplicationsApi(self.rems_client)
        body = remsclient.CloseCommand(application_id, comment="cancelled by the user through the data catalogue")
        try:
            result = rems_applications.api_applications_close_post(body, **self.authentication_kwargs_admin)
            if not result.success:
                raise CouldNotCloseApplicationException(result.errors[0]['type'])
        except ApiException as e:
            raise CouldNotCloseApplicationException(e)

    def my_applications(self):
        try:
            rems_applications = remsclient.ApplicationsApi(self.rems_client)
            return rems_applications.api_my_applications_get(**self.authentication_kwargs)
        except ApiException:
            return []

    def applications(self, query):
        try:
            rems_applications = remsclient.ApplicationsApi(self.rems_client)
            kwargs = dict(self.authentication_kwargs)
            kwargs["query"] = query
            return rems_applications.api_applications_get(**kwargs)
        except ApiException:
            return []

    def create_user(self, user_id, name, email):
        rems_users = remsclient.UsersApi(self.rems_client)
        body = remsclient.CreateUserCommand(user_id, name, email)
        return rems_users.api_users_create_post(body, **self.authentication_kwargs_admin)

    def add_attachment(self, application_id, file_path):
        rems_attachment = remsclient.ApplicationsApi(self.rems_client)
        response = rems_attachment.api_applications_add_attachment_post(file_path, application_id,
                                                                        **self.authentication_kwargs)
        return response.id

    def get_application(self, application_id):
        rems_application = remsclient.ApplicationsApi(self.rems_client)
        application = rems_application.api_applications_application_id_get(application_id,
                                                                           **self.authentication_kwargs)
        return application
