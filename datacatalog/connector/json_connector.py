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
    datacatalog.connector.json_connector
    -------------------

   Module containing the JsonConnector class


"""
import json
from math import isnan
from typing import Type, Generator

from .entities_connector import ImportEntitiesConnector
from .. import app
from ..solr.solr_orm_entity import SolrEntity

__author__ = 'Valentin Grouès'

logger = app.logger


class JSONConnector(ImportEntitiesConnector):
    """
    Import entities directly from a JSON file
    """

    def __init__(self, json_file_path: str, entity_class: Type[SolrEntity]) -> None:
        """
        Initialize a JSONConnector instance configuring the json file path and the entity class
        The build_all_entities methods will then create instances of entity_class from the json file json_file_path
        @param json_file_path: the path of json file containing the serialized entities
        @param entity_class: the class to instantiate
        """
        self.entity_class = entity_class
        self.json_file_path = json_file_path

    def build_all_entities(self) -> Generator[SolrEntity, None, None]:
        """
        Yields instances of self.entity_class parsed from the json file self.json_file_path
        """
        with open(self.json_file_path, encoding='utf8') as json_file:
            data = json.load(json_file)
            for entity in data['docs']:
                new_entity = self.entity_class()
                for key in entity:
                    value = entity[key]
                    if type(value) == float and isnan(value):
                        value = None
                    setattr(new_entity, key, value)
                yield new_entity
