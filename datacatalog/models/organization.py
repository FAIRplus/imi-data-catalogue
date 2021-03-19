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
    datacatalog.models.organization
    -------------------

   Module containing the Organization entity

@deprecated - fields moved to Project entity


"""
import logging

from datacatalog.solr.solr_orm import SolrAutomaticQuery
from datacatalog.solr.solr_orm_entity import SolrEntity
from datacatalog.solr.solr_orm_fields import SolrField

logger = logging.getLogger(__name__)


class Organization(SolrEntity):
    """
    Study entity, subclass of SolrEntity
    """
    # specifies the list of compatibles connectors
    COMPATIBLE_CONNECTORS = ['Json']
    query_class = SolrAutomaticQuery
    business_address = SolrField("business_address", indexed=False)
    business_fax_number = SolrField("business_fax_number", indexed=False)
    business_phone_number = SolrField("business_phone_number", indexed=False)
    title = SolrField("title")

    def __init__(self, title: str = None, entity_id: str = None) -> None:
        """
          Initialize a new Organization instance with title and entity_id
          @param title: title of the Organization
          @param entity_id:  id of the Organization
          """
        super().__init__(entity_id)
        self.title = title
