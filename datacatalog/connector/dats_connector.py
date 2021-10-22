# coding=utf-8

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
    datacatalog.connector.dats_connector
    -------------------

   Module containing the DATSConnector class


"""
import json
import os
from typing import Type, Generator

from jsonpath_ng import parse
from slugify import slugify

from .entities_connector import ImportEntitiesConnector
from .. import app
from ..models.dataset import Dataset
from ..models.project import Project
from ..models.study import Study
from ..solr.solr_orm_entity import SolrEntity

__author__ = 'Danielle Welter'

logger = app.logger


class DATSConnector(ImportEntitiesConnector):
    """
    Import entities directly from a DATS JSON file
    """

    def __init__(self, json_file_path: str, entity_class: Type[SolrEntity]) -> None:
        """
        Initialize a DATSConnector instance configuring the json file path and the entity class
        The build_all_entities methods will then create instances of entity_class from the json file json_file_path
        @param json_file_path: the path of json file containing the serialized entities
        @param entity_class: the class to instantiate
        """
        self.entity_class = entity_class
        self.json_file_path = json_file_path

    def build_all_entities(self) -> Generator[SolrEntity, None, None]:
        """
        Yields instances of self.entity_class parsed from the json file self.json_file_path
        """

        with os.scandir(self.json_file_path) as data_files:
            for data_file in data_files:
                with open(self.json_file_path + "/" + data_file.name, encoding='utf8') as json_file:
                    data = json.load(json_file)
                    if self.entity_class == Project:
                        new_project = Project()
                        yield self.build_project(data, new_project)
                    elif self.entity_class == Dataset:
                        if 'projectAssets' in data:
                            for asset in data['projectAssets']:
                                if asset['@type'] == 'Dataset':
                                    new_dataset = Dataset()
                                    yield self.build_dataset(asset, new_dataset)
                                elif asset['@type'] == 'Study' and 'output' in asset:
                                    for dataset_metadata in asset['output']:
                                        new_dataset = Dataset()
                                        yield self.build_dataset(dataset_metadata, new_dataset)
                    elif self.entity_class == Study:
                        if 'projectAssets' in data:
                            for study_metadata in data['projectAssets']:
                                if study_metadata['@type'] == 'Study':
                                    new_study = Study()
                                    yield self.build_study(study_metadata, new_study)
                    else:
                        logger.error("Entity type not recognised")

    @staticmethod
    def build_project(metadata, project):
        if 'identifier' in metadata:
            project.id = metadata['identifier']['identifier']
        else:
            logger.error("Project entity has no identifier")

        if 'title' in metadata:
            project.title = metadata['title']
        if 'description' in metadata:
            project.description = metadata['description']
        if 'types' in metadata:
            jsonpath_expr = parse('types[*].value')
            project.types = [match.value for match in jsonpath_expr.find(metadata)]

        if 'fundedBy' in metadata:
            if len(metadata['fundedBy']) == 1:
                project.funded_by = metadata['fundedBy'][0]['name']
            else:
                jsonpath_expr = parse('fundedBy[*].name')
                project.funded_by = ', '.join([match.value for match in jsonpath_expr.find(metadata)])

        if 'keywords' in metadata:
            jsonpath_expr = parse('keywords[*].value')
            project.keywords = [match.value for match in jsonpath_expr.find(metadata)]

        # TO DO: adjust for multiple project contacts
        if 'projectLeads' in metadata:
            project_lead = metadata['projectLeads'][0]
            if 'title' in project_lead:
                project.contact_title = project_lead['title']
            if 'firstName' in project_lead:
                project.first_name = project_lead['firstName']
            else:
                project.first_name = ''
            if 'lastName' in project_lead:
                project.last_name = project_lead['lastName']
            else:
                project.last_name = ''

            project.display_name = ' '.join([project.first_name, project.last_name])

            if 'email' in project_lead:
                project.email = project_lead['email']

            if 'affiliations' in project_lead:
                project.affiliation = project_lead['affiliations'][0]['name']

                if 'location' in project_lead['affiliations'][0] and 'postalAddress' in project_lead['affiliations'][0][
                    'location']:
                    project.business_address = project_lead['affiliations'][0]['location']['postalAddress']

            if 'roles' in project_lead:
                if len(project_lead['roles']) == 1:
                    project.role = project_lead['roles'][0]['value']
                else:
                    jsonpath_expr = parse('roles[*].value')
                    project.role = ', '.join([match.value for match in jsonpath_expr.find(metadata)])

            if 'phoneNumber' in project_lead:
                project.business_phone_number = project_lead['phoneNumber']

        if 'startDate' in metadata:
            project.start_date = metadata['startDate']['date']

        if 'endDate' in metadata:
            project.end_date = metadata['endDate']['date']

        if 'primaryPublications' in metadata:
            jsonpath_expr = parse('primaryPublications[*].identifier.identifier')
            project.reference_publications = [match.value for match in jsonpath_expr.find(metadata)]

        project.slugs = []
        if 'extraProperties' in metadata:
            for ep in metadata['extraProperties']:
                if ep['category'] == 'website':
                    project.website = ep['values'][0]['value']

                elif ep['category'] == 'projectAcronym':
                    project.project_name = ep['values'][0]['value']
                    project.slugs.append(slugify(project.project_name))
                elif ep['category'] == 'slugs':
                    project.slugs.extend([value.get('value') for value in ep.get('values', []) if value.get('value')])

        if 'projectAssets' in metadata:
            project.studies = []
            project.datasets = []
            for study in metadata['projectAssets']:
                if study['@type'] == 'Study' and 'identifier' in study:
                    project.studies.append(study['identifier']['identifier'])

                if 'output' in study:
                    for dataset in study['output']:
                        if dataset['@type'] == 'Dataset' and 'identifier' in dataset:
                            project.datasets.append(dataset['identifier']['identifier'])
                            if 'extraProperties' in dataset:
                                for ep in dataset['extraProperties']:
                                    if ep['category'] == 'fairEvaluation':
                                        if ep['values'][0]['value']:
                                            project.fair_evaluation = "FAIRplus Evaluation"

        return project

    @staticmethod
    def build_study(metadata, study):
        if 'identifier' in metadata:
            study.id = metadata['identifier']['identifier']
        else:
            logger.error("Study entity has no identifier")

        if 'name' in metadata:
            study.title = metadata['name']

        if 'description' in metadata:
            study.description = metadata['description']

        if 'types' in metadata:
            jsonpath_expr = parse('types[*].value')
            study.types = [match.value for match in jsonpath_expr.find(metadata)]

        # TO DO account for studies with >1 studyGroup
        if 'studyGroups' in metadata and len(metadata['studyGroups']) == 1:
            cohort = metadata['studyGroups'][0]
            if 'size' in cohort:
                study.size = cohort['size']

            if 'name' in cohort:
                study.cohorts_description = cohort['name']

            if 'extraProperties' in cohort:
                bmi_lower = ''
                bmi_upper = ''
                bmi_range = ''
                age_lower = ''
                age_upper = ''
                age_unit = ''
                age_range = ''
                for ep in cohort['extraProperties']:
                    if ep['category'] == 'BMI range lower limit':
                        bmi_lower = ep['values'][0]['value']
                    elif ep['category'] == 'BMI range upper limit':
                        bmi_upper = ep['values'][0]['value']
                    elif ep['category'] == 'BMI range':
                        bmi_range = ep['values'][0]['value']
                    elif ep['category'] == 'Age range lower limit':
                        age_lower = ep['values'][0]['value']
                    elif ep['category'] == 'Age range upper limit':
                        age_upper = ep['values'][0]['value']
                    elif ep['category'] == 'Age unit':
                        age_unit = ep['values'][0]['value']

                if bmi_lower != '' or bmi_upper != '':
                    bmi_range = bmi_lower + '-' + bmi_upper

                if bmi_range != '':
                    study.bmi_range = bmi_range

                if age_lower != '' or age_upper != '':
                    age_range = age_lower + '-' + age_upper + ' ' + age_unit

                if age_range != '':
                    study.age_range = age_range

        #     TO DO account for studies with >1 input material
        if 'input' in metadata and len(metadata['input']) == 1:
            input = metadata['input'][0]

            if 'types' in input:
                jsonpath_expr = parse('types[*].value')
                study.samples_source = [match.value for match in jsonpath_expr.find(input)]

            if 'taxonomy' in input:
                jsonpath_expr = parse('taxonomy[*].name')
                study.organisms = [match.value for match in jsonpath_expr.find(input)]

            if 'bearerOfDisease' in input:
                jsonpath_expr = parse('bearerOfDisease[*].name')
                study.disease = [match.value for match in jsonpath_expr.find(input)]

            if 'derivesFrom' in input:
                jsonpath_expr = parse('derivesFrom[*].name')
                study.samples_type = [match.value for match in jsonpath_expr.find(input)]

        if 'output' in metadata:
            study.datasets = []

            for dataset in metadata['output']:
                if dataset['@type'] == "Dataset" and 'identifier' in dataset:
                    study.datasets.append(dataset['identifier']['identifier'])

                    if 'extraProperties' in dataset:
                        for ep in dataset['extraProperties']:
                            if ep['category'] == 'fairEvaluation':
                                if ep['values'][0]['value']:
                                    study.fair_evaluation = "FAIRplus Evaluation"

        if 'extraProperties' in metadata:
            for ep in metadata['extraProperties']:
                if ep['category'] == 'informedConsent':
                    if ep['values'][0]['value'] == 'true':
                        study.informed_consent = True
                    elif ep['values'][0]['value'] == 'false':
                        study.informed_consent = False

                elif ep['category'] == 'multiCenter':
                    if ep['values'][0]['value'] == 'true':
                        study.multi_center_study = True
                    elif ep['values'][0]['value'] == 'false':
                        study.multi_center_study = False

                elif ep['category'] == 'primaryPurpose':
                    study.primary_purpose = ep['values'][0]['value']
                elif ep['category'] == 'slugs':
                    study.slugs = [value.get('value') for value in ep.get('values', []) if value.get('value')]

        return study

    @staticmethod
    def build_dataset(metadata, dataset):
        if 'identifier' in metadata:
            dataset.id = metadata['identifier']['identifier']
        else:
            logger.error("Dataset entity has no identifier")

        if 'title' in metadata:
            dataset.title = metadata['title']

        if 'types' in metadata:
            jsonpath_expr = parse('types[*].method.value')
            dataset.data_types = [match.value for match in jsonpath_expr.find(metadata)]

            jsonpath_expr = parse('types[*].platform.value')
            dataset.platform = [match.value for match in jsonpath_expr.find(metadata)]

        if 'isAbout' in metadata:
            treatment = []
            treatment_category = []
            disease = []
            sampleType = []
            for entity in metadata['isAbout']:
                if entity['@type'] == 'MolecularEntity':
                    treatment.append(entity['name'])

                    if 'roles' in entity:
                        for role in entity['roles']:
                            if role['value'] not in treatment_category:
                                treatment_category.append(role['value'])

                elif entity['@type'] == 'Disease':
                    disease.append(entity['name'])

                elif entity['@type'] == 'AnatomicalPart':
                    sampleType.append(entity['name'])

                elif entity['@type'] == 'CategoryValuesPair':
                    if entity['category'] == 'Experiment category':
                        for val in entity['values']:
                            if val['value'] not in treatment_category:
                                treatment_category.append(val['value'])
                    if entity['category'] == 'Experiment name':
                        for val in entity['values']:
                            if val['value'] not in treatment:
                                treatment.append(val['value'])

            dataset.treatment_name = ', '.join(treatment)
            dataset.treatment_category = treatment_category
            dataset.disease = disease
            dataset.samples_type = sampleType

        if 'extraProperties' in metadata:
            for ep in metadata['extraProperties']:
                if ep['category'] == 'number of samples':
                    dataset.samples_number = ep['values'][0]['value']

                elif ep['category'] == 'fairAssessmentDetails':
                    dataset.fair_assessment_details = ep['values'][0]['value']

                elif ep['category'] == 'fairAssessmentLink':
                    dataset.fair_assessment_details_link = ep['values'][0]['value']

                elif ep['category'] == 'fairIndicators':
                    dataset.fair_indicators = ep['values'][0]['value']

                elif ep['category'] == 'fairIndicatorsHref':
                    dataset.fair_indicators_href = ep['values'][0]['value']

                elif ep['category'] == 'fairScoreMandatory':
                    dataset.fair_score_mandatory_indicators = ep['values'][0]['value']

                elif ep['category'] == 'fairScoreRecommended':
                    dataset.fair_score_recommended_indicators = ep['values'][0]['value']

                elif ep['category'] == 'fairScoreOverall':
                    dataset.fair_score_overall = ep['values'][0]['value']

                elif ep['category'] == 'fairEvaluation':
                    if ep['values'][0]['value']:
                        dataset.fair_evaluation = "FAIRplus Evaluation"
                elif ep['category'] == 'slugs':
                    dataset.slugs = [value.get('value') for value in ep.get('values', []) if value.get('value')]

        # TO DO deal with cases where there's more than one distribution object
        if 'distributions' in metadata and len(metadata['distributions']) == 1:
            distro = metadata['distributions'][0]

            if 'access' in distro:
                if 'accessURL' in distro['access']:
                    dataset.dataset_link_href = distro['access']['accessURL']

                if 'landingPage' in distro['access']:
                    dataset.dataset_link_label = distro['access']['landingPage']

            if 'version' in distro:
                dataset.version = distro['version']

            if 'conformsTo' in distro:
                jsonpath_expr = parse('conformsTo[*].name')
                dataset.data_standards = [match.value for match in jsonpath_expr.find(distro)]

            if 'dates' in distro:
                for date in distro['dates']:
                    if date['type']['value'] == 'creation date':
                        dataset.dataset_created = date['date']
                    elif date['type']['value'] == 'last update date':
                        dataset.dataset_modified = date['date']

        return dataset
