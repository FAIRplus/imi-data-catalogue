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
    datacatalog.connector.limesurvey_connector
    -------------------

   Module containing the LimesurveyConnector class


"""
import base64
import json
from typing import Generator

from .entities_connector import ImportEntitiesConnector
from .limesurveyrc2api import LimeSurveyRemoteControl2API, CompletionStatus, ResponsesType
from .. import app
from ..models.dataset import Dataset

logger = app.logger


class LimesurveyConnector(ImportEntitiesConnector):
    """
    EntitiesConnector subclass to import entities from a Limesurvey instance
    """
    DIRECT_MAPPING = {
        # 'AgeRange[SQ001]': Dataset.age_range_lower_limit,
        # 'AgeRange[SQ002]': Dataset.age_range_upper_limit,
        # 'AgeUnit': Dataset.age_unit,
        # "address": Dataset.business_address,
        # "affiliation": Dataset.affiliation,
        # 'BMIRange[SQ001]': Dataset.bmi_range_lower_limit,
        # 'BMIRange[SQ002]': Dataset.bmi_range_upper_limit,
        # 'BodySystemOrganClass': Dataset.body_system_or_organ_class,
        # "datasettitle": Dataset.title,
        # "datastandard": Dataset.data_standards,
        # "datecreate": Dataset.dataset_created,
        # "dateupdate": Dataset.dataset_modified,
        # "DetailSamples": Dataset.samples_details,
        # "DoseDescription": Dataset.dose_description,
        # "dscrpcohort": Dataset.cohorts_description,
        # 'disease': Dataset.disease,
        # 'email': Dataset.contact_email,
        # 'fax': Dataset.business_fax_number,
        # "firstname": Dataset.contact_first_name,
        # 'InterventionModel': Dataset.intervention_model,
        # 'Indication': Dataset.indication,
        # 'InformedConsent': Dataset.informed_consent,
        # "lastname": Dataset.contact_last_name,
        # "multicenter": Dataset.multi_center_study,
        # 'NameOfTreatment': Dataset.treatment_name,
        # 'NumHumSubj': Dataset.total_number_human_subjects,
        # 'NumNonHumSubj': Dataset.total_number_non_human_subjects,
        # 'NumSubjEachCohort': Dataset.subjects_number_per_cohort,
        # 'NumSample': Dataset.samples_number,
        # 'Organism[SQ001]': Dataset.organism,
        # 'PlannedArm': Dataset.planned_arm,
        # 'PrimaryPurpose': Dataset.primary_purpose,
        # "protocol": Dataset.study_protocol_description,
        # "phone": Dataset.business_phone_number,
        # 'refpub': Dataset.reference_publications,
        # 'SecondaryAnalysis[SQ001]': Dataset.secondary_analysis,
        # 'StandardizedTreatme': Dataset.treatment_name_standardized,
        # "StudyClassification": Dataset.study_classification,
        # 'StudyPhase[SQ001]': Dataset.study_phase,
        # 'SubjectCompo': Dataset.subjects_composition_details,
        # 'studytype': Dataset.study_type_comment,
        # "studytype[comment]": Dataset.study_type_comment,
        # "TypeSample[SQ009]": Dataset.samples_type,
        # "TreatmentCategory": Dataset.treatment_category,
        # 'version': Dataset.version,
        # "website": Dataset.project_website
    }
    TO_SKIP = ["id"]

    def __init__(self, limesurvey_url: str, username: str, password: str, survey_id: str) -> None:
        """
        Initialize a LimesurveyConnector instance with the limesurvey connection details and survey id
        @param limesurvey_url: the hostname and port of the Limesurvey installation
        @param username: Limesurvey username
        @param password:  Limesurvey password
        @param survey_id: Limesurvey survey id
        """
        self.survey_id = survey_id
        self.limesurvey = self.api = LimeSurveyRemoteControl2API(limesurvey_url)
        self.username = username
        self.password = password

    def build_all_entities(self) -> Generator[Dataset, None, None]:
        """
        Yields Dataset instances created by querying Limesurvey API
        """
        session = self.limesurvey.sessions.get_session_key(
            self.username, self.password)
        session_key = session.get('result')
        responses = self.limesurvey.responses.list_responses(
            session_key, self.survey_id, 'json', CompletionStatus.complete, responses_type=ResponsesType.long)
        base64_encoded_response = responses['result']
        decoded_response = base64.b64decode(base64_encoded_response).decode('utf-8')
        json_response = json.loads(decoded_response)
        responses_list = json_response.get('responses')
        responses_list_dict = {response_id: response for entry_dict in responses_list for response_id, response in
                               entry_dict.items()}
        for response in responses_list_dict.values():
            yield self.create_dataset(response)

    def create_dataset(self, response: dict) -> Dataset:
        """
        Creates a Dataset from a dict containing metadata from limesurvey
        @param response: dict containing metadata from limesurvey
        @return: a Dataset instance
        """
        dataset_id = response.get('id', None)
        if dataset_id is not None:
            dataset_id = "limesurvey_{}".format(dataset_id)
        dataset = Dataset(entity_id=dataset_id)
        self.map_fields(dataset, response)
        return dataset
