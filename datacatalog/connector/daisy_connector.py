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
import json
import logging
from json import JSONDecodeError
from typing import Type, Generator

import requests

from .dats_connector import DATSConnector
from .entities_connector import ImportEntitiesConnector
from ..models.contact import Contact
from ..models.dataset import Dataset
from ..models.project import Project
from ..models.study import Study
from ..solr.solr_orm_entity import SolrEntity

__author__ = "Valentin Grouès"

logger = logging.getLogger(__name__)


class DaisyConnector(ImportEntitiesConnector):
    """
    Import entities from DAISY API
    """

    def __init__(
        self, daisy_url: str, entity_class: Type[SolrEntity], verify_ssl: bool = True
    ) -> None:
        """
        Initialize a DaisyConnector instance configuring the daisy url and the entity class
        The build_all_entities methods will then create instances of entity_class
        @param daisy_url: the URL of the daisy API endpoint
        @param entity_class: the class to instantiate
        @param verify_ssl: set to False to  skip ssl certificate verification
        """
        logger.info(
            "Initializing Daisy connector for %s with URL %s",
            entity_class.__name__,
            daisy_url,
        )
        self.entity_class = entity_class
        self.daisy_url = daisy_url
        self.dats_connector = DATSConnector("", entity_class)
        self.verify_ssl = verify_ssl

    def build_all_entities(self) -> Generator[SolrEntity, None, None]:
        """
        Yields instances of self.entity_class parsed from the daisy API
        """

        def _build_dataset(item):
            logger.debug("building a dataset instance")
            MAPPING_FIELDS = {
                "name": "title",
                "external_id": "id",
            }
            dataset = Dataset()
            # we enable the e2e flow for all daisy datasets
            dataset.e2e = True
            dataset.hosted = True
            if "metadata" in item:
                try:
                    metadata = json.loads(item["metadata"])
                    self.dats_connector.build_dataset(
                        metadata, dataset, id_required=False
                    )
                    dataset.former_ids = [dataset.id]
                except JSONDecodeError as e:
                    logger.error("invalid json", exc_info=e)
            for field, attribute in MAPPING_FIELDS.items():
                setattr(dataset, attribute, item.get(field))
            logger.debug("dataset title is %s", dataset.title)
            data_types_set = set()
            dataset.use_restrictions = []
            for data_declaration in item["data_declarations"]:
                data_types_set.update(data_declaration.get("data_types", []))
                dataset.use_restrictions.extend(
                    data_declaration.get("use_restrictions", [])
                )
            dataset.storages = []
            for storage in item.get("storages", []):
                dataset.storages.append(
                    {
                        "location": storage.get("location"),
                        "platform": storage.get("platform"),
                    }
                )
            dataset.data_types = list(data_types_set)
            project_external_id = item.get("project_external_id")
            project = Project.query.get(project_external_id)
            if project is None:
                logger.warning(
                    "project %s not found for dataset %s",
                    project_external_id,
                    dataset.id,
                )
            else:
                if project.studies_entities:
                    # FIXME, currently supports only projects with a single study
                    logger.debug("linking dataset to study")
                    study = project.studies_entities[0]
                    dataset.study = study.id
                else:
                    logger.debug("linking dataset to project")
                    dataset.project = project_external_id
            return dataset

        def _build_project(item):
            logger.debug("building project")

            def map_contact(contact, project):
                (
                    email,
                    first_name,
                    last_name,
                    affiliation,
                    full_name,
                    business_address,
                ) = (None, None, None, None, None, None)
                roles = []
                if contact["first_name"]:
                    first_name = contact["first_name"]
                if contact["last_name"]:
                    last_name = contact["last_name"]
                if len(contact["affiliations"]) > 0:
                    affiliation = contact["affiliations"][0]
                    business_address = contact["affiliations"][0]
                if contact["email"]:
                    email = contact["email"]
                if contact["role"]:
                    roles.append(contact["role"])
                if first_name is not None or last_name is not None:
                    full_name = (first_name, last_name)
                else:
                    full_name = "-"

                _contact = Contact(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    affiliation=affiliation,
                    business_address=business_address,
                    full_name=" ".join(full_name),
                    roles=roles,
                )
                project.contacts.append(_contact)

            MAPPING_FIELDS = {
                "acronym": "project_name",
                "name": "title",
                "study_type": "types",
                "description": "description",
                "study_terms": "keywords",
                "external_id": "id",
                # 'acronym': 'id',
            }
            project = Project()
            if "metadata" in item:
                try:
                    metadata = json.loads(item["metadata"])
                    self.dats_connector.build_project(
                        metadata, project, id_required=False
                    )
                    project.former_ids = [project.id]
                    self.dats_connector_studies = DATSConnector("", Study)
                    for (
                        study
                    ) in self.dats_connector_studies.build_all_entities_for_dict(
                        metadata
                    ):
                        yield study
                except JSONDecodeError as e:
                    logger.error("invalid json", exc_info=e)
            for field, attribute in MAPPING_FIELDS.items():
                value = item.get(field)
                if value is not None and value != "":
                    setattr(project, attribute, value)
            logger.debug("project title is %s", project.title)
            if item.get("contacts"):
                project.contacts = []
                for contact in item.get("contacts", []):
                    map_contact(contact, project)
            project.reference_publications = []
            for publication in item.get("publications", []):
                if publication.get("citation"):
                    project.reference_publications.append(publication["citation"])
            yield project

        logger.info("Calling daisy API")
        response = requests.get(self.daisy_url, verify=self.verify_ssl)
        response_json = response.json()
        logger.info("Success")
        items = response_json["items"]
        logger.info("%d items found, parsing and importing", len(items))
        for item in items:
            if self.entity_class == Dataset:
                yield _build_dataset(item)
            if self.entity_class == Project:
                for entity in _build_project(item):
                    yield entity
