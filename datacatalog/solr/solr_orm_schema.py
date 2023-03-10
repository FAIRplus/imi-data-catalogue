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

"""
    datacatalog.solr.solr_orm_schema
    -------------------

   Module containing the SolrSchemaAdmin class

"""
import logging

import requests

from .. import app

logger = logging.getLogger(__name__)


class SolrSchemaAdmin:
    """
    Class to manipulate solr schema
    Create and delete fields
    """

    def __init__(self, url):
        self.url = url
        self.solr_query_fields = app.config.get(
            "SOLR_QUERY_TEXT_FIELD",
            {"dataset": ["title"], "project": ["title"], "study": ["title"]},
        )
        if app.config.get("SOLR_QUERY_SEARCH_EXTENDED"):
            if "datasets_metadata" not in self.solr_query_fields.get("project"):
                self.solr_query_fields.get("project").extend(
                    ["datasets_metadata", "studies_metadata"]
                )
            if not app.config.get(
                "SOLR_QUERY_SEARCH_EXTENDED_2_WAY_INDEX"
            ) and "datasets_metadata" not in self.solr_query_fields.get("study"):
                self.solr_query_fields.get("study").append("datasets_metadata")
            if app.config.get(
                "SOLR_QUERY_SEARCH_EXTENDED_2_WAY_INDEX"
            ) and "projects_metadata" not in self.solr_query_fields.get("study"):
                self.solr_query_fields.get("study").extend(
                    ["datasets_metadata", "projects_metadata"]
                )
                self.solr_query_fields.get("dataset").extend(
                    ["studies_metadata", "projects_metadata"]
                )

    def create_field(
        self,
        field_name: str,
        field_type: str,
        index: bool = True,
        store: bool = False,
        multivalued: bool = False,
    ) -> None:
        """
        Create a solr field
        @param field_name: name of the field to create
        @param field_type: type of the field to create
        @param index: should the field be marked as indexed
        @param store: should the field be marked as stored
        @param multivalued: should the field be marked as multivalued
        """
        logger.debug("creating field %s", field_name)
        json_create = {
            "add-field": {
                "name": field_name,
                "type": field_type,
                "stored": store,
                "indexed": index,
                "multiValued": multivalued,
            }
        }
        ret = requests.post(self.url, json=json_create)
        ret.raise_for_status()

    def update_field(
        self,
        field_name: str,
        field_type: str,
        index: bool = True,
        store: bool = False,
        multivalued: bool = False,
    ) -> None:
        """
        Update a solr field
        @param field_name: name of the field to update
        @param field_type: type of the field to update
        @param index: should the field be marked as indexed
        @param store: should the field be marked as stored
        @param multivalued: should the field be marked as multivalued
        """
        logger.debug("updating field %s", field_name)
        ret = requests.post(
            self.url,
            json={
                "replace-field": {
                    "name": field_name,
                    "type": field_type,
                    "stored": store,
                    "indexed": index,
                    "multiValued": multivalued,
                }
            },
        )
        ret.raise_for_status()

    def delete_field(self, field_name: str) -> None:
        """
        Delete a solr field
        @param field_name: the field to delete
        @return: raises an exception if not successful
        """
        logger.debug("deleting field %s", field_name)
        ret = requests.post(self.url, json={"delete-field": {"name": field_name}})
        ret.raise_for_status()
