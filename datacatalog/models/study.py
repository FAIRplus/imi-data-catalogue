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
    datacatalog.models.study
    -------------------

   Module containing the Study entity


"""
import logging

from datacatalog.models import DatasetQuery
from datacatalog.solr.solr_orm_entity import SolrEntity
from datacatalog.solr.solr_orm_fields import SolrField, SolrTextField

logger = logging.getLogger(__name__)


class StudyQuery(DatasetQuery):
    # The sort options that will be offered on the search page
    SORT_OPTIONS = ["title", "id"]
    # labels of the sort options that will be offered on the search page
    SORT_LABELS = ["title", "id"]
    # default sort option
    DEFAULT_SORT = 'title'
    # default sort order
    DEFAULT_SORT_ORDER = 'desc'


class Study(SolrEntity):
    """
    Study entity, subclass of SolrEntity
    """
    # specifies the list of compatibles connectors
    COMPATIBLE_CONNECTORS = ['Json']
    query_class = StudyQuery
    title = SolrField("title")
    summary = SolrTextField("summary")

    def __init__(self, title: str = None, entity_id: str = None) -> None:
        """
          Initialize a new Study instance with title and entity_id
          @param title: title of the Study
          @param entity_id:  id of the Study
          """
        super().__init__(entity_id)
        self.title = title

    @classmethod
    def plural_name(cls) -> str:
        """
        Plural form of the entity name for display
        @return: a string representing the plural version of the entity name
        """
        return 'studies'
