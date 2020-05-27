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
    datacatalog.importer.entities_importer.entities_importer
    -------------------

   Module containing the EntitiesImporter class


"""
from typing import List

from .connector.entities_connector import EntitiesConnector
from .. import app

__author__ = 'Valentin Grouès'

logger = app.logger


class EntitiesImporter(object):
    """
    Entities importer
    """

    def __init__(self, connectors: List[EntitiesConnector]) -> None:
        """
        Initialize the entities importer with a list of connectors
        @param connectors: a list of EntitiesConnector that will be used to retrieve entities
        """
        self.connectors = connectors
        for connector in connectors:
            assert (isinstance(connector, EntitiesConnector))

    def import_all(self) -> None:
        """
        Loop over the connectors to build the entities and store them in solr
        A commit is triggered at the end
        """
        logger.info("Importing all entities")
        count = 0
        for connector in self.connectors:
            entities = connector.build_all_entities()
            for entity in entities:
                entity.save()
                count += 1
        app.config['_solr_orm'].commit()
        logger.info("%s entities have been imported", count)
