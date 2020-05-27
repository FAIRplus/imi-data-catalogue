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
    datacatalog.importer.connector.ckan_connector
    -------------------

   Module containing the CKANConnector class


"""
import datetime
from typing import Generator

from ckanapi import RemoteCKAN

from .entities_connector import EntitiesConnector
from ... import app
from ...models.dataset import Dataset

CKAN_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

__author__ = 'Valentin Grouès'

logger = app.logger


class CKANConnector(EntitiesConnector):
    """
    The CKAN connector class implements the EntitiesConnector methods to build Dataset using the REST API of a CKAN
    instance
    """
    # MAPPING between CKAN and Dataset fields
    DIRECT_MAPPING = {
        "Affiliation": Dataset.affiliation,
        "Therapeutic Area Standards  Disease Area  if applicable": Dataset.therapeutic_area_standards_disease,
        "Organism": Dataset.organism,
        "PubMed": Dataset.pubmed_link,
        "Type of Samples": Dataset.samples_type,
        "Number of Samples": Dataset.samples_number,
        "Disease": Dataset.disease,
        "Contact Address": Dataset.business_address,
        "Platform": Dataset.platform,
        "Indication": Dataset.indication,
        "Type of Data": Dataset.data_type,
        "Description of Cohorts  if multi cohorts": Dataset.cohorts_description,
        'Dataset Title': Dataset.title,
        'Email': Dataset.contact_email,
        'Study Type': Dataset.study_type,
        'Funding': Dataset.funding,
        'Version': Dataset.version,
        'Primary Purpose': Dataset.primary_purpose,
        'Secondary Analysis': Dataset.secondary_analysis,
        'Informed Consent': Dataset.informed_consent,
        'Standardized Treatment Name': Dataset.treatment_name_standardized,
        'Study Classification': Dataset.study_classification,
        'First Name': Dataset.contact_first_name,
        'Multi center Study': Dataset.multi_center_study,
        'Type of Samples Collected': Dataset.samples_type,
        "Name of Treatment": Dataset.treatment_name,
        "Dose Description": Dataset.dose_description,
        "Study Phase": Dataset.study_phase,
        "Business Phone Number": Dataset.business_phone_number,
        "Study Protocol Description": Dataset.study_protocol_description,
        "BMI Range": Dataset.bmi_range,
        "Project Website": Dataset.project_website,
        "Last Name": Dataset.contact_last_name,
        "Intervention Model": Dataset.intervention_model,
        "Business Address": Dataset.business_address,
        "Detail Subject Composition": Dataset.subjects_composition_details,
        "Data Standards Implemented": Dataset.data_standards,
        "Body System or Organ Class": Dataset.body_system_or_organ_class,
        "Age Unit  of the above range": Dataset.age_unit,
        "Total Number of  Human  Subjects": Dataset.total_number_subjects,
        "Number of Samples Collected": Dataset.samples_number,
        "Age Range  Upper Llimit  of Study Participants": Dataset.age_range_upper_limit,
        "Age Range  Low Limit  of Study Participants": Dataset.age_range_lower_limit,
        "Number of Subjects in Each Cohorts  if multi cohorts": Dataset.subjects_number_per_cohort,
        "Reference Publications": Dataset.reference_publications,
        "Total Number of Subjects": Dataset.total_number_subjects,
        "Category": Dataset.category,
        "Planned Arm  Description of Sub cohorts": Dataset.planned_arm,
        "Date of Creation of the dataset": Dataset.dataset_created,
        "Date of the Last Update of the dataset": Dataset.dataset_modified
    }
    # CKAN fields to skip
    TO_SKIP = ["Email Address", "Project Name"]

    def __init__(self, ckan_url: str) -> None:
        """
        Initialize a CKANConnector instance configuring the CKAN instance URL
        @param ckan_url: hostname and port of the CKAN instance
        """
        self.ckan = RemoteCKAN(ckan_url)

    def build_all_entities(self) -> Generator[Dataset, None, None]:
        """
        Retrieves all datasets from CKAN, creates corresponding Dataset instance and yields them
        """
        datasets_names = self.ckan.action.package_list()
        for dataset_name in datasets_names:
            package = self.ckan.action.package_show(id=dataset_name)
            yield self.create_dataset(package)

    def create_dataset(self, package: dict) -> Dataset:
        """
        Convert a CKAN package to a Dataset instance
        @param package: a dict containing the CKAN field of a package
        @return: a Dataset instance initialized with the data from the CKAN package
        """
        project_name = package.get('title', None)
        dataset = Dataset(None, package.get('id', None))
        dataset.project_name = project_name
        extras_with_values = {extra['key'].strip(): extra['value'] for extra in package.get('extras') if extra['value']}
        self.map_fields(dataset, extras_with_values)
        if dataset.title is None:
            dataset.title = project_name
        dataset.name = package.get('name', None)
        dataset.notes = package.get('notes', None)
        dataset.tags = [tag['display_name'] for tag in package.get('tags', [])]
        dataset.groups = [group['display_name'] for group in package.get('groups', [])]
        dataset.url = package.get('url', None)
        created_string = package.get('metadata_created', None)
        if created_string is not None:
            created_datetime = datetime.datetime.strptime(created_string, CKAN_DATE_FORMAT)
        dataset.created = created_datetime
        modified_string = package.get('metadata_modified', None)
        if modified_string is not None:
            modified_datetime = datetime.datetime.strptime(modified_string, CKAN_DATE_FORMAT)
        dataset.modified = modified_datetime
        return dataset
