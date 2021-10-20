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
    datacatalog.connector.daisy_connector
    -------------------

   Module containing the DaisyConnector class


"""
from typing import Type, Generator

import requests

from .entities_connector import ImportEntitiesConnector
from .. import app
from ..models.dataset import Dataset
from ..models.project import Project
from ..solr.solr_orm_entity import SolrEntity

__author__ = 'Valentin Grouès'

logger = app.logger


class DaisyConnector(ImportEntitiesConnector):
    """
    Import entities from DAISY API
    """

    def __init__(self, daisy_url: str, entity_class: Type[SolrEntity]) -> None:
        """
        Initialize a DaisyConnector instance configuring the daisy url and the entity class
        The build_all_entities methods will then create instances of entity_class
        @param daisy_url: the URL of the daisy API endpoint
        @param entity_class: the class to instantiate
        """
        self.entity_class = entity_class
        self.daisy_url = daisy_url

    def build_all_entities(self) -> Generator[SolrEntity, None, None]:
        """
        Yields instances of self.entity_class parsed from the json file self.json_file_path
        """

        def _build_dataset(item):
            MAPPING_FIELDS = {
                'name': 'title',
                'external_id': 'id',
            }
            dataset = Dataset()
            for field, attribute in MAPPING_FIELDS.items():
                setattr(dataset, attribute, item.get(field))
            data_types_set = set()
            dataset.use_restrictions = []
            for data_declaration in item['data_declarations']:
                data_types_set.update(data_declaration.get('data_types', []))
                dataset.use_restrictions.extend(data_declaration.get('use_restrictions', []))
            dataset.data_types = list(data_types_set)
            return dataset

        def _build_project(item):
            def map_contact(contact, project):
                project.role = contact.get('role')
                project.email = contact.get('email')
                project.first_name = contact.get('first_name')
                project.last_name = contact.get('last_name')
                project.affiliation = contact.get('affiliations', [None])[0]
                project.display_name = " ".join([project.first_name, project.last_name, f'({project.role})'])

            MAPPING_FIELDS = {
                'acronym': 'project_name',
                'name': 'title',
                'study_type': 'types',
                'end_date': 'end_date',
                'start_date': 'start_date',
                'description': 'description',
                'study_terms': 'keywords',
                'external_id': 'id',
                # 'acronym': 'id',
            }
            project = Project()

            for field, attribute in MAPPING_FIELDS.items():
                setattr(project, attribute, item.get(field))
            for contact in item.get('contacts', []):
                # we take the first values available
                if contact.get('role') == 'Principal_Investigator':
                    map_contact(contact, project)
                    break
            else:
                # we didn't find a principal investigator, we take the first contact
                if len(item.get('contacts', [])) > 0:
                    map_contact(item['contacts'][0], project)
            project.reference_publications = []
            for publication in item.get('publications', []):
                if publication.get('citation'):
                    project.reference_publications.append(publication['citation'])
            return project

        response = requests.get(self.daisy_url, verify=False)
        response_json = response.json()
        for item in response_json['items']:
            if self.entity_class == Dataset:
                yield _build_dataset(item)
            if self.entity_class == Project:
                yield _build_project(item)
