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
    datacatalog.models.studyGroup
    -------------------

   Module containing the StudyGroup entity

@deprecated - fields moved to Study entity


"""
import logging

from datacatalog.solr.solr_orm import SolrAutomaticQuery
from datacatalog.solr.solr_orm_entity import SolrEntity
from datacatalog.solr.solr_orm_fields import SolrField, SolrTextField, SolrForeignKeyField, \
    SolrIntField

logger = logging.getLogger(__name__)


class StudyGroup(SolrEntity):
    """
    Study entity, subclass of SolrEntity
    """
    # specifies the list of compatibles connectors
    COMPATIBLE_CONNECTORS = ['Json']
    query_class = SolrAutomaticQuery
    title = SolrField("title")
    description = SolrTextField("description")
    size = SolrIntField("size")
    study = SolrForeignKeyField("study", entity_name="study", multivalued=False, reversed_by='studygroups',
                                reversed_multiple=True)

    def __init__(self, title: str = None, entity_id: str = None) -> None:
        """
          Initialize a new Study instance with title and entity_id
          @param title: title of the Study
          @param entity_id:  id of the Study
          """
        super().__init__(entity_id)
        self.title = title
