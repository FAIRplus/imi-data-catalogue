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
    datacatalog.models.dataset
    -------------------

   Module containing the Dataset entity


"""
import logging
from collections import defaultdict
from dataclasses import dataclass

from . import EntityWithSlugs
from .. import app, DEFAULT_USE_RESTRICTIONS_ICONS
from ..solr.solr_orm import SolrAutomaticQuery
from ..solr.solr_orm_entity import SolrEntity
from ..solr.solr_orm_fields import (
    SolrField,
    SolrDateTimeField,
    SolrFloatField,
    SolrJsonField,
    SolrBooleanField,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UseRestriction:
    use_restriction_note: str
    use_class: str
    use_class_label: str
    use_restriction_rule: str
    use_class_note: str

    @classmethod
    def from_dict(cls, source_dict):
        return cls(
            use_restriction_note=source_dict.get("use_restriction_note"),
            use_class=source_dict.get("use_class"),
            use_class_label=source_dict.get("use_class_label"),
            use_restriction_rule=source_dict.get("use_restriction_rule"),
            use_class_note=source_dict.get("use_class_note"),
        )


class Dataset(SolrEntity, EntityWithSlugs):
    """
    Subclass of SolrEntity that is used as default entity
    """

    # specifies the list of compatibles connectors
    COMPATIBLE_CONNECTORS = ["Ckan", "Limesurvey", "Geo", "Json", "Dats", "Daisy"]

    title = SolrField("title")
    data_standards = SolrField("data_standards", multivalued=True)
    data_types = SolrField("data_types", multivalued=True)
    dataset_created = SolrDateTimeField("dataset_created")
    dataset_modified = SolrDateTimeField("dataset_modified")
    file_formats = SolrField("file_formats", multivalued=True)
    version = SolrField("version", indexed=False)
    studies_metadata = SolrField("studies_metadata", multivalued=True)
    projects_metadata = SolrField("projects_metadata", multivalued=True)
    dataset_link_href = SolrField("dataset_link_href")
    dataset_link_label = SolrField("dataset_link_label")
    fair_assessment_link_pre = SolrField("fair_assessment_link_pre")
    fair_assessment_link_post = SolrField("fair_assessment_link_post")
    fair_score_representation_pre = SolrFloatField("fair_score_representation_pre")
    fair_score_representation_post = SolrFloatField("fair_score_representation_post")
    fair_score_content_pre = SolrFloatField("fair_score_content_pre")
    fair_score_content_post = SolrFloatField("fair_score_content_post")
    fair_score_hosting_pre = SolrFloatField("fair_score_hosting_pre")
    fair_score_hosting_post = SolrFloatField("fair_score_hosting_post")
    fair_score_overall_pre = SolrFloatField("fair_score_overall_pre")
    fair_score_overall_post = SolrFloatField("fair_score_overall_post")
    fair_indicators_href_pre = SolrField("fair_indicators_href_pre")
    fair_indicators_href_post = SolrField("fair_indicators_href_post")
    fair_indicators_pre = SolrField("fair_indicators_pre")
    fair_indicators_post = SolrField("fair_indicators_post")
    fair_evaluation = SolrField("fair_evaluation")
    e2e = SolrBooleanField("e2e")
    hosted = SolrBooleanField("hosted")
    use_restrictions = SolrJsonField("use_restrictions")
    storages = SolrJsonField("storages")
    use_restrictions_class_label = SolrField(
        "use_restrictions_class_label", multivalued=True
    )
    platform = SolrField("platform")
    query_class = SolrAutomaticQuery
    samples_number = SolrField("samples_number", indexed=False)
    treatment_category = SolrField("treatment_category", multivalued=True)
    treatment_name = SolrField("treatment_name", multivalued=True)
    disease = SolrField("disease", multivalued=True)
    samples_type = SolrField("samples_type", multivalued=True)
    dataset_contact = SolrField("dataset_contact")
    dataset_email = SolrField("dataset_email", indexed=False)
    dataset_affiliation = SolrField("dataset_affiliation")
    dataset_owner = SolrField("dataset_owner")

    def __init__(
        self,
        title: str = None,
        entity_id: str = None,
        e2e: bool = False,
        hosted: bool = False,
    ) -> None:
        """
        Initialize a new Dataset instance with title and entity_id
        @param title: title of the Dataset
        @param entity_id:  id of the Dataset
        """
        super().__init__(entity_id)
        self.title = title
        self.e2e = e2e
        self.hosted = hosted

    def set_computed_values(self):
        results = dict()  # using dict instead of set to preserve order
        for restriction in self.use_restrictions or []:
            use_restriction = UseRestriction.from_dict(restriction)
            results[use_restriction] = None
        self.use_restrictions_class_label = [u.use_class_label for u in results]
        self.use_restrictions = [r.__dict__ for r in results.keys()]

    @property
    def use_restrictions_by_type(self):
        results = defaultdict(list)
        mapping_icons = app.config.get(
            "USE_RESTRICTIONS_ICONS", DEFAULT_USE_RESTRICTIONS_ICONS
        )
        icons = {}
        for use_restriction in self.use_restrictions:
            if use_restriction.get("use_restriction_rule"):
                results[use_restriction.get("use_restriction_rule")].append(
                    use_restriction
                )
        for restriction_type in results:
            icons[restriction_type] = mapping_icons.get(restriction_type)
        return results, icons

    def get_keywords(self):
        keywords = [
            self.data_standards,
            self.file_formats,
            self.data_types,
            self.disease,
            self.treatment_category,
            self.treatment_name,
        ]
        if self.study_entity:
            keywords.append(self.study_entity.samples_type)
        return keywords
