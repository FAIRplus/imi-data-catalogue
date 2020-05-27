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

from . import DatasetQuery
from ..solr.solr_orm_entity import SolrEntity
from ..solr.solr_orm_fields import SolrField, SolrDateTimeField, SolrFloatField, SolrIntField, SolrBooleanField

logger = logging.getLogger(__name__)


class Dataset(SolrEntity):
    """
    Subclass of SolrEntity that is used as default entity
    """
    # specifies the list of compatibles connectors
    COMPATIBLE_CONNECTORS = ['Ckan', 'Limesurvey', 'Geo', 'Json']
    title = SolrField("title")
    name = SolrField("name")
    notes = SolrField("notes")
    url = SolrField("url")
    tags = SolrField("tags", multivalued=True)
    groups = SolrField("groups", multivalued=True)
    query_class = DatasetQuery

    affiliation = SolrField("affiliation")
    age_unit = SolrField("age_unit", indexed=False)
    age_range_lower_limit = SolrIntField("age_range_lower_limit", indexed=False)
    age_range_upper_limit = SolrIntField("age_range_upper_limit", indexed=False)
    body_system_or_organ_class = SolrField("body_system_or_organ_class")
    bmi_range = SolrField("bmi_range", indexed=False)
    bmi_range_lower_limit = SolrFloatField("bmi_range_lower_limit")
    bmi_range_upper_limit = SolrFloatField("bmi_range_upper_limit")
    business_phone_number = SolrField("business_phone_number", indexed=False)
    business_fax_number = SolrField("business_fax_number", indexed=False)
    business_address = SolrField("business_address", indexed=False)
    category = SolrField("category", indexed=False)
    contact_email = SolrField("contact_email", indexed=False)
    contact_first_name = SolrField("contact_first_name")
    contact_last_name = SolrField("contact_last_name")
    contact_names = SolrField("contact_names", multivalued=True)
    cohorts_description = SolrField("cohorts_description")
    data_standards = SolrField("data_standards")
    data_type = SolrField("data_type")
    dataset_created = SolrDateTimeField("dataset_created")
    dataset_modified = SolrDateTimeField("dataset_modified")
    disease = SolrField("disease")
    dose_description = SolrField("dose_description")
    funding = SolrField("funding")
    indication = SolrField("indication")
    intervention_model = SolrField("intervention_model")
    informed_consent = SolrBooleanField("informed_consent")
    multi_center_study = SolrBooleanField("multi_center_study")
    organism = SolrField("organism")
    primary_purpose = SolrField("primary_purpose")
    platform = SolrField("platform")
    project_name = SolrField("project_name")
    project_website = SolrField("project_website", indexed=False)
    pubmed_link = SolrField("pubmed_link", indexed=False)
    reference_publications = SolrField("reference_publications", indexed=False, multivalued=True)
    samples_details = SolrField("samples_details")
    samples_number = SolrField("samples_number", indexed=False)
    samples_type = SolrField("samples_type", multivalued=True)
    secondary_analysis = SolrField("secondary_analysis")
    study_phase = SolrField("study_phase")
    study_classification = SolrField("study_classification")
    study_protocol_description = SolrField("study_protocol_description")
    study_type = SolrField("study_type")
    study_type_comment = SolrField("study_type_comment")
    treatment_category = SolrField("treatment_category")
    planned_arm = SolrField("planned_arm")
    subjects_composition_details = SolrField("subjects_composition_details")
    subjects_number_per_cohort = SolrField("subjects_number_per_cohort", indexed=False)
    therapeutic_area_standards_disease = SolrField("therapeutic_area_standards_disease")
    treatment_name = SolrField("treatment_name")
    treatment_name_standardized = SolrField("treatment_name_standardized")
    total_number_subjects = SolrIntField("total_number_subjects")
    total_number_human_subjects = SolrIntField("total_number_human_subjects")
    total_number_non_human_subjects = SolrIntField("total_number_non_human_subjects")
    version = SolrField("version", indexed=False)
    findable = SolrIntField("findable")
    accessible = SolrIntField("accessible")
    interoperable = SolrIntField("interoperable")
    reusable = SolrIntField("reusable")
    open_access_link = SolrField("open_access_link")
    is_fairplus_evaluated = SolrBooleanField("is_fairplus_evaluated")
    fair_indicators = SolrField("fair_indicators")
    fair_indicators_href = SolrField("fair_indicators_href")
    fair_score_overall = SolrFloatField("fair_score_overall")
    fair_score_mandatory_indicators = SolrFloatField("fair_score_mandatory_indicators")
    fair_score_recommended_indicators = SolrFloatField("fair_score_recommended_indicators")
    fair_assessment_details = SolrField('fair_assessment_details')
    fair_assessment_details_link = SolrField('fair_assessment_details_link')
    dataset_link_label = SolrField("dataset_link_label")
    dataset_link_href = SolrField("dataset_link_href")

    def __init__(self, title: str = None, entity_id: str = None) -> None:
        """
        Initialize a new Dataset instance with title and entity_id
        @param title: title of the Dataset
        @param entity_id:  id of the Dataset
        """
        super().__init__(entity_id)
        self.title = title
