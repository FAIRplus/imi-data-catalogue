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
import logging
import uuid
from datetime import datetime
from typing import Optional

from .solr_orm_fields import SolrDateTimeField, SolrField, SolrIntField

logger = logging.getLogger(__name__)
# datetime formats for json serialization
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
DATETIME_FORMAT_NO_MICRO = '%Y-%m-%dT%H:%M:%SZ'


class SolrEntity:
    """
    Base class for a solr entity
    Base entity contains a created and modified field
    Provides methods to save, delete, parse and serialize the entity
    """
    created = SolrDateTimeField("created")
    modified = SolrDateTimeField("modified")
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
        return cls.__name__.lower() + 's'

    def save(self) -> str:
        """
        Create dict representation of the entity instance and index it in solr
        Beware that this method doesn't trigger a commit
        @return: a string containing the solr response body
        """
        entity_dict = self.to_dict()
        entity_type = self.__class__.__name__.lower()
        entity_dict['id'] = entity_type + "_" + self.id
        entity_dict['type'] = entity_type
        return self._solr_orm.add(entity_dict)

    def to_dict(self) -> dict:
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
            entity_dict[entity_type + '_' + field.name] = attribute_value
        if self.id is None or isinstance(self.id, SolrField):
            self.id = str(uuid.uuid1())
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
        return self._solr_orm.delete(self.id)

    @classmethod
    def from_json(cls, entity_json: dict) -> 'SolrEntity':
        """
        Create a SolrEntity instance based on a dict containing the fields names and values
        @param entity_json: source dict
        @return: new SolrEntity instance
        """
        new_instance = cls()
        entity_type = cls.__name__.lower()
        for attribute_name, field in cls._solr_fields.items():
            solr_value = entity_json.get(entity_type + '_' + field.name)
            if solr_value is not None and field.type == 'date':
                try:
                    solr_value = datetime.strptime(solr_value, DATETIME_FORMAT)
                except:
                    solr_value = datetime.strptime(solr_value, DATETIME_FORMAT_NO_MICRO)
            if solr_value is not None and isinstance(field, SolrIntField):
                solr_value = int(solr_value)
            setattr(new_instance, attribute_name, solr_value)
        if 'id' in entity_json:
            new_instance.id = entity_json.get('id')
        return new_instance
