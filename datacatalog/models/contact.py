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
    datacatalog.models.contact
    -------------------

   Module containing the Contact entity

@deprecated - fields moved to Project entity

"""
import logging

from datacatalog.solr.solr_orm import SolrAutomaticQuery
from datacatalog.solr.solr_orm_entity import SolrEntity
from datacatalog.solr.solr_orm_fields import SolrField, SolrForeignKeyField

logger = logging.getLogger(__name__)


class ContactQuery(SolrAutomaticQuery):
    # The sort options that will be offered on the search page
    SORT_OPTIONS = ["display_name", "id"]
    # labels of the sort options that will be offered on the search page
    SORT_LABELS = ["name", "id"]
    # default sort option
    DEFAULT_SORT = 'display_name'
    # default sort order
    DEFAULT_SORT_ORDER = 'asc'


class Contact(SolrEntity):
    """
    Study entity, subclass of SolrEntity
    """
    # specifies the list of compatibles connectors
    COMPATIBLE_CONNECTORS = ['Json']
    query_class = ContactQuery
    affiliation = SolrForeignKeyField("affiliation", entity_name='organization', multivalued=True)
    display_name = SolrField("display_name")
    email = SolrField("contact_email", indexed=False)
    first_name = SolrField("contact_first_name")
    last_name = SolrField("contact_last_name")
    role = SolrField("role", multivalued=True)


def __init__(self, display_name: str = None, entity_id: str = None) -> None:
    """
      Initialize a new Contact instance with display_name and entity_id
      @param name: display_name of the Contact
      @param entity_id:  id of the Contact
      """
    super().__init__(entity_id)
    self.display_name = display_name
