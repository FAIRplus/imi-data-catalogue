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
    datacatalog.models.project
    -------------------

   Module containing the Project entity

@deprecated - fields moved to Project entity


"""
import logging

from . import EntityWithSlugs
from ..solr.solr_orm import SolrAutomaticQuery
from ..solr.solr_orm_entity import SolrEntity
from ..solr.solr_orm_fields import SolrField, SolrTextField, SolrForeignKeyField, SolrDateTimeField, SolrBooleanField

logger = logging.getLogger(__name__)


class Project(SolrEntity, EntityWithSlugs):
    """
    Project entity, subclass of SolrEntity
    """
    # specifies the list of compatibles connectors
    COMPATIBLE_CONNECTORS = ['Json', 'Dats', 'Geo', 'Daisy']
    query_class = SolrAutomaticQuery
    affiliation = SolrField("affiliation")
    business_address = SolrField("business_address", indexed=False)
    business_fax_number = SolrField("business_fax_number", indexed=False)
    business_phone_number = SolrField("business_phone_number", indexed=False)
    datasets = SolrForeignKeyField("datasets", entity_name="dataset", multivalued=True, reversed_by='project',
                                   reversed_multiple=False)
    description = SolrTextField("description")
    display_name = SolrField("display_name")
    email = SolrField("contact_email", indexed=False)
    end_date = SolrDateTimeField("end_date")
    contact_title = SolrField("contact_title", indexed=False)
    first_name = SolrField("contact_first_name")
    funded_by = SolrField("funded_by")
    keywords = SolrField("keywords", multivalued=True)
    last_name = SolrField("contact_last_name")
    project_name = SolrField("project_name")
    reference_publications = SolrField("reference_publications", indexed=False, multivalued=True)
    role = SolrField("role", multivalued=True)
    start_date = SolrDateTimeField("start_date")
    studies = SolrForeignKeyField("studies", entity_name="study", multivalued=True, reversed_by='project',
                                  reversed_multiple=False)
    title = SolrField("title")
    types = SolrField("types", multivalued=True)
    website = SolrField("website", indexed=False)

    fair_evaluation = SolrField("fair_evaluation")

    def __init__(self, title: str = None, entity_id: str = None) -> None:
        """
       Initialize a new Project instance with title and entity_id
       @param title: title of the Project
       @param entity_id:  id of the Project
       """
        super().__init__(entity_id)
        self.title = title
