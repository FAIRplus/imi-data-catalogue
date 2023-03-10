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
import csv
import json
import logging
import os
import re
import uuid
from datetime import datetime
from typing import Generator, Type

import GEOparse

from .entities_connector import ImportEntitiesConnector
from .. import app
from ..models.dataset import Dataset
from ..models.project import Project
from ..models.study import Study
from ..solr.solr_orm_entity import SolrEntity

"""
    datacatalog.connector.geostudies_connector
    -------------------

   Module containing the GEOStudiesConnector class


"""
__author__ = "kavita.rege"

logger = logging.getLogger(__name__)


class GEOStudiesConnector(ImportEntitiesConnector):
    """
    Import datasets from the geo database.
    From a list of geo studies id, downloads them from the geo database and creates datasets.
    Alternatively, import directly from local json files
    """

    def __init__(self, input_folder_path: str, entity_class: Type[SolrEntity]) -> None:
        """
        Initialize GEOStudiesConnector instance configuring the folder of the files to import.
        The folder can contain either tsv files with one geo id per line or directly json files
        One id per line, example:
            GSE31773
            GSE44037
        @param input_folder_path: the path to the folder containing the geo files
        @param entity_class: the kind of entity to create
        """
        self.input_folder_path = input_folder_path
        self.entity_class = entity_class

    def build_all_entities(self) -> Generator[SolrEntity, None, None]:
        """
        For each geo study specified in self.input_folder_path, retrieves the metadata from geo database or
         from the json files
        and yields a corresponding project, study or dataset.
        """
        with os.scandir(self.input_folder_path) as data_files:
            for data_file in data_files:
                try:
                    new_entity = self.entity_class()

                    json_full_path = os.path.join(
                        self.input_folder_path, data_file.name
                    )
                    logger.info("importing from file %s", json_full_path)
                    if data_file.name.endswith(".tsv"):
                        with open(json_full_path, "r") as new_geo_studies:
                            rd = csv.reader(
                                new_geo_studies, delimiter="\t", quotechar='"'
                            )

                            for entry in rd:
                                series = entry.split("\t")[0]
                                disease_name = entry.spit("\t")[1]
                                logger.info("Downloading GEO Series " + series)
                                gse = GEOparse.get_GEO(
                                    geo=series.strip(),
                                    destdir=app.config.get("GEO_TEMP_FOLDER"),
                                    silent=True,
                                )
                                metadata = gse.metadata
                                metadata["disease"] = disease_name
                                metadata["project_id"] = str(uuid.uuid1())
                                metadata["dataset_id"] = str(uuid.uuid1())
                                metadata["study_id"] = str(uuid.uuid1())
                                accession = gse.get_accession()

                                meta_json = json.dumps(metadata, indent=4)
                                with open(
                                    self.input_folder_path + accession + ".json", "w"
                                ) as f:
                                    f.write(meta_json)
                                self.create_entry(metadata, new_entity)
                                yield new_entity
                    elif data_file.name.endswith(".json"):
                        with open(json_full_path) as json_file:
                            metadata = json.load(json_file)
                        self.create_entry(metadata, new_entity)
                        yield new_entity
                    else:
                        logger.warning("ignoring file, format not supported")
                except ValueError as e:
                    logger.error(e)

    @staticmethod
    def create_entry(metadata: dict, new_entity: SolrEntity) -> None:
        """
        Configure the new_entity instance with metadata from the metadata dict
        @param metadata: dict containing the metadata from the geo files
        @param new_entity: the instance to configure
        @return: None
        """
        if isinstance(new_entity, Project):
            # title, geo_accession, summary, type, contributor, contact*, web_link?, relation?, citation
            if "title" in metadata:
                new_entity.title = metadata["title"][0]
            if "geo_accession" in metadata:
                new_entity.project_name = metadata["geo_accession"][0]
            new_entity.keywords = ["NCBI GEO"]
            if "project_id" in metadata:
                new_entity.id = metadata["project_id"]
            if "summary" in metadata:
                para = ""
                for line in metadata["summary"]:
                    if "Keywords" in line:
                        line = line.replace("Keywords: ", "")
                        new_entity.keywords = re.split("; |, ", line)
                    else:
                        para = para + line
                new_entity.description = para

            if "keywords" in metadata:
                for kw in metadata["keywords"]:
                    new_entity.keywords.append(kw)

            if "type" in metadata:
                for t in metadata["type"]:
                    new_entity.keywords.append(t)

            if "contact_name" in metadata:
                new_entity.display_name = (
                    metadata["contact_name"][0].replace(",,", " ").replace(",", " ")
                )
            if "contact_email" in metadata:
                new_entity.email = metadata["contact_email"][0]
            if "contact_institute" in metadata:
                new_entity.affiliation = metadata["contact_institute"][0]
            address = ""
            if "contact_address" in metadata:
                address = address + metadata["contact_address"][0] + ","
            if "contact_city" in metadata:
                address = address + metadata["contact_city"][0] + ","
            if "contact_state" in metadata:
                address = address + metadata["contact_state"][0] + ","
            if "contact_zip/postal_code" in metadata:
                address = address + metadata["contact_zip/postal_code"][0] + ","
            if "contact_country" in metadata:
                address = address + metadata["contact_country"][0]
            new_entity.business_address = address

            if "contact_phone" in metadata:
                new_entity.business_phone_number = metadata["contact_phone"][0]
            if "contact_fax" in metadata:
                new_entity.business_fax_number = metadata["contact_fax"][0]

            if "relation" in metadata:
                index = [
                    i for i, x in enumerate(metadata["relation"]) if "BioProject" in x
                ][0]
                link = metadata["relation"][index].split(":", 1)[1]
                if link:
                    new_entity.website = link

            if "pubmed_id" in metadata:
                new_entity.reference_publications = []
                for pmid in metadata["pubmed_id"]:
                    new_entity.reference_publications.append(
                        "https://pubmed.ncbi.nlm.nih.gov/" + pmid
                    )

            new_entity.types = ["NCBI GEO"]

            if "study_id" in metadata:
                new_entity.studies = [metadata["study_id"]]

            if "dataset_id" in metadata and "study_id" not in metadata:
                new_entity.datasets = [metadata["dataset_id"]]

        elif isinstance(new_entity, Dataset):
            # submission_date, last_update_date, status?, supplementary_file, platform_id, platform_taxid

            if "dataset_id" in metadata:
                new_entity.id = metadata["dataset_id"]

            if "title" in metadata:
                new_entity.title = metadata["title"][0]

            if "submission_date" in metadata:
                sub_date = datetime.strptime(metadata["submission_date"][0], "%b %d %Y")
                new_entity.dataset_created = sub_date.date()

            if "last_update_date" in metadata:
                update_date = datetime.strptime(
                    metadata["last_update_date"][0], "%b %d %Y"
                )
                new_entity.dataset_modified = update_date.date()

            if "platform_id" in metadata:
                new_entity.platform = ",".join(metadata["platform_id"])

            if "type" in metadata:
                new_entity.data_types = metadata["type"]

            if "supplementary_file" in metadata:
                new_entity.dataset_link_href = metadata["supplementary_file"][0]

            if "disease" in metadata:
                new_entity.disease = metadata["disease"]

            if "sample_id" in metadata:
                new_entity.samples_number = str(len(metadata["sample_id"]))

        elif isinstance(new_entity, Study):
            # overall_design, sample_id, sample_taxid

            if "study_id" in metadata:
                new_entity.id = metadata["study_id"]

            if "title" in metadata:
                new_entity.title = metadata["title"][0]

            if "overall_design" in metadata:
                para = ""
                for line in metadata["overall_design"]:
                    para = para + line
                new_entity.description = para

            if "dataset_id" in metadata:
                new_entity.datasets = [metadata["dataset_id"]]

            if "disease" in metadata:
                new_entity.disease = metadata["disease"]

            if "species" in metadata:
                new_entity.organisms = [metadata["species"]]
        else:
            logger.error("Entity type not recognised")
