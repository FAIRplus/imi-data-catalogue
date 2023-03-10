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

from flask import url_for

from datacatalog.solr.solr_orm import SolrAutomaticQuery
from datacatalog.solr.solr_orm_entity import SolrEntity
from datacatalog.solr.solr_orm_fields import (
    SolrBooleanField,
    SolrField,
    SolrTextField,
    SolrForeignKeyField,
    SolrIntField,
)
from . import EntityWithSlugs

logger = logging.getLogger(__name__)


class Study(SolrEntity, EntityWithSlugs):
    """
    Study entity, subclass of SolrEntity
    """

    # specifies the list of compatibles connectors
    COMPATIBLE_CONNECTORS = ["Json", "Dats", "Geo"]
    query_class = SolrAutomaticQuery
    # age_range = SolrField("age_range")
    # bmi_range = SolrField("bmi_range", indexed=False)

    cohort_characteristics = SolrField("cohort_characteristics", multivalued=True)

    cohorts_description = SolrField("cohorts_description")
    datasets = SolrForeignKeyField(
        "datasets",
        entity_name="dataset",
        multivalued=True,
        reversed_by="study",
        reversed_multiple=False,
    )
    datasets_metadata = SolrField("datasets_metadata", multivalued=True)
    projects_metadata = SolrField("projects_metadata", multivalued=True)

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
    study_characteristics = SolrField("study_characteristics", multivalued=True)

    fair_evaluation = SolrField("fair_evaluation")

    def __init__(self, title: str = None, entity_id: str = None) -> None:
        """
        Initialize a new Study instance with title and entity_id
        @param title: title of the Study
        @param entity_id:  id of the Study
        """
        super().__init__(entity_id)
        self.title = title

    def get_author(self):
        for dataset in self.datasets_entities:
            if dataset.dataset_contact:
                return {
                    "type": "Person",
                    "name": dataset.dataset_contact,
                }
            elif dataset.dataset_owner:
                return {
                    "type": "Organisation",
                    "name": dataset.dataset_owner,
                }

        parent = self.project_entity
        if parent and parent.contacts:
            return {
                "type": "Person",
                "name": parent.contacts[0].full_name,
            }
        else:
            return None

    def get_published_date(self):
        first_date = None
        for dataset in self.datasets_entities:
            if dataset.dataset_created and (
                first_date is None or first_date > dataset.dataset_created
            ):
                first_date = dataset.dataset_created

        return first_date

    def get_keywords(self):
        return [self.disease, self.organisms, self.samples_source, self.samples_type]

    def get_related_studies_urls(self):
        parent = self.project_entity
        related = (
            [
                url_for(
                    "entity_details",
                    entity_name="study",
                    entity_id=study_id,
                    _external=True,
                )
                for study_id in parent.studies
                if study_id != self.id
            ]
            if parent
            else []
        )

        return related

    @classmethod
    def plural_name(cls) -> str:
        """
        Plural form of the entity name for display
        @return: a string representing the plural version of the entity name
        """
        return "studies"
