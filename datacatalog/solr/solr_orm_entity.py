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
    datacatalog.solr.solr_orm_entity
    -------------------

   Module containing the SolrEntity class

"""
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Any

from .solr_orm_fields import SolrDateTimeField, SolrField, SolrIntField, SolrJsonField
from .. import app
from ..connector.file_storage_connectors.webdav_file_connector import (
    WebdavFileStorageConnector,
)

logger = logging.getLogger(__name__)
# datetime formats for json serialization
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DATETIME_FORMAT_NO_MICRO = "%Y-%m-%dT%H:%M:%SZ"


class SolrEntity:
    """
    Base class for a solr entity
    Base entity contains a created and modified field
    Provides methods to save, delete, parse ans serialize the entity
    """

    created = SolrDateTimeField("created")
    modified = SolrDateTimeField("modified")
    former_ids = SolrField("former_ids", multivalued=True, indexed=False)
    connector_name = SolrField("connector_name", multivalued=False, indexed=False)

    # dict holding reverse foreign keys references
    reversed_field = {}
    query = None
    _solr_orm = None

    def __init__(self, entity_id: Optional[str] = None) -> None:
        """
        Initialize a SolrEntity instance setting its id or generating one if none is provided.
        Generated id is based on uuid.uuid1 method.
        Also initialize the created and modified date to current datetime.
        @param entity_id: entity id or None if id should be generated
        @type entity_id:
        """
        for attribute_name in self._solr_fields.keys():
            setattr(self, attribute_name, None)
        if entity_id is None:
            self.id = str(uuid.uuid1())
        else:
            self.id = entity_id
        self.created = datetime.now()
        self.modified = self.created

    @classmethod
    def plural_name(cls) -> str:
        """
        Plural form of the entity name for display
        @return: a string representing the plural version of the entity name
        """
        return cls.__name__.lower() + "s"

    def __getattr__(self, attribute: str) -> Any:
        """
        check if we have foreign key reference and resolve it if it's the case
        @todo: ADD caching
        @param attribute: name of the attribute
        @return: list of entities if many to many relationship
        """
        elements = attribute.rsplit("_")
        suffix = elements[-1]
        prefix = "".join(elements[0:-1])
        if suffix in ["entities", "entity"]:
            # check if it's a reversed relationship
            if prefix in self.reversed_field:
                (
                    source_entity_name,
                    field_name,
                    field_reversed_multiple,
                ) = self.reversed_field[prefix]
                source_entity_class = app.config.get("entities").get(source_entity_name)
                holding_entities = source_entity_class.query.search_holding_entities(
                    field_name=field_name,
                    target_entity_id=self.id,
                    source_entity_type=source_entity_name,
                ).entities
                if field_reversed_multiple or not holding_entities:
                    return holding_entities
                else:
                    return holding_entities[0]
            else:
                entities_ids = getattr(self, prefix, [])
                results = []
                if entities_ids:
                    # get foreign entity type
                    linked_entity_name = self._solr_fields[prefix].linked_entity_name
                    linked_entity_class = app.config["entities"][linked_entity_name]
                    for entity_id in entities_ids:
                        linked_entity = linked_entity_class.query.get(entity_id)
                        results.append(linked_entity)
            return results
        raise AttributeError(
            "'{}' object has no attribute '{}'".format(
                self.__class__.__name__, attribute
            )
        )

    def save(self, commit=False) -> str:
        """
        Create dict representation of the entity instance and index it in solr
        Beware that this method doesn't trigger a commit
        @return: a string containing the solr response body
        """
        entity_dict = self.to_dict()
        entity_type = self.__class__.__name__.lower()
        entity_dict["id"] = entity_type + "_" + entity_dict["id"]
        entity_dict["type"] = entity_type
        logger.info("Indexing entity %s (%s)", self.id, entity_type)
        for field_name, info in self.reversed_field.items():
            source_entity_class_name, reversed_field_name, reversed_multiple = info
            field_value = getattr(self, field_name, None)
            if field_value and self.id:
                # get linked entity     from solr
                source_entity_class = app.config["entities"].get(
                    source_entity_class_name
                )
                source_entity = source_entity_class.query.get(field_value)
                if source_entity:
                    entities = getattr(source_entity, reversed_field_name, []) or []
                    entities.append(self.id)
                    setattr(source_entity, reversed_field_name, entities)
                    source_entity.save()
        result_add = self._solr_orm.add(entity_dict)
        if commit:
            self._solr_orm.commit()
        return result_add

    def to_dict(self, add_prefix=True) -> dict:
        """
        Create a dict containing all attributes as key and the field values as value
        @return: dict representation of the entity instance
        """
        entity_dict = {}
        entity_type = self.__class__.__name__.lower()
        for attribute_name, field in self.__class__._solr_fields.items():
            attribute_value = getattr(self, attribute_name, None)
            if isinstance(attribute_value, SolrField):
                attribute_value = None
            if add_prefix:
                key = entity_type + "_" + field.name
            else:
                key = field.name
            if isinstance(field, SolrJsonField):
                if field.model:
                    if attribute_value is not None:
                        for count, value in enumerate(attribute_value):
                            attribute_value[count] = json.dumps(value.to_json())
                else:
                    attribute_value = json.dumps(attribute_value)
            entity_dict[key] = attribute_value
        if self.id is None or isinstance(self.id, SolrField):
            self.id = str(uuid.uuid1())
        entity_dict["id"] = self.id.replace(" ", "_")
        return entity_dict

    def to_api_dict(self) -> dict:
        """
        Similar to method to_dict but can be used to restrict the list of fields exported via api endpoints.
        @return: dict representation of the entity instance
        """
        return self.__dict__

    def delete(self) -> str:
        """
        Delete an entity from Solr
        Beware that this method doesn't trigger a commit
        @return:
        """
        logger.info("Deleting entity %s", self.id)
        return self._solr_orm.delete(self.id)

    @classmethod
    def from_json(cls, entity_json: dict) -> "SolrEntity":
        """
        Create a SolrEntity instance based on a dict containing the fields names and values
        @param entity_json: source dict
        @return: new SolrEntity instance
        """
        new_instance = cls()
        entity_type = cls.__name__.lower()
        for attribute_name, field in cls._solr_fields.items():
            solr_value = entity_json.get(entity_type + "_" + field.name)
            if solr_value is not None and field.type == "date":
                try:
                    solr_value = datetime.strptime(solr_value, DATETIME_FORMAT)
                except ValueError:
                    solr_value = datetime.strptime(solr_value, DATETIME_FORMAT_NO_MICRO)
            if solr_value is not None and isinstance(field, SolrIntField):
                solr_value = int(solr_value)
            setattr(new_instance, attribute_name, solr_value)
        if "id" in entity_json:
            new_instance.id = entity_json.get("id")
        return new_instance

    def attachment_url(self) -> str:
        entity_name = self.__class__.__name__.lower()
        return app.config["PUBLIC_FILE_STORAGE_ROOT"] + f"/{entity_name}/{self.id}"

    def attachment_exists(self) -> bool:
        """
        This method checks if the entity has attachment files stored in the file storage

        Returns:
            bool: True if attachments were found, else False
        """
        connector = WebdavFileStorageConnector()
        attachments_folder = self.attachment_url()
        return connector.folder_exists(attachments_folder)

    def list_attached_files(self) -> str:
        """
        This method search for the files attached to this entity in the file storage.

        Returns:
            list: A list built by parse_webdav_response if the requests was answered successfully. [] if not
        """
        connector = WebdavFileStorageConnector()
        attachments_folder = self.attachment_url()

        return connector.list_files(attachments_folder)

    def set_computed_values(self):
        pass
