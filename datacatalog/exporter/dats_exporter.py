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
from typing import Dict

from .. import app
from ..models.dataset import Dataset
from ..models.project import Project
from ..models.study import Study

__author__ = 'Nirmeen Sallam'

logger = app.logger

w3id_base_url = "https://w3id.org/dats/context/sdo/"
w3id_annotation = w3id_base_url+"annotation_sdo_context.jsonld"


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

        if isinstance(entity, Project):
            return self.build_dats_project(metadata, entity)
        elif isinstance(entity, Dataset):
            return self.build_dats_dataset(metadata, entity)
        elif isinstance(entity, Study):
            return self.build_dats_study(metadata, entity)
        else:
            logger.error("Entity type not recognised")

    @staticmethod
    def build_dats_project(metadata, project):

        metadata["@type"] = "Project"
        metadata["@context"] = [w3id_base_url+"dataset_sdo_context.jsonld",
                                "http://w3id.org/dats/context/obo/dataset_obo_context.jsonld"]
        if project.id:
            metadata['identifier'] = {
                "identifier": project.id,
                "@type": "Identifier",
                "@context": w3id_base_url+"identifier_info_sdo_context.jsonld"
            }
        else:
            logger.error("Project entity has no identifier")

        if project.title:
            metadata['title'] = project.title
        if project.description:
            metadata['description'] = project.description

        metadata['types'] = []
        if project.types:
            for project_type in project.types:
                temp = {
                    "@type": "Annotation",
                    "@context": w3id_annotation,
                    "value": project_type
                }
                metadata['types'].append(temp)

        if project.funded_by:
            metadata['fundedBy'] = []
            funded_by_names = project.funded_by.split(", ")
            for name in funded_by_names:
                temp = {"name": name,
                        "@type": "Grant",
                        "@context": w3id_base_url+"grant_sdo_context.jsonld"
                        }
                metadata['fundedBy'].append(temp)

        if project.keywords:
            metadata['keywords'] = []
            for keyword in project.keywords:
                temp = {
                    "@type": "Annotation",
                    "@context": w3id_annotation,
                    "value": keyword
                }
                metadata['keywords'].append(temp)

        if project.contact_title or project.first_name or project.last_name or project.email or \
                project.affiliation or project.business_address or project.role or project.business_fax_number or \
                project.business_phone_number:
            metadata['projectLeads'] = [{
                "@type": "Person",
                "@context": w3id_base_url+"person_sdo_context.jsonld"
            }]
            if project.contact_title:
                metadata['projectLeads'][0]['title'] = project.contact_title
            if project.first_name:
                metadata['projectLeads'][0]['firstName'] = project.first_name
            else:
                metadata['projectLeads'][0]['firstName'] = ''
            if project.last_name:
                metadata['projectLeads'][0]['lastName'] = project.last_name
            else:
                metadata['projectLeads'][0]['lastName'] = ''

            if project.email:
                metadata['projectLeads'][0]['email'] = project.email

            if project.affiliation:
                metadata['projectLeads'][0]['affiliations'] = [{
                    "@type": "Organization",
                    "@context": w3id_base_url+"organization_sdo_context.jsonld",
                    "name": project.affiliation
                }]

                if project.business_address:
                    metadata['projectLeads'][0]['affiliations'][0]['location'] = {
                        "postalAddress": project.business_address,
                        "@type": "Place",
                        "@context": w3id_base_url+"place_sdo_context.jsonld"
                    }

            if project.role:
                metadata['projectLeads'][0]['roles'] = []
                if isinstance(project.role, str):
                    roles = project.role.split(", ")
                else:
                    roles = project.role
                for role in roles:
                    temp = {
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                        "value": role
                    }
                    metadata['projectLeads'][0]['roles'].append(temp)

            if project.business_phone_number or project.business_fax_number:
                metadata['projectLeads'][0]['extraProperties'] = []
                if project.business_phone_number:
                    temp = {
                        "values": [
                            {
                                "value": project.business_phone_number,
                                "@type": "Annotation",
                                "@context": w3id_annotation
                            }
                        ],
                        "category": "phoneNumber"
                    }
                    metadata['projectLeads'][0]['extraProperties'].append(temp)

                elif project.business_fax_number:
                    temp = {
                        "values": [
                            {
                                "value": project.business_fax_number,
                                "@type": "Annotation",
                                "@context": w3id_annotation
                            }
                        ],
                        "category": "faxNumber"
                    }
                    metadata['projectLeads'][0]['extraProperties'].append(temp)

        if project.start_date:
            metadata['startDate'] = {
                "@type": "Date",
                "@context": w3id_base_url+"date_info_sdo_context.jsonld",
                "date": project.start_date,
                "type": {
                    "value": "start date",
                    "valueIRI": "http://semanticscience.org/resource/SIO_000031"
                }
            }

        if project.end_date:
            metadata['endDate'] = {
                "@type": "Date",
                "@context": w3id_base_url+"date_info_sdo_context.jsonld",
                "date": project.end_date,
                "type": {
                    "value": "end date",
                    "valueIRI": "http://semanticscience.org/resource/SIO_000036"
                }
            }

        if project.reference_publications:
            metadata['primaryPublications'] = []
            for publication in project.reference_publications:
                temp = {
                    "@type": "Publication",
                    "@context": w3id_base_url+"publication_sdo_context.jsonld",
                    "identifier": {
                        "identifier": publication,
                        "@type": "Identifier",
                        "@context": w3id_base_url+"identifier_info_sdo_context.jsonld"
                    }
                }
                metadata['primaryPublications'].append(temp)

        if project.website or project.project_name:
            metadata['extraProperties'] = []
            if project.website:
                temp = {
                    "values": [
                        {
                            "value": project.website,
                            "@type": "Annotation",
                            "@context": w3id_annotation
                        }
                    ],
                    "category": "website"
                }
                metadata['extraProperties'].append(temp)

            elif project.project_name:
                temp = {
                    "values": [
                        {
                            "value": project.project_name,
                            "@type": "Annotation",
                            "@context": w3id_annotation
                        }
                    ],
                    "@type": "CategoryValuesPair",
                    "category": "projectAcronym"
                }
                metadata['extraProperties'].append(temp)

        if project.studies or project.datasets:
            metadata['projectAssets'] = []
            if project.studies:
                for study in project.studies:
                    temp = {
                        "@type": "Study",
                        "@context": w3id_base_url+"study_sdo_context.jsonld",
                        "identifier": {
                            "identifier": study,
                            "@type": "Identifier",
                            "@context": w3id_base_url+"identifier_info_sdo_context.jsonld"
                        }

                    }
                    metadata['projectAssets'].append(temp)
            if project.datasets:
                metadata['projectAssets'][0]['output'] = []
                for dataset in project.datasets:
                    temp = {
                        "@type": "Dataset",
                        "@context": w3id_base_url+"dataset_sdo_context.jsonld",
                        "identifier": {
                            "identifier": dataset,
                            "@type": "Identifier",
                            "@context": w3id_base_url+"identifier_info_sdo_context.jsonld"
                        }

                    }
                    metadata['projectAssets'][0]['output'].append(temp)

        return metadata

    @staticmethod
    def build_dats_dataset(metadata, dataset):
        metadata["projectAssets"] = [{}]
        metadata["projectAssets"][0]["@type"] = "Dataset"
        metadata["projectAssets"][0]["@context"] = w3id_base_url+"dataset_sdo_context.jsonld"
        if dataset.title:
            metadata["projectAssets"][0]['title'] = dataset.title

        if dataset.id:
            metadata["projectAssets"][0]['identifier'] = {
                "identifier": dataset.id,
                "@type": "Identifier",
                "@context": w3id_base_url+"identifier_info_sdo_context.jsonld"
            }
        else:
            logger.error("Dataset entity has no identifier")

        metadata["projectAssets"][0]['types'] = []
        if dataset.data_types:
            for dataset_type in dataset.data_types:
                temp = {
                    "method": {
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                        "value": dataset_type
                    },
                    "@type": "DataType",
                    "@context": w3id_base_url+"data_type_sdo_context.jsonld"
                }
                metadata["projectAssets"][0]['types'].append(temp)
        if dataset.platform:
            for platform in dataset.platform:
                temp = {
                    "method": {
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                        "value": platform
                    },
                    "@type": "DataType",
                    "@context": w3id_base_url+"data_type_sdo_context.jsonld"
                }
                metadata["projectAssets"][0]['types'].append(temp)

        if dataset.treatment_name or dataset.disease:
            metadata["projectAssets"][0]['isAbout'] = []

        if dataset.treatment_name:
            treatments = dataset.treatment_name.split(",")
            for treatment_name in treatments:
                temp = {
                    "@type": "MolecularEntity",
                    "@context": w3id_base_url+"molecular_entity_sdo_context.jsonld",
                    "name": treatment_name,
                    "identifier": {

                    }
                }
                metadata["projectAssets"][0]['isAbout'].append(temp)

        if dataset.disease:
            temp = {
                "name": dataset.disease,
                "@type": "Disease",
                "@context": w3id_base_url+"disease_sdo_context.jsonld"
            }
            metadata["projectAssets"][0]['isAbout'].append(temp)

        if dataset.samples_number or dataset.fair_indicators or dataset.fair_indicators_href \
                or dataset.fair_score_mandatory_indicators or dataset.fair_score_overall \
                or dataset.fair_score_recommended_indicators or dataset.fair_assessment_details \
                or dataset.fair_assessment_details_link or dataset.is_fairplus_evaluated:
            metadata["projectAssets"][0]["extraProperties"] = []
        if dataset.samples_number:
            temp = {
                "category": "number of samples",
                "values": [
                    {
                        "value": dataset.samples_number,
                        "@type": "Annotation",
                        "@context": w3id_annotation
                    }
                ],
                "@type": "CategoryValuesPair",
                "@context": "http://w3id.org/dats/context/obo/category_values_pair_obo_context.jsonld"
            }
            metadata["projectAssets"][0]["extraProperties"].append(temp)

        if dataset.fair_assessment_details:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_assessment_details,
                        "@type": "Annotation",
                        "@context": w3id_annotation
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairAssessmentDetails"
            }
            metadata["projectAssets"][0]["extraProperties"].append(temp)
        if dataset.fair_assessment_details_link:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_assessment_details_link,
                        "@type": "Annotation",
                        "@context": w3id_annotation
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairAssessmentLink"
            }
            metadata["projectAssets"][0]["extraProperties"].append(temp)
        if dataset.fair_indicators:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_indicators,
                        "@type": "Annotation",
                        "@context": w3id_annotation
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairIndicators"
            }
            metadata["projectAssets"][0]["extraProperties"].append(temp)
        if dataset.fair_indicators_href:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_indicators_href,
                        "@type": "Annotation",
                        "@context": w3id_annotation
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairIndicatorsHref"
            }
            metadata["projectAssets"][0]["extraProperties"].append(temp)
        if dataset.fair_score_mandatory_indicators:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_score_mandatory_indicators,
                        "@type": "Annotation",
                        "@context": w3id_annotation
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairScoreMandatory"
            }
            metadata["projectAssets"][0]["extraProperties"].append(temp)
        if dataset.fair_score_recommended_indicators:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_score_recommended_indicators,
                        "@type": "Annotation",
                        "@context": w3id_annotation
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairScoreRecommended"
            }
            metadata["projectAssets"][0]["extraProperties"].append(temp)
        if dataset.fair_score_overall:
            temp = {
                "values": [
                    {
                        "value": dataset.fair_score_overall,
                        "@type": "Annotation",
                        "@context": w3id_annotation
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairScoreOverall"
            }
            metadata["projectAssets"][0]["extraProperties"].append(temp)
        if dataset.is_fairplus_evaluated:
            temp = {
                "values": [
                    {
                        "value": dataset.is_fairplus_evaluated,
                        "@type": "Annotation",
                        "@context": w3id_annotation
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "fairEvaluation"
            }
            metadata["projectAssets"][0]["extraProperties"].append(temp)

        metadata["projectAssets"][0]["distributions"] = [{"@type": "DatasetDistribution",
                                                          "@context": "https://w3id.org/dats/context/sdo"
                                                                      "/dataset_distribution_sdo_context.jsonld"}]

        if dataset.dataset_link_href or dataset.dataset_link_label:
            metadata["projectAssets"][0]["distributions"][0]["access"] = {
                "accessURL": dataset.dataset_link_href if dataset.dataset_link_href else "",
                "landingPage": dataset.dataset_link_label if dataset.dataset_link_label else "",
                "@type": "Access",
                "@context": w3id_base_url+"access_sdo_context.jsonld"
            }
        if dataset.dataset_created or dataset.dataset_modified:
            metadata["projectAssets"][0]["distributions"][0]["dates"] = []
            if dataset.dataset_created:
                temp = {
                    "date": dataset.dataset_created,
                    "@type": "Date",
                    "@context": w3id_base_url+"date_info_sdo_context.jsonld",
                    "type": {
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                        "value": "creation date"
                    }
                }
                metadata["projectAssets"][0]["distributions"][0]["dates"].append(temp)
            if dataset.dataset_modified:
                temp = {
                    "date": dataset.dataset_modified,
                    "@type": "Date",
                    "@context": w3id_base_url+"date_info_sdo_context.jsonld",
                    "type": {
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                        "value": "last update date"
                    }
                }
                metadata["projectAssets"][0]["distributions"][0]["dates"].append(temp)

        if dataset.data_standards:
            metadata["projectAssets"][0]["distributions"][0]["conformsTo"] = [
                {
                    "name": dataset.data_standards,
                    "type": {
                        "@type": "Annotation",
                        "@context": w3id_annotation,
                        "value": "clinical data standard"
                    },
                    "@type": "DataStandard",
                    "@context": w3id_base_url+"data_standard_sdo_context.jsonld"
                }
            ]
        if dataset.version:
            metadata["projectAssets"][0]["distributions"][0]["version"] = dataset.version

        return metadata

    @staticmethod
    def build_dats_study(metadata, study):
        metadata["projectAssets"] = [{}]
        metadata["projectAssets"][0]["@type"] = "Study"
        metadata["projectAssets"][0]["@context"] = w3id_base_url+"study_sdo_context.jsonld"

        if study.id:
            metadata["projectAssets"][0]['identifier'] = {
                "identifier": study.id,
                "@type": "Identifier",
                "@context": w3id_base_url+"identifier_info_sdo_context.jsonld"
            }
        else:
            logger.error("Study entity has no identifier")

        if study.title:
            metadata["projectAssets"][0]['name'] = study.title

        if study.description:
            metadata["projectAssets"][0]['description'] = study.description

        if study.types:
            metadata["projectAssets"][0]['types'] = []
            for study_type in study.types:
                temp = {
                    "@type": "Annotation",
                    "@context": w3id_annotation,
                    "value": study_type
                }
                metadata["projectAssets"][0]['types'].append(temp)

        if study.size or study.cohorts_description:
            metadata["projectAssets"][0]['studyGroups'] = [{
                "@type": "StudyGroup",
                "@context": w3id_base_url+"studygroup_sdo_context.jsonld"
            }]
            if study.size:
                metadata["projectAssets"][0]['studyGroups'][0]['size'] = study.size
            if study.cohorts_description:
                metadata["projectAssets"][0]['studyGroups'][0]['name'] = study.cohorts_description

            if study.age_range or study.bmi_range:
                metadata["projectAssets"][0]['studyGroups'][0]['extraProperties'] = []
                if study.bmi_range is not None:
                    lower, upper = study.bmi_range.split('-')
                    if lower:
                        lower_range = {
                            "values": [
                                {
                                    "value": lower,
                                    "@type": "Annotation",
                                    "@context": w3id_annotation
                                }
                            ],
                            "@type": "CategoryValuesPair",
                            "category": "BMI range lower limit"
                        }
                        metadata["projectAssets"][0]['studyGroups'][0]['extraProperties'].append(lower_range)
                    if upper:
                        upper_range = {
                            "values": [
                                {
                                    "value": upper,
                                    "@type": "Annotation",
                                    "@context": w3id_annotation
                                }
                            ],
                            "@type": "CategoryValuesPair",
                            "category": "BMI range upper limit"
                        }
                        metadata["projectAssets"][0]['studyGroups'][0]['extraProperties'].append(upper_range)
                if study.age_range:
                    lower, upper_unit = study.age_range.split('-')
                    upper, unit = upper_unit.split(" ")
                    if lower:
                        lower_range = {
                            "values": [
                                {
                                    "value": lower,
                                    "@type": "Annotation",
                                    "@context": w3id_annotation
                                }
                            ],
                            "@type": "CategoryValuesPair",
                            "category": "Age range lower limit"
                        }
                        metadata["projectAssets"][0]['studyGroups'][0]['extraProperties'].append(lower_range)
                    if upper:
                        upper_range = {
                            "values": [
                                {
                                    "value": upper,
                                    "@type": "Annotation",
                                    "@context": w3id_annotation
                                }
                            ],
                            "@type": "CategoryValuesPair",
                            "category": "Age range upper limit"
                        }
                        metadata["projectAssets"][0]['studyGroups'][0]['extraProperties'].append(upper_range)
                    if unit:
                        unit = {
                            "values": [
                                {
                                    "value": unit,
                                    "@type": "Annotation",
                                    "@context": w3id_annotation
                                }
                            ],
                            "@type": "CategoryValuesPair",
                            "category": "Age unit"
                        }
                        metadata["projectAssets"][0]['studyGroups'][0]['extraProperties'].append(unit)

        if study.organisms or study.disease or study.samples_type:
            metadata["projectAssets"][0]['input'] = [{
                "@type": "Material",
                "@context": w3id_base_url+"material_sdo_context.jsonld",
                "name": "input material"
            }]

            if study.organisms:
                metadata["projectAssets"][0]['input'][0]['taxonomy'] = []
                for organism in study.organisms:
                    temp = {
                        "@type": "TaxonomicInformation",
                        "@context": w3id_base_url+"taxonomic_info_sdo_context.jsonld",
                        "name": organism
                    }

                    metadata["projectAssets"][0]['input'][0]['taxonomy'].append(temp)

            if study.disease:
                metadata["projectAssets"][0]['input'][0]['bearerOfDisease'] = []
                for disease in study.disease:
                    temp = {
                        "name": disease,
                        "@type": "Disease",
                        "@context": w3id_base_url+"disease_sdo_context.jsonld"
                    }
                    metadata["projectAssets"][0]['input'][0]['bearerOfDisease'].append(temp)

            if study.samples_type:
                metadata["projectAssets"][0]['input'][0]['derivesFrom'] = []
                for samples_type in study.samples_type:
                    temp = {
                        "name": samples_type,
                        "@type": "AnatomicalPart",
                        "@context": w3id_base_url+"anatomical_part_sdo_context.jsonld"
                    }
                    metadata["projectAssets"][0]['input'][0]['derivesFrom'].append(temp)

        if study.datasets:
            metadata['projectAssets'][0]['output'] = []
            for dataset in study.datasets:
                temp = {
                    "@type": "Dataset",
                    "@context": w3id_base_url+"dataset_sdo_context.jsonld",
                    "identifier": {
                        "identifier": dataset,
                        "@type": "Identifier",
                        "@context": w3id_base_url+"identifier_info_sdo_context.jsonld"
                    }

                }
                metadata['projectAssets'][0]['output'].append(temp)
        if study.informed_consent is not None or study.primary_purpose or study.multi_center_study is not None:
            metadata['projectAssets'][0]['extraProperties'] = []
        if study.informed_consent is not None:
            temp = {
                "values": [
                    {
                        "value": str(study.informed_consent),
                        "@type": "Annotation",
                        "@context": w3id_annotation
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "informedConsent"
            }
            metadata['projectAssets'][0]['extraProperties'].append(temp)
        if study.primary_purpose:
            temp = {
                "values": [
                    {
                        "value": study.primary_purpose,
                        "@type": "Annotation",
                        "@context": w3id_annotation
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "primaryPurpose"
            }
            metadata['projectAssets'][0]['extraProperties'].append(temp)
        if study.multi_center_study is not None:
            temp = {
                "values": [
                    {
                        "value": str(study.multi_center_study),
                        "@type": "Annotation",
                        "@context": w3id_annotation
                    }
                ],
                "@type": "CategoryValuesPair",
                "category": "multiCenter"
            }
            metadata['projectAssets'][0]['extraProperties'].append(temp)
        return metadata
