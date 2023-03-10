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
    datacatalog.exporter.entities_exporter
    -------------------

   Module containing the EntitiesExporter class


"""

import logging
from abc import ABCMeta
from typing import List

from ..connector.entities_connector import ExportEntitiesConnector

logger = logging.getLogger(__name__)


class EntitiesExporter(metaclass=ABCMeta):
    def __init__(self, connectors: List[ExportEntitiesConnector]) -> None:
        """
        Initialize the entities export with a list of connectors
        @param connectors: a list of EntitiesConnector that will be used to export entities
        """
        self.connectors = connectors
        for connector in connectors:
            assert isinstance(connector, ExportEntitiesConnector)

    def export_all(self, entities) -> None:
        """
        Loop over the connectors to build thet entities and store them in solr
        A commit is triggered at the end
        """
        logger.info("Exporting all entities")
        count = 0
        for connector in self.connectors:
            logger.info("Using connector %s", connector.__class__.__name__)
            count += connector.export_entities(entities)
        logger.info("%s entities have been exported", count)
