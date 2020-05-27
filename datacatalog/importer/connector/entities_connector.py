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
"""
    datacatalog.importer.connector.entities_connector
    -------------------

   Module containing the EntitiesConnector abstract class


"""
import datetime
import re
from abc import ABCMeta, abstractmethod
from typing import List

from ... import app
from ...solr.solr_orm_entity import SolrEntity
from ...solr.solr_orm_fields import SolrDateTimeField, SolrFloatField, SolrIntField, SolrBooleanField

__author__ = 'Valentin Grouès'

logger = app.logger


class EntitiesConnector(metaclass=ABCMeta):
    """
    Abstract class specifying the methods that must be implemented by all EntitiesConnector:
        - build_all_entities

    """
    DIRECT_MAPPING = {}
    TO_SKIP = []
    DELIMITER_MULTIVALUED = '[,;]'

    @abstractmethod
    def build_all_entities(self) -> List[SolrEntity]:
        """
        Build and returns a list of entities
        """
        pass

    def map_fields(self, entity: SolrEntity, source: dict) -> None:
        """
        Set values of entity attributes based on source and the mapping from self.DIRECT_MAPPING
        @param entity: the entity we want to configure from response
        @param source: a dict containing the values to copy
        """
        for key, value in source.items():
            if key in self.TO_SKIP:
                continue
            solr_field = self.DIRECT_MAPPING.get(key, None)
            if solr_field is None:
                logger.warn("no direct mapping for key '%s'", key)
                continue
            attribute_name = solr_field.attribute_name
            if value is not None:
                value = value.strip()
            attribute_value = value
            if solr_field.multivalued and isinstance(attribute_value, str):
                attribute_value = re.split(self.DELIMITER_MULTIVALUED, attribute_value)
                attribute_value = list(map(str.strip, attribute_value))
            if isinstance(solr_field, SolrIntField):
                if solr_field.multivalued:
                    attribute_value = [int(val.strip()) for val in attribute_value]
                else:
                    try:
                        attribute_value = int(value)
                    except TypeError:
                        logger.error("value for %s is None, cannot convert to int", attribute_name)
            if isinstance(solr_field, SolrFloatField):
                if solr_field.multivalued:
                    attribute_value = [float(val.strip()) for val in attribute_value]
                else:
                    try:
                        attribute_value = float(value)
                    except TypeError:
                        logger.error("value for %s is None, cannot convert to float", attribute_name)
            if isinstance(solr_field, SolrBooleanField):
                if solr_field.multivalued:
                    attribute_value = [(val.lower() in ['yes', 'y']) for val in attribute_value]
                else:
                    attribute_value = (value.lower() in ['yes', 'y'])
            if isinstance(solr_field, SolrDateTimeField):
                for format in ["%Y-%m-%d", "%m/%d/%Y"]:
                    try:
                        if solr_field.multivalued:
                            attribute_value = [datetime.datetime.strptime(val, format) for val in attribute_value]
                        else:
                            attribute_value = datetime.datetime.strptime(attribute_value, format)
                        break
                    except ValueError:
                        continue
                else:
                    logger.warn("date format error: %s", attribute_value)
            setattr(entity, attribute_name, attribute_value)
