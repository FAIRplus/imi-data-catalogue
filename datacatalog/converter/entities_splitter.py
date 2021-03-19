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

import json
import logging
import random
from datetime import datetime
from math import isnan
from typing import TextIO

from datacatalog.models.dataset import Dataset
from datacatalog.models.project import Project
from datacatalog.models.study import Study
from datacatalog.solr.solr_orm_entity import DATETIME_FORMAT, DATETIME_FORMAT_NO_MICRO

logger = logging.getLogger(__name__)
LOREM = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
"""
PRESERVED_STUDY_ATTRIBUTES = [
    'age_range_lower_limit',
    'age_range_upper_limit',
    'age_unit',
    'bmi_range',
    'bmi_range_lower_limit',
    'body_system_or_organ_class',
    'category',
    'cohorts_description',
    'therapeutic_area_standards_disease',
    'treatment_name_standardized',
    'multi_center_study'
]
MAPPED_STUDY_ATTRIBUTES = {
    'study_primary_purpose': 'primary_purpose',
    'study_phase': 'phase',
    'study_type': 'types',
    'organism': 'organisms',
    'study_protocol_description': 'protocol_description'
}
MAPPED_PROJECT_ATTRIBUTES = {
    'project_name': 'title',
    'project_website': 'website'
}
MAPPED_DATASET_ATTRIBUTES = {
    'tags': 'keywords',
}

PRESERVED_PROJECT_ATTRIBUTES = [
]
JSON_HEADER = """
{
  "docs": [
"""
JSON_FOOTER = """
]
}
"""


def split_entities(records_file: TextIO, datasets_file: TextIO, studies_file: TextIO, projects_file: TextIO):
    records = json.load(records_file).get('docs')
    random_words = LOREM.split()
    if not records:
        return
    studies_file.write(JSON_HEADER)
    datasets_file.write(JSON_HEADER)
    projects_file.write(JSON_HEADER)
    for index, record in enumerate(records):
        dataset = Dataset()
        for key, value in record.items():
            value = prepare_value(key, value, dataset)
            key = MAPPED_DATASET_ATTRIBUTES.get(key, key)
            setattr(dataset, key, value)
        if 'pubmed' in dataset.title:
            continue
        study = Study()
        extract_entity(study, record, PRESERVED_STUDY_ATTRIBUTES, MAPPED_STUDY_ATTRIBUTES)
        study.title = f'Study of dataset {dataset.title}'
        study.datasets = [dataset.id]
        if not study.description:
            study.description = LOREM
        project = Project()
        project.studies = [study.id]
        extract_entity(project, record, PRESERVED_PROJECT_ATTRIBUTES, MAPPED_PROJECT_ATTRIBUTES)
        project.title = f'Project of dataset {dataset.title}'
        if not project.description:
            project.description = LOREM
        if not project.keywords:
            project.keywords = [random.choice(random_words) for _ in range(random.randint(1, 4))]
        if not project.start_date:
            project.start_date = datetime.date(datetime.now())
        json.dump(study.to_dict(add_prefix=False), studies_file, default=str)
        json.dump(project.to_dict(add_prefix=False), projects_file, default=str)
        json.dump(dataset.to_dict(add_prefix=False), datasets_file, default=str)
        if index != len(records) - 1:
            projects_file.write(',')
            studies_file.write(',')
            datasets_file.write(',')
    studies_file.write(JSON_FOOTER)
    datasets_file.write(JSON_FOOTER)
    projects_file.write(JSON_FOOTER)


def prepare_value(attribute, value, entity):
    if not value:
        return value
    if type(value) == float and isnan(value):
        return None
    try:
        field = entity._solr_fields[attribute]
    except KeyError:
        return value
    if field.type == 'date':
        try:
            value = datetime.strptime(value, DATETIME_FORMAT)
        except ValueError:
            value = datetime.strptime(value, DATETIME_FORMAT_NO_MICRO)
    return value


def extract_entity(entity, record, preserved_attributes, mapped_attributes):
    for attribute in preserved_attributes:
        value = record.get(attribute)
        value = prepare_value(attribute, value, entity)
        if value:
            setattr(entity, attribute, value)
    for former_attribute, new_attribute in mapped_attributes.items():
        value = record.get(former_attribute)
        value = prepare_value(new_attribute, value, entity)
        if value:
            setattr(entity, new_attribute, value)
