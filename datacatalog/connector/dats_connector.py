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
import logging
import os
from typing import Type, Generator
import re

from jsonpath_ng import parse
from slugify import slugify

from .entities_connector import ImportEntitiesConnector
from .. import app
from ..models.dataset import Dataset
from ..models.project import Project
from ..models.study import Study
from ..models.contact import Contact
from ..solr.solr_orm_entity import SolrEntity

__author__ = "Danielle Welter"

logger = logging.getLogger(__name__)

HOSTED_AT_INSTITUTION = app.config.get("HOSTED_STRING", "hosted")


class DATSConnector(ImportEntitiesConnector):
    """
    Import entities directly from a DATS JSON file
    """

    def __init__(self, json_folder_path: str, entity_class: Type[SolrEntity]) -> None:
        """
        Initialize a DATSConnector instance configuring the json folder path and the entity class
        The build_all_entities methods will then create instances of entity_class from the json folder json_folder_path
        @param json_folder_path: the path of folder with json file containing the serialized entities
        @param entity_class: the class to instantiate
        """
        logger.info(
            "Initializing DATS connector for %s with folder path %s",
            entity_class.__name__,
            json_folder_path,
        )
        self.entity_class = entity_class
        self.json_folder_path = json_folder_path

    def build_all_entities(self) -> Generator[SolrEntity, None, None]:
        """
        Yields instances of self.entity_class parsed from the json files in self.json_folder_path
        """
        for data_dir in [
            data_directory[0] for data_directory in os.walk(self.json_folder_path)
        ]:
            with os.scandir(data_dir) as data_files:
                for data_file in data_files:
                    if not os.path.isdir(data_file):
                        logger.info("parsing file %s", data_file.name)
                        with open(
                            data_dir + "/" + data_file.name, encoding="utf8"
                        ) as json_file:
                            data = json.load(json_file)
                            filename = f"{data_dir}/{data_file.name}".replace(
                                f"{self.json_folder_path}/", ""
                            )
                            for entity in self.build_all_entities_for_dict(
                                data, filename
                            ):
                                yield entity

    @staticmethod
    def build_project(metadata, project, id_required=True, filename: str = None):
        logger.debug("building project")
        if "identifier" in metadata:
            project.id = metadata["identifier"]["identifier"]
        elif id_required:
            logger.warning("Project entity has no identifier")
        if filename:
            project.filename = filename
        if "title" in metadata:
            project.title = metadata["title"]
        logger.debug("project title is %s", project.title)
        if "description" in metadata:
            project.description = metadata["description"]
        if "types" in metadata:
            jsonpath_expr = parse("types[*].value")
            project.types = [match.value for match in jsonpath_expr.find(metadata)]

        if "fundedBy" in metadata:
            funded_by = []
            for grant in metadata["fundedBy"]:
                funded_by.append(
                    grant["name"]
                    + " (Grant number "
                    + grant["identifier"]["identifier"]
                    + ")"
                )
            project.funded_by = "; ".join(funded_by)

        if "keywords" in metadata:
            jsonpath_expr = parse("keywords[*].value")
            project.keywords = [match.value for match in jsonpath_expr.find(metadata)]

        if "projectLeads" in metadata and len(metadata["projectLeads"]) > 0:
            project.contacts = []
            for count, value in enumerate(metadata["projectLeads"]):
                if metadata["projectLeads"][count]:
                    (
                        email,
                        first_name,
                        last_name,
                        affiliation_name,
                        location,
                        full_name,
                    ) = (None, None, None, None, None, None)
                    roles = []
                    project_lead = metadata["projectLeads"][count]
                    if "firstName" in project_lead and project_lead["firstName"]:
                        first_name = project_lead["firstName"]
                    if "lastName" in project_lead and project_lead["lastName"]:
                        last_name = project_lead["lastName"]
                    if "fullName" in project_lead and project_lead["fullName"]:
                        full_name = project_lead["fullName"]
                    if "affiliations" in project_lead and project_lead["affiliations"]:
                        if (
                            "name" in project_lead["affiliations"][0]
                            and project_lead["affiliations"][0]["name"]
                        ):
                            affiliation_name = project_lead["affiliations"][0]["name"]
                        if (
                            "location" in project_lead["affiliations"][0]
                            and project_lead["affiliations"][0]["location"]
                        ):
                            location = project_lead["affiliations"][0]["location"][
                                "postalAddress"
                            ]
                    if "roles" in project_lead:
                        for i in range(0, len(project_lead["roles"])):
                            roles.append(project_lead["roles"][i]["value"])
                    if "email" in project_lead and project_lead["email"]:
                        email = project_lead["email"]

                    contact = Contact(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        affiliation=affiliation_name,
                        business_address=location,
                        full_name=full_name,
                        roles=roles,
                    )
                    project.contacts.append(contact)
        if "startDate" in metadata:
            project.start_date = metadata["startDate"]["date"]

        if "endDate" in metadata:
            project.end_date = metadata["endDate"]["date"]

        if "primaryPublications" in metadata:
            jsonpath_expr = parse("primaryPublications[*].identifier.identifier")
            project.reference_publications = [
                match.value for match in jsonpath_expr.find(metadata)
            ]
        if "projectWebsite" in metadata:
            project.website = metadata["projectWebsite"]

        project.slugs = []
        if "acronym" in metadata:
            project.project_name = metadata["acronym"]
            project.slugs.append(slugify(project.project_name))

        if "extraProperties" in metadata:
            for ep in metadata["extraProperties"]:
                if ep["category"] == "slugs":
                    project.slugs.extend(
                        [
                            value.get("value")
                            for value in ep.get("values", [])
                            if value.get("value")
                        ]
                    )

        if "projectAssets" in metadata:
            project.studies = []
            project.datasets = []
            for project_assets in metadata["projectAssets"]:
                dataset_linked_study = False
                if (
                    project_assets["@type"] == "Study"
                    and "identifier" in project_assets
                ):
                    dataset_linked_study = True
                    study_identifier = project_assets["identifier"]["identifier"]
                    project.studies.append(study_identifier)
                    logger.debug("linking project to study %s", study_identifier)

                if "output" in project_assets:
                    for dataset in project_assets["output"]:
                        if dataset["@type"] == "Dataset" and "identifier" in dataset:
                            if not dataset_linked_study:
                                dataset_identifier = dataset["identifier"]["identifier"]
                                logger.debug(
                                    "linking project to dataset %s", dataset_identifier
                                )
                                project.datasets.append(dataset_identifier)
                            if "extraProperties" in dataset:
                                for ep in dataset["extraProperties"]:
                                    if ep["category"] == "fairEvaluation":
                                        if ep["values"][0]["value"]:
                                            project.fair_evaluation = (
                                                "FAIRplus Evaluation"
                                            )
                elif (
                    "output" not in project_assets
                    and project_assets["@type"] == "Dataset"
                    and "identifier" in project_assets
                ):
                    dataset_identifier = project_assets["identifier"]["identifier"]
                    logger.debug("linking project to dataset %s", dataset_identifier)
                    project.datasets.append(dataset_identifier)
                    if "extraProperties" in project_assets:
                        for ep in project_assets["extraProperties"]:
                            if ep["category"] == "fairEvaluation":
                                if ep["values"][0]["value"]:
                                    project.fair_evaluation = "FAIRplus Evaluation"
        return project

    @staticmethod
    def build_study(metadata, study):
        logger.debug("building study")
        if "identifier" in metadata:
            study.id = metadata["identifier"]["identifier"]
        else:
            logger.warning("Study entity has no identifier")
        if "name" in metadata:
            study.primary_purpose = metadata["name"]

        if "acronym" in metadata:
            study.title = metadata["acronym"]
        logger.debug("study title is %s", study.title)

        if "description" in metadata:
            study.description = metadata["description"]

        if "types" in metadata:
            jsonpath_expr = parse("types[*].value")
            study.types = [match.value for match in jsonpath_expr.find(metadata)]

        # TO DO account for studies with >1 studyGroup
        if "studyGroups" in metadata and len(metadata["studyGroups"]) == 1:
            cohort = metadata["studyGroups"][0]
            if "size" in cohort:
                study.size = cohort["size"]

            if "name" in cohort:
                study.cohorts_description = cohort["name"]

            if "consentInformation" in cohort:
                for consent in cohort["consentInformation"]:
                    if consent["name"]["value"] == "informed consent":
                        study.informed_consent = True
                    else:
                        study.informed_consent = False

            if "characteristics" in cohort:

                characteristics = []
                for charac in cohort["characteristics"]:
                    dimension = ""
                    unit = ""
                    min = ""
                    max = ""
                    if "name" in charac:
                        dimension = charac["name"]["value"]
                    if "unit" in charac:
                        unit = charac["unit"]["value"]
                    value = ""
                    for val in charac["values"]:
                        if val["categoryIRI"] == "SIO:001113":
                            min = val["values"][0]["value"]
                        elif val["categoryIRI"] == "SIO:001114":
                            max = val["values"][0]["value"]
                        else:
                            if value == "":
                                value = (
                                    val["values"][0]["value"] + " " + val["category"]
                                )
                            else:
                                value = (
                                    value
                                    + ", "
                                    + val["values"][0]["value"]
                                    + " "
                                    + val["category"]
                                )

                    if min != "" or max != "":
                        range = min + "-" + max + " " + unit
                        field = dimension + ": " + range
                    elif value != "":
                        field = dimension + ": " + value + " " + unit
                    characteristics.append(field.strip())

                study.cohort_characteristics = characteristics

        if "input" in metadata:
            study.samples_source = []
            study.organisms = []
            study.disease = []
            study.samples_type = []
            for input in metadata["input"]:
                if "types" in input:
                    jsonpath_expr = parse("types[*].value")
                    study.samples_source.extend(
                        [match.value for match in jsonpath_expr.find(input)]
                    )

                if "taxonomy" in input:
                    jsonpath_expr = parse("taxonomy[*].name")
                    study.organisms.extend(
                        [match.value for match in jsonpath_expr.find(input)]
                    )

                if "bearerOfDisease" in input:
                    jsonpath_expr = parse("bearerOfDisease[*].name")
                    study.disease.extend(
                        [match.value for match in jsonpath_expr.find(input)]
                    )

                if "derivesFrom" in input:
                    jsonpath_expr = parse("derivesFrom[*].name")
                    study.samples_type.extend(
                        [match.value for match in jsonpath_expr.find(input)]
                    )
            study.samples_source = list(set(study.samples_source))
            study.organisms = list(set(study.organisms))
            study.disease = list(set(study.disease))
            study.samples_type = list(set(study.samples_type))

        if "output" in metadata:
            study.datasets = []

            for dataset in metadata["output"]:
                if dataset["@type"] == "Dataset" and "identifier" in dataset:
                    dataset_identifier = dataset["identifier"]["identifier"]
                    logger.debug("linking study to dataset %s", dataset_identifier)
                    study.datasets.append(dataset_identifier)

                    if "extraProperties" in dataset:
                        for ep in dataset["extraProperties"]:
                            if ep["category"] == "fairEvaluation":
                                if ep["values"][0]["value"]:
                                    study.fair_evaluation = "FAIRplus Evaluation"

        if "characteristics" in metadata:
            study_charac = []
            for ep in metadata["characteristics"]:
                if ep["name"]["valueIRI"] == "NCIT:C93599":
                    if ep["values"][0]["value"] == "true":
                        study.multi_center_study = True
                    elif ep["values"][0]["value"] == "false":
                        study.multi_center_study = False
                else:
                    dimension = ep["name"]["value"]
                    values = []
                    for value in ep["values"]:
                        values.append(value["value"])
                    study_charac.append(dimension + ": " + ", ".join(values))

            study.study_characteristics = study_charac

        if "extraProperties" in metadata:
            for ep in metadata["extraProperties"]:
                if ep["category"] == "slugs":
                    study.slugs = [
                        value.get("value")
                        for value in ep.get("values", [])
                        if value.get("value")
                    ]

        return study

    @staticmethod
    def build_dataset(metadata, dataset, id_required=True):
        logger.debug("build dataset")
        if "identifier" in metadata:
            dataset.id = metadata["identifier"]["identifier"]
        elif id_required:
            logger.error("Dataset entity has no identifier")
        if "title" in metadata:
            dataset.title = metadata["title"]
        logger.debug("dataset title is %s", dataset.title)
        if "types" in metadata:
            jsonpath_expr = parse("types[*].value")
            dataset.data_types = [match.value for match in jsonpath_expr.find(metadata)]

        if "isAbout" in metadata:
            treatment = []
            treatment_category = []
            disease = []
            sampleType = []
            for entity in metadata["isAbout"]:
                if entity["@type"] == "MolecularEntity":
                    treatment.append(entity["name"])

                    if "roles" in entity:
                        for role in entity["roles"]:
                            if role["value"] not in treatment_category:
                                treatment_category.append(role["value"])

                elif entity["@type"] == "Disease":
                    disease.append(entity["name"])

                elif entity["@type"] == "AnatomicalPart":
                    sampleType.append(entity["name"])

                elif entity["@type"] == "CategoryValuesPair":
                    if entity["category"] == "Experiment category":
                        for val in entity["values"]:
                            if val["value"] not in treatment_category:
                                treatment_category.append(val["value"])
                    if entity["category"] == "Experiment name":
                        for val in entity["values"]:
                            if val["value"] not in treatment:
                                treatment.append(val["value"])
                    if (
                        "categoryIRI" in entity
                        and entity["categoryIRI"] == "SIO:000069"
                    ):
                        for val in entity["values"]:
                            if val["value"] not in sampleType:
                                sampleType.append(val["value"])

            dataset.treatment_name = treatment
            dataset.treatment_category = treatment_category
            dataset.disease = disease
            dataset.samples_type = sampleType

        if "dataUseConditions" in metadata:
            dataset.use_restrictions = []
            restriction_label = []
            for condition in metadata["dataUseConditions"]:
                restriction = {
                    "use_class": "",
                    "use_class_label": "",
                    "use_class_note": "",
                    "use_restriction_note": "",
                    "use_restriction_rule": "",
                }
                if "abbreviation" in condition:
                    restriction["use_class"] = condition["abbreviation"]
                if "name" in condition:
                    restriction["use_class_label"] = condition["name"]
                    restriction_label.append(condition["name"])
                if "description" in condition:
                    restriction["use_restriction_note"] = condition["description"]
                if "restriction_type" in condition:
                    if type(condition["restriction_type"]) == str:
                        restriction["use_restriction_rule"] = condition[
                            "restriction_type"
                        ]
                    else:
                        restriction["use_restriction_rule"] = condition[
                            "restriction_type"
                        ]["value"]
                dataset.use_restrictions.append(restriction)

        if "dimensions" in metadata:
            for dimension in metadata["dimensions"]:
                if dimension["name"]["valueIRI"] == "NCIT:C53190":
                    dataset.samples_number = dimension["values"][0]["value"]

        if "extraProperties" in metadata:
            for ep in metadata["extraProperties"]:
                if ep["category"] == "fairEvaluation":
                    if ep["values"][0]["value"]:
                        dataset.fair_evaluation = "FAIRplus Evaluation"
                elif ep["category"] == "slugs":
                    dataset.slugs = [
                        value.get("value")
                        for value in ep.get("values", [])
                        if value.get("value")
                    ]
                else:
                    category = re.split("(?=[A-Z])", ep["category"])
                    attribute = "_".join(map(str.lower, category))
                    setattr(dataset, attribute, ep["values"][0]["value"])

        # TO DO deal with cases where there's more than one distribution object
        if "distributions" in metadata and len(metadata["distributions"]) == 1:
            distro = metadata["distributions"][0]

            if "access" in distro:
                if "accessURL" in distro["access"]:
                    dataset.dataset_link_href = distro["access"]["accessURL"]

                if "landingPage" in distro["access"]:
                    dataset.dataset_link_label = distro["access"]["landingPage"]

                if "types" in distro["access"]:
                    if distro["access"]["types"][0]["value"] == HOSTED_AT_INSTITUTION:
                        dataset.hosted = True

            if "version" in distro:
                dataset.version = distro["version"]

            if "conformsTo" in distro:
                jsonpath_expr = parse("conformsTo[*].name")
                dataset.data_standards = [
                    match.value for match in jsonpath_expr.find(distro)
                ]

            if "dates" in distro:
                for date in distro["dates"]:
                    if date["type"]["value"] == "creation date":
                        dataset.dataset_created = date["date"]
                    elif date["type"]["value"] == "last update date":
                        dataset.dataset_modified = date["date"]

            file_formats = []
            if "formats" in distro:
                for format in distro["formats"]:
                    if type(format) is str:
                        file_formats.append(format)
                    else:
                        file_formats.append(format["value"])
            dataset.file_formats = file_formats

        if "creators" in metadata:
            if (
                metadata["creators"][0]["@type"] == "Organization"
                and metadata["creators"][0]["name"] != ""
            ) or (
                metadata["creators"][0]["@type"] == "Person"
                and metadata["creators"][0]["fullName"] != ""
            ):
                for creator in metadata["creators"]:

                    if creator["@type"] == "Organization":
                        dataset.dataset_owner = creator["name"]

                    elif creator["@type"] == "Person":
                        dataset.dataset_contact = creator["fullName"]
                        if "affiliations" in creator:
                            dataset.dataset_affiliation = creator["affiliations"][0][
                                "name"
                            ]

                    if "email" in creator:
                        dataset.dataset_email = creator["email"]
        return dataset

    def build_all_entities_for_dict(self, data, filename: str = None):
        if self.entity_class == Project:
            new_project = Project()
            yield self.build_project(data, new_project, filename=filename)
        elif self.entity_class == Dataset:
            if "projectAssets" in data:
                for asset in data["projectAssets"]:
                    if asset["@type"] == "Dataset":
                        new_dataset = Dataset()
                        yield self.build_dataset(asset, new_dataset)
                    elif asset["@type"] == "Study" and "output" in asset:
                        for dataset_metadata in asset["output"]:
                            new_dataset = Dataset()
                            yield self.build_dataset(dataset_metadata, new_dataset)
        elif self.entity_class == Study:
            if "projectAssets" in data:
                for study_metadata in data["projectAssets"]:
                    if study_metadata["@type"] == "Study":
                        new_study = Study()
                        yield self.build_study(study_metadata, new_study)
        else:
            logger.error("Entity type not recognised")
