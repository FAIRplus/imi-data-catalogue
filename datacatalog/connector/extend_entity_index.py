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
    datacatalog.connector.extend_entity_index.py
    -------------------

   Module containing the EntitiesIndexExtender class


"""
import logging

from .. import app
from ..controllers.web_controllers import get_entity
from ..models.dataset import Dataset
from ..models.project import Project
from ..models.study import Study

__author__ = "Nirmeen Sallam"

logger = logging.getLogger(__name__)


class EntitiesIndexExtender(object):
    """
    Entities index extender
    """

    @staticmethod
    def extend_project_index() -> None:
        logger.debug("extend project index")
        if not app.config.get("SOLR_QUERY_SEARCH_EXTENDED"):
            logger.debug("solr query search extended not enabled in settings")
            return
        projects = Project.query.all()

        for project in projects:
            logger.debug("processing project %s", project.id)
            project.datasets_metadata = []
            dataset_data = []
            project.studies_metadata = []
            study_data = []
            logger.debug("indexing project's datasets")
            for dataset in project.datasets or []:
                curr_dataset = get_entity("dataset", dataset)
                for field in (
                    app.config.get("SOLR_QUERY_TEXT_FIELD_EXTENDED", {}).get("dataset")
                    or []
                ):
                    if isinstance(getattr(curr_dataset, field), list):
                        dataset_data += getattr(curr_dataset, field)
                    else:
                        dataset_data.append(getattr(curr_dataset, field))

            logger.debug("indexing project's studies")
            for study in project.studies or []:
                curr_study = get_entity("study", study)
                for field in (
                    app.config.get("SOLR_QUERY_TEXT_FIELD_EXTENDED", {}).get("study")
                    or []
                ):
                    if isinstance(getattr(curr_study, field), list):
                        study_data += getattr(curr_study, field)
                    else:
                        study_data.append(getattr(curr_study, field))

                logger.debug("indexing study's datasets")
                for dataset in curr_study.datasets or []:
                    curr_dataset = get_entity("dataset", dataset)
                    for field in (
                        app.config.get("SOLR_QUERY_TEXT_FIELD_EXTENDED", {}).get(
                            "dataset"
                        )
                        or []
                    ):
                        if isinstance(getattr(curr_dataset, field), list):
                            dataset_data += getattr(curr_dataset, field)
                        else:
                            dataset_data.append(getattr(curr_dataset, field))

            if study_data:
                project.studies_metadata += study_data

            if dataset_data:
                project.datasets_metadata += dataset_data

            # if dataset_data or study_data:
            project.save()
        app.config["_solr_orm"].commit()

    @staticmethod
    def extend_study_index() -> None:
        if not app.config.get("SOLR_QUERY_SEARCH_EXTENDED"):
            logger.debug("solr query search extended not enabled in settings")
            return
        studies = Study.query.all()

        for study in studies:
            logger.debug("processing study %s", study.title)
            study.datasets_metadata = []
            dataset_data = []
            study.projects_metadata = []
            project_data = []
            logger.debug("indexing study's dataset")
            for dataset in study.datasets or []:
                curr_dataset = get_entity("dataset", dataset)
                for field in (
                    app.config.get("SOLR_QUERY_TEXT_FIELD_EXTENDED", {}).get("dataset")
                    or []
                ):
                    if isinstance(getattr(curr_dataset, field), list):
                        dataset_data += getattr(curr_dataset, field)
                    else:
                        dataset_data.append(getattr(curr_dataset, field))
            if dataset_data:
                study.datasets_metadata += dataset_data

            if app.config.get("SOLR_QUERY_SEARCH_EXTENDED_2_WAY_INDEX"):
                logger.debug("indexing study's project")
                curr_project = study.project_entity
                if curr_project:
                    for field in (
                        app.config.get("SOLR_QUERY_TEXT_FIELD_EXTENDED", {}).get(
                            "project"
                        )
                        or []
                    ):
                        if isinstance(getattr(curr_project, field), list):
                            project_data += getattr(curr_project, field)
                        else:
                            project_data.append(getattr(curr_project, field))
                    if project_data:
                        study.projects_metadata += project_data

            # if dataset_data or project_data:
            study.save()
        app.config["_solr_orm"].commit()

    @staticmethod
    def extend_dataset_index() -> None:
        if not app.config.get("SOLR_QUERY_SEARCH_EXTENDED") or not app.config.get(
            "SOLR_QUERY_SEARCH_EXTENDED_2_WAY_INDEX"
        ):
            logger.debug(
                "solr query search extended or 2 way index not enabled in settings"
            )
            return
        datasets = Dataset.query.all()

        for dataset in datasets:
            logger.debug("processing dataset %s", dataset.id)
            dataset.studies_metadata = []
            study_data = []
            dataset.projects_metadata = []
            project_data = []
            curr_project = []

            curr_study = dataset.study_entity

            if curr_study:
                for field in (
                    app.config.get("SOLR_QUERY_TEXT_FIELD_EXTENDED", {}).get("study")
                    or []
                ):
                    if isinstance(getattr(curr_study, field), list):
                        study_data += getattr(curr_study, field)
                    else:
                        study_data.append(getattr(curr_study, field))
                if study_data:
                    dataset.studies_metadata += study_data

                curr_project = dataset.study_entity.project_entity

            if not curr_project:
                curr_project = dataset.project_entity

            if curr_project:
                for field in (
                    app.config.get("SOLR_QUERY_TEXT_FIELD_EXTENDED", {}).get("project")
                    or []
                ):
                    if isinstance(getattr(curr_project, field), list):
                        project_data += getattr(curr_project, field)
                    else:
                        project_data.append(getattr(curr_project, field))
                if project_data:
                    dataset.projects_metadata += project_data

            # if study_data or project_data:
            dataset.save()
        app.config["_solr_orm"].commit()
