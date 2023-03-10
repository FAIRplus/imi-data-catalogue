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
    datacatalog.exporter.dats_exporter
    -------------------

   Module containing the DATSExporter class


"""
import json
import logging
from typing import Dict

import werkzeug.exceptions
from flask import safe_join

from .. import app
from ..models.dataset import Dataset
from ..models.project import Project
from ..models.study import Study

__author__ = "Nirmeen Sallam, Abetare Shabani"

from ..solr.solr_orm_entity import SolrEntity

logger = logging.getLogger(__name__)

w3id_base_url = "https://w3id.org/dats/context/sdo/"
w3id_annotation = w3id_base_url + "annotation_sdo_context.jsonld"

value_block = {
    "values": [],
    "@type": "CategoryValuesPair",
    "category": "",
}

annot_block = {
    "value": "",
    "@type": "Annotation",
    "@context": "https://w3id.org/dats/context/sdo/annotation_sdo_context.jsonld",
}


class DATSExporter:
    """
    Export entity directly from JSON to Dats
    """

    def __init__(self) -> None:
        """
        Initialize a DATSExporter instance configuring the entity class
        The export_entities methods will then create Dats file of entity_class from the json object
        """
        pass

    def export_dats_entity(self, entity) -> Dict:
        """
        Returns Dats json file of the solr entity
        """
        metadata = {}
        if entity.connector_name and entity.connector_name.lower() == "datsconnector":
            return DATSExporter.read_dats_file(metadata, entity)
        else:
            if isinstance(entity, Dataset) or isinstance(entity, Study):
                parent_entity = DATSExporter.get_entity_parent(entity)
                if isinstance(parent_entity, Project):
                    return self.build_dats_project(metadata, parent_entity)
            elif isinstance(entity, Project):
                return self.build_dats_project(metadata, entity)
            else:
                logger.warning("Entity type not recognised")

    @staticmethod
    def get_entity_filename(entity: SolrEntity) -> str:
        return entity.filename

    @staticmethod
    def read_dats_file(metadata: dict, entity: SolrEntity) -> dict:
        """
        Returns the data directly from a specific file
        @param: metadata
        @param: entity
        """
        try:
            entity_path = app.config["JSON_FILE_PATH"][
                f"{entity.__class__.__name__.lower()}"
            ]
            parent_entity = DATSExporter.get_entity_parent(entity)
            if parent_entity:
                project_name = DATSExporter.get_entity_filename(parent_entity)
            else:
                project_name = DATSExporter.get_entity_filename(entity)
            filepath = safe_join(entity_path, project_name)
            with open(filepath, "r") as f:
                metadata = json.load(f)
            return metadata
        except FileNotFoundError as e:
            logger.error(e)

    @staticmethod
    def build_dats_project(metadata, project):
        logger.debug("exporting project %s as DATS", project.id)
        metadata["@type"] = "Project"
        metadata["@context"] = [
            w3id_base_url + "dataset_sdo_context.jsonld",
            "http://w3id.org/dats/context/obo/dataset_obo_context.jsonld",
        ]
        if project.id:
            metadata["identifier"] = {
                "identifier": project.id,
                "@type": "Identifier",
                "@context": w3id_base_url + "identifier_info_sdo_context.jsonld",
            }
        else:
            logger.warning("Project entity has no identifier: %s", project.title)

        if project.title:
            metadata["title"] = project.title
        if project.description:
            metadata["description"] = project.description

        metadata["types"] = []
        if project.types:
            for project_type in project.types:
                temp = {
                    "@type": "Annotation",
                    "@context": w3id_annotation,
                    "value": project_type,
                }
                metadata["types"].append(temp)

        if project.funded_by:
            metadata["fundedBy"] = []
            funded_by_names = project.funded_by.split(", ")
            for name in funded_by_names:
                temp = {
                    "name": name,
                    "@type": "Grant",
                    "@context": w3id_base_url + "grant_sdo_context.jsonld",
                }
                metadata["fundedBy"].append(temp)

        if project.keywords:
            metadata["keywords"] = []
            for keyword in project.keywords:
                temp = {
                    "@type": "Annotation",
                    "@context": w3id_annotation,
                    "value": keyword,
                }
                metadata["keywords"].append(temp)
        metadata["projectLeads"] = []
        for count, contact in enumerate(project.contacts or []):
            temp = {
                "@type": "Person",
                "@context": w3id_base_url + "person_sdo_context.jsonld",
            }
            metadata["projectLeads"].append(temp)
            if contact.first_name:
                metadata["projectLeads"][count]["firstName"] = contact.first_name
            else:
                metadata["projectLeads"][count]["firstName"] = ""

            if contact.last_name:
                metadata["projectLeads"][count]["lastName"] = contact.last_name
            else:
                metadata["projectLeads"][count]["lastName"] = ""

            if contact.full_name:
                metadata["projectLeads"][count]["fullName"] = contact.full_name
            else:
                metadata["projectLeads"][count]["fullName"] = "-"

            if contact.email:
                metadata["projectLeads"][count]["email"] = contact.email
            else:
                metadata["projectLeads"][count]["email"] = "-"

            if contact.affiliation:
                metadata["projectLeads"][count]["affiliations"] = [
                    {
                        "@type": "Organization",
                        "@context": w3id_base_url + "organization_sdo_context.jsonld",
                        "name": contact.affiliation,
                    }
                ]
            else:
                metadata["projectLeads"][count]["affiliations"] = [
                    {
                        "@type": "Organization",
                        "@context": w3id_base_url + "organization_sdo_context.jsonld",
                        "name": "-",
                    }
                ]
            if contact.business_address:
                metadata["projectLeads"][count]["affiliations"][0]["location"] = {
                    "postalAddress": contact.business_address,
                    "@type": "Place",
                    "@context": w3id_base_url + "place_sdo_context.jsonld",
                }
            else:
                metadata["projectLeads"][count]["affiliations"][0]["location"] = {
                    "postalAddress": "-",
                    "@type": "Place",
                    "@context": w3id_base_url + "place_sdo_context.jsonld",
                }

            if contact.roles:
                metadata["projectLeads"][count]["roles"] = []
                for role in contact.roles:
                    temp = {
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                        "value": role,
                    }
                    metadata["projectLeads"][count]["roles"].append(temp)
            else:
                metadata["projectLeads"][count]["roles"] = []

        if project.start_date:
            metadata["startDate"] = {
                "@type": "Date",
                "@context": w3id_base_url + "date_info_sdo_context.jsonld",
                "date": project.start_date,
                "type": {
                    "value": "start date",
                    "valueIRI": "http://semanticscience.org/resource/SIO_000031",
                },
            }

        if project.end_date:
            metadata["endDate"] = {
                "@type": "Date",
                "@context": w3id_base_url + "date_info_sdo_context.jsonld",
                "date": project.end_date,
                "type": {
                    "value": "end date",
                    "valueIRI": "http://semanticscience.org/resource/SIO_000036",
                },
            }

        if project.reference_publications:
            metadata["primaryPublications"] = []
            for publication in project.reference_publications:
                temp = {
                    "@type": "Publication",
                    "@context": w3id_base_url + "publication_sdo_context.jsonld",
                    "identifier": {
                        "identifier": publication,
                        "@type": "Identifier",
                        "@context": w3id_base_url
                        + "identifier_info_sdo_context.jsonld",
                    },
                }
                metadata["primaryPublications"].append(temp)

        if project.website or project.project_name:
            metadata["extraProperties"] = []
            if project.website:
                temp = {
                    "values": [
                        {
                            "value": project.website,
                            "@type": "Annotation",
                            "@context": w3id_annotation,
                        }
                    ],
                    "category": "website",
                }
                metadata["extraProperties"].append(temp)

            elif project.project_name:
                temp = {
                    "values": [
                        {
                            "value": project.project_name,
                            "@type": "Annotation",
                            "@context": w3id_annotation,
                        }
                    ],
                    "@type": "CategoryValuesPair",
                    "category": "projectAcronym",
                }
                metadata["extraProperties"].append(temp)
        metadata["projectAssets"] = []
        if project.studies or project.datasets:
            if project.studies:
                for study in project.studies:
                    entity = Study.query.get_or_404(study)
                    metadata["projectAssets"].append(
                        DATSExporter.build_dats_study({}, entity)
                    )

            if project.datasets:
                for dataset in project.datasets:
                    entity = Dataset.query.get_or_404(dataset)
                    metadata["projectAssets"].append(
                        DATSExporter.build_dats_dataset({}, entity)
                    )
        if project.project_name:
            metadata["acronym"] = project.project_name
        if project.website:
            metadata["projectWebsite"] = project.website
        return metadata

    @staticmethod
    def build_dats_dataset(metadata, dataset):
        logger.debug("exporting dataset %s as DATS, %s", dataset.id, dataset.title)
        template = {
            "@type": "Dataset",
            "@context": w3id_base_url + "dataset_sdo_context.jsonld",
            "title": "dataset_title",
            "identifier": {
                "identifier": "dataset.id",
                "@type": "Identifier",
                "@context": w3id_base_url + "identifier_info_sdo_context.jsonld",
            },
            "creators": [
                {
                    "@type": "Organization",
                    "@context": "https://w3id.org/dats/context/sdo/organization_sdo_context.jsonld",
                    "name": "",
                }
            ],
        }
        if dataset.samples_number:
            template["dimensions"] = []
            temp = {
                "name": {
                    "value": "sample size",
                    "valueIRI": "NCIT:C53190",
                    "@type": "Annotation",
                    "@context": "https://w3id.org/dats/context/sdo/annotation_sdo_context.jsonld",
                },
                "values": [
                    {
                        "value": dataset.samples_number,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "Dimension",
                "@context": "http://w3id.org/dats/context/obo/category_values_pair_obo_context.jsonld",
            }
            template["dimensions"].append(temp)

        if dataset.title:
            template["title"] = dataset.title

        if dataset.id:
            template["identifier"] = {
                "identifier": dataset.id,
                "@type": "Identifier",
                "@context": w3id_base_url + "identifier_info_sdo_context.jsonld",
            }
        else:
            logger.warning("Dataset entity has no identifier: %s", dataset.title)

        template["types"] = []
        if dataset.data_types:
            for dataset_type in dataset.data_types:
                temp = {
                    "@type": "Annotation",
                    "@context": w3id_annotation,
                    "value": dataset_type,
                }
                template["types"].append(temp)
        else:
            temp = {
                "@type": "Annotation",
                "@context": w3id_annotation,
                "value": "",
            }
            template["types"].append(temp)

        if dataset.treatment_name or dataset.disease:
            template["isAbout"] = []

        if dataset.treatment_name:
            for treatment_name in dataset.treatment_name:
                temp = {
                    "@type": "MolecularEntity",
                    "@context": w3id_base_url + "molecular_entity_sdo_context.jsonld",
                    "name": treatment_name,
                    "identifier": {},
                }
                template["isAbout"].append(temp)
        if dataset.disease:
            for disease in dataset.disease:
                temp = {
                    "name": disease,
                    "@type": "Disease",
                    "@context": w3id_base_url + "disease_sdo_context.jsonld",
                }
                template["isAbout"].append(temp)
        if dataset.fair_evaluation:
            template["extraProperties"] = []
        if dataset.fair_assessment_link_pre:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_assessment_link_pre,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairAssessmentLinkPre",
            }
            template["extraProperties"].append(temp)
        if dataset.fair_score_representation_pre:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_score_representation_pre,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairScoreRepresentationPre",
            }
            template["extraProperties"].append(temp)
        if dataset.fair_score_content_pre:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_score_content_pre,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairScoreContentPre",
            }
            template["extraProperties"].append(temp)
        if dataset.fair_score_hosting_pre:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_score_hosting_pre,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairScoreHostingPre",
            }
            template["extraProperties"].append(temp)
        if dataset.fair_score_overall_pre:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_score_overall_pre,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairScoreOverallPre",
            }
            template["extraProperties"].append(temp)
        if dataset.fair_indicators_href_pre:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_indicators_href_pre,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairIndicatorsHrefPre",
            }
            template["extraProperties"].append(temp)
        if dataset.fair_indicators_pre:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_indicators_pre,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairIndicatorsPre",
            }
            template["extraProperties"].append(temp)
        if dataset.fair_assessment_link_post:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_assessment_link_post,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairAssessmentLinkPost",
            }
            template["extraProperties"].append(temp)
        if dataset.fair_score_representation_post:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_score_representation_post,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairScoreRepresentationPost",
            }
            template["extraProperties"].append(temp)
        if dataset.fair_score_content_post:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_score_content_post,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairScoreContentPost",
            }
            template["extraProperties"].append(temp)
        if dataset.fair_score_hosting_post:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_score_hosting_post,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairScoreHostingPost",
            }
            template["extraProperties"].append(temp)
        if dataset.fair_score_overall_post:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_score_overall_post,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairScoreOverallPost",
            }
            template["extraProperties"].append(temp)
        if dataset.fair_indicators_href_post:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_indicators_href_post,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairIndicatorsHrefPost",
            }
            template["extraProperties"].append(temp)
        if dataset.fair_indicators_post:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_indicators_post,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairIndicatorsPost",
            }
            template["extraProperties"].append(temp)
        if dataset.fair_evaluation:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_evaluation,
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairEvaluation",
            }
            template["extraProperties"].append(temp)

        template["distributions"] = [
            {
                "@type": "DatasetDistribution",
                "@context": "https://w3id.org/dats/context/sdo"
                "/dataset_distribution_sdo_context.jsonld",
                "access": {
                    "accessURL": "",
                    "landingPage": "",
                    "@type": "Access",
                    "@context": w3id_base_url + "access_sdo_context.jsonld",
                },
            }
        ]
        if dataset.dataset_link_href or dataset.dataset_link_label:
            template["distributions"][0]["access"]["accessURL"] = (
                dataset.dataset_link_href or ""
            )

            template["distributions"][0]["access"]["landingPage"] = (
                dataset.dataset_link_label or ""
            )

        if dataset.dataset_created or dataset.dataset_modified:
            template["distributions"][0]["dates"] = []
            if dataset.dataset_created:
                temp = {
                    "date": dataset.dataset_created,
                    "@type": "Date",
                    "@context": w3id_base_url + "date_info_sdo_context.jsonld",
                    "type": {
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                        "value": "creation date",
                    },
                }
                template["distributions"][0]["dates"].append(temp)
            if dataset.dataset_modified:
                temp = {
                    "date": dataset.dataset_modified,
                    "@type": "Date",
                    "@context": w3id_base_url + "date_info_sdo_context.jsonld",
                    "type": {
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                        "value": "last update date",
                    },
                }
                template["distributions"][0]["dates"].append(temp)

        if dataset.data_standards:
            template["distributions"][0]["conformsTo"] = [
                {
                    "name": dataset.data_standards,
                    "type": {
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                        "value": "clinical data standard",
                    },
                    "@type": "DataStandard",
                    "@context": w3id_base_url + "data_standard_sdo_context.jsonld",
                }
            ]
        if dataset.version:
            template["distributions"][0]["version"] = dataset.version

        metadata["projectAssets"] = template

        return template

    @staticmethod
    def build_dats_study(metadata, study):
        logger.debug("exporting study %s as DATS, %s", study.id, study.title)
        template = {
            "@type": "Study",
            "@context": w3id_base_url + "study_sdo_context.jsonld",
            "identifier": {
                "identifier": "study",
                "@type": "Identifier",
                "@context": w3id_base_url + "identifier_info_sdo_context.jsonld",
            },
        }

        if study.id:
            template["identifier"]["identifier"] = study.id
        else:
            logger.warning("Study entity has no identifier: %s", study.title)

        if study.title:
            template["acronym"] = study.title

        if study.primary_purpose:
            template["name"] = study.primary_purpose
        else:
            template["name"] = "-"

        if study.description:
            template["description"] = study.description

        if study.types:
            template["types"] = []
            for study_type in study.types:
                temp = {
                    "@type": "Annotation",
                    "@context": w3id_annotation,
                    "value": study_type,
                }
                template["types"].append(temp)

        if study.size or study.cohorts_description:
            template["studyGroups"] = [
                {
                    "@type": "StudyGroup",
                    "@context": w3id_base_url + "studygroup_sdo_context.jsonld",
                }
            ]
            if study.size:
                template["studyGroups"][0]["size"] = study.size
            if study.cohorts_description:
                template["studyGroups"][0]["name"] = study.cohorts_description

            if study.cohort_characteristics:
                template["studyGroups"][0]["characteristics"] = []

                for charac in study.cohort_characteristics:
                    dimension = charac.split(":")[0].strip()
                    value = charac.split(":")[1].strip()

                    nums = []
                    unit = ""
                    min = ""
                    max = ""
                    if "-" in value:
                        min = value.split("-")[0].strip()
                        max_u = value.split("-")[1].strip()

                        if " " in max_u:
                            max = max_u.split(" ")[0].strip()
                            unit = max_u.split(" ")[1].strip()

                    elif "," in value:
                        cats = []
                        vals = value.split(",")
                        for val in vals:
                            num = val.split(" ")[0].strip()
                            category = val.split(" ")[1].strip()
                            nums.append(num)
                            cats.append(category)

                    temp = {
                        "name": {
                            "value": "",
                            "@type": "Annotation",
                            "@context": "https://w3id.org/dats/context/sdo/annotation_sdo_context.jsonld",
                        },
                        "values": [],
                        "@type": "Dimension",
                        "@context": "https://w3id.org/dats/context/sdo/dimension_sdo_context.jsonld",
                    }

                    temp["name"]["value"] = dimension
                    if unit != "":
                        temp["unit"] = annot_block.copy()
                        temp["unit"]["value"] = unit
                    if min != "" and max != "":
                        min_block = value_block.copy()
                        min_val = annot_block.copy()
                        min_val["value"] = min
                        min_block["values"].append(min_val)
                        min_block["category"] = "minimal value"

                        max_block = value_block.copy()
                        max_val = annot_block.copy()
                        max_val["value"] = max
                        max_block["values"].append(max_val)
                        max_block["category"] = "maximal value"

                        temp["values"].append(min_block)
                        temp["values"].append(max_block)

                    if len(nums) > 0:
                        for n in nums:
                            block = value_block.copy()
                            value = annot_block.copy()
                            value["value"] = n
                            block["values"].append(value)
                            block["category"] = cats[nums.index(n)]
                            temp["values"].append(block)
                    template["studyGroups"][0]["characteristics"].append(temp)

            if study.informed_consent is not None and study.informed_consent is True:
                template["studyGroups"][0]["consentInformation"] = [
                    {
                        "name": {
                            "value": "Informed Consent",
                            "@type": "Annotation",
                            "@context": "https://w3id.org/dats/context/sdo/annotation_sdo_context.jsonld",
                        },
                        "identifier": {
                            "@type": "Identifier",
                            "@context": "https://w3id.org/dats/context/sdo/identifier_info_sdo_context.jsonld",
                            "identifier": "NCIT:C16735",
                            "identifierSource": "NCIt",
                        },
                        "@type": "ConsentInfo",
                        "@context": "https://w3id.org/dats/context/sdo/consent_info_obo_context.jsonld",
                    }
                ]

        if study.organisms or study.disease or study.samples_type:
            template["input"] = [
                {
                    "@type": "Material",
                    "@context": w3id_base_url + "material_sdo_context.jsonld",
                    "name": "input material",
                }
            ]

            if study.organisms:
                template["input"][0]["taxonomy"] = []
                for organism in study.organisms:
                    temp = {
                        "@type": "TaxonomicInformation",
                        "@context": w3id_base_url + "taxonomic_info_sdo_context.jsonld",
                        "name": organism,
                    }
                    template["input"][0]["taxonomy"].append(temp)

            if study.disease:
                template["input"][0]["bearerOfDisease"] = []
                for disease in study.disease:
                    temp = {
                        "name": disease,
                        "@type": "Disease",
                        "@context": w3id_base_url + "disease_sdo_context.jsonld",
                    }
                    template["input"][0]["bearerOfDisease"].append(temp)

            if study.samples_type:
                template["input"][0]["derivesFrom"] = []
                for samples_type in study.samples_type:
                    temp = {
                        "name": samples_type,
                        "@type": "AnatomicalPart",
                        "@context": w3id_base_url
                        + "anatomical_part_sdo_context.jsonld",
                    }
                    template["input"][0]["derivesFrom"].append(temp)

        if study.datasets:
            template["output"] = []
            for dataset in study.datasets:
                entity = Dataset.query.get_or_404(dataset)
                template["output"].append(
                    DATSExporter.build_dats_dataset(metadata, entity)
                )
        if study.multi_center_study is not None:
            template["characteristics"] = []

            temp = {
                "name": {
                    "value": "Multi-institution Indicator",
                    "@type": "Annotation",
                    "@context": "https://w3id.org/dats/context/sdo/annotation_sdo_context.jsonld",
                },
                "identifier": {
                    "@type": "Identifier",
                    "@context": "https://w3id.org/dats/context/sdo/identifier_info_sdo_context.jsonld",
                    "identifier": "NCIT:C93599",
                    "identifierSource": "NCIt",
                },
                "values": [
                    {
                        "value": str(study.multi_center_study),
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                    }
                ],
                "@type": "Dimension",
                "@context": "https://w3id.org/dats/context/sdo/dimension_sdo_context.jsonld",
            }
            template["characteristics"].append(temp)
            metadata["projectAssets"] = template
        return template

    @staticmethod
    def get_entity_parent(entity: SolrEntity) -> SolrEntity:
        try:
            entity_name = f"{entity.__class__.__name__}".lower()
            if entity_name == "dataset":
                if entity.study_entity:
                    child_entity = entity.study_entity
                    parent_entity = child_entity.project_entity
                else:
                    parent_entity = entity.project_entity
                return parent_entity
            elif entity_name == "study":
                return entity.project_entity
            else:
                logger.info("Reached parent in the hierarchy")
                return None
        except werkzeug.exceptions.NotFound as e:
            logger.error(e)
