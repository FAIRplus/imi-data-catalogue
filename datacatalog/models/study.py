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

from datacatalog.solr.solr_orm import SolrAutomaticQuery
from datacatalog.solr.solr_orm_entity import SolrEntity
from datacatalog.solr.solr_orm_fields import SolrBooleanField, SolrField, SolrTextField, SolrForeignKeyField, \
    SolrIntField
from . import EntityWithSlugs

logger = logging.getLogger(__name__)


class Study(SolrEntity, EntityWithSlugs):
    """
    Study entity, subclass of SolrEntity
    """
    # specifies the list of compatibles connectors
    COMPATIBLE_CONNECTORS = ['Json', 'Dats', 'Geo']
    query_class = SolrAutomaticQuery
    age_range = SolrField("age_range")
    bmi_range = SolrField("bmi_range", indexed=False)

    cohorts_description = SolrField("cohorts_description")
    datasets = SolrForeignKeyField("datasets", entity_name="dataset", multivalued=True, reversed_by='study',
                                   reversed_multiple=False)
    description = SolrTextField("description")
    disease = SolrField("disease", multivalued=True)
    informed_consent = SolrBooleanField("informed_consent")
    multi_center_study = SolrBooleanField("multi_center_study")
    organisms = SolrField("organisms", multivalued=True)
    primary_purpose = SolrField("primary_purpose")
    samples_source = SolrField("samples_source", multivalued=True)
    samples_type = SolrField("samples_type", multivalued=True)
    size = SolrIntField("size")
    title = SolrField("title")
    types = SolrField("types", multivalued=True)

    fair_evaluation = SolrField("fair_evaluation")

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
