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

import os
from datetime import datetime
from typing import Generator

import GEOparse

from .entities_connector import EntitiesConnector
from ... import app
from ...models.dataset import Dataset

"""
    datacatalog.importer.connector.geostudies_connector
    -------------------

   Module containing the GEOStudiesConnector class


"""
__author__ = "kavita.rege"

logger = app.logger


class GEOStudiesConnector(EntitiesConnector):
    """
    Import datasets from the geo database.
    From a list of geo studies id, downloads them from the geo database and creates datasets.
    """

    def __init__(self, study_file_path: str) -> None:
        """
        Initialize GEOStudiesConnector instance configuring the study file path.
        This file must contain a list of geo studies to import.
        One id per line, example:
            GSE31773
            GSE44037
        @param study_file_path: the file containing the list of geo identifiers
        """
        self.geostudies_list = study_file_path

    def build_all_entities(self) -> Generator[Dataset, None, None]:
        """
        For each geo study specified in self.geostudies_list, retrieves the metadata from geo database
        and yields a corresponding dataset.
        """
        try:
            for file in os.listdir(self.geostudies_list):
                if file.endswith('.txt'):
                    disease_name = file.split(".")[0]
                    geostudies_open = open(os.path.join(self.geostudies_list, file), 'r')
                    for series in geostudies_open:
                        logger.info("Downloading GEO Series " + series)
                        gse = GEOparse.get_GEO(geo=series.strip(), destdir=app.config.get('GEO_TEMP_FOLDER'),
                                               silent=True)

                        yield self.create_dataset(gse, disease_name)
        except ValueError as e:
            logger.error(e)

    @staticmethod
    def create_dataset(gse: 'GEOparse.BaseGEO', disease_name: str) -> Dataset:
        """
        Create a Dataset instance from a geoparse object and a disease name
        @param gse: geoparse object containing the metadata from the geo database
        @param disease_name:
        @return: a Dataset instance
        """
        logger.info("Processing and creating dataset")
        metadata = gse.metadata
        dataset_id = metadata['geo_accession'][0]

        dataset = Dataset(None, dataset_id)
        if disease_name:
            dataset.therapeutic_area_standards_disease = disease_name
        if 'title' in metadata:
            dataset.title = metadata['title'][0]
        if 'summary' in metadata:
            dataset.notes = metadata['summary'][0]
        if 'contact_name' in metadata:
            dataset.contact_names = metadata['contact_name'][0].replace(',,', '.').replace(',', '.')
        address = metadata['contact_institute'][0] + "  " + metadata['contact_address'][0] + "  " + \
                  metadata['contact_city'][0] \
                  + "  " + metadata['contact_zip/postal_code'][0] + "  " + metadata['contact_country'][0]
        dataset.business_address = address
        if 'relation' in metadata:
            index = [i for i, x in enumerate(gse.metadata['relation']) if 'BioProject' in x][0]
            link = gse.metadata['relation'][index].split(":", 1)[1]
            if link:
                dataset.project_website = link
        if 'contact_phone' in metadata:
            dataset.business_phone_number = metadata['contact_phone'][0]
        if 'contact_email' in metadata:
            dataset.contact_email = metadata['contact_email'][0]
        if 'pubmed_id' in metadata:
            dataset.pubmed_link = metadata['pubmed_id'][0]
            dataset.reference_publications = metadata['pubmed_id']
        if 'type' in metadata:
            dataset.samples_type = metadata['type'][0]
        if 'sample_id' in metadata:
            dataset.samples_number = len(metadata['sample_id'][0])
        if 'platform_id' in metadata:
            dataset.organism = gse.gpls[gse.metadata['platform_id'][0]].metadata['organism'][0]
        if 'last_update_date' in metadata:
            dataset.dataset_modified = datetime.strptime(gse.metadata['last_update_date'][0], "%b %d %Y").date()
        dataset.groups = ['GEO']
        dataset.tags = ['GEO']
        # TODO, enable this when download feature is activated
        # dataset.open_access_link = app.config.get('DATASET_OPEN_ACCESS_LINK_REPOSITORY') + disease_name + "/" + dataset_id + ".zip"
        return dataset
