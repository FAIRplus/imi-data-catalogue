import os

from datacatalog import app
from datacatalog.connector.dats_connector import DATSConnector
from datacatalog.connector.extend_entity_index import EntitiesIndexExtender
from datacatalog.controllers.web_controllers import get_entity
from datacatalog.importer.entities_importer import EntitiesImporter
from datacatalog.models.dataset import Dataset
from datacatalog.models.project import Project
from datacatalog.models.study import Study
from tests.base_test import BaseTest

__author__ = "Nirmeen Sallam"


class TestExtendEntityIndex(BaseTest):
    connector = [
        DATSConnector(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../../data/imi_projects"
            ),
            Project,
        ),
        DATSConnector(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../../data/imi_projects"
            ),
            Study,
        ),
        DATSConnector(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../../data/imi_projects"
            ),
            Dataset,
        ),
    ]
    entities_importer = EntitiesImporter(connector)

    assert_with_title = False
    if (
        app.config.get("SOLR_QUERY_TEXT_FIELD_EXTENDED")
        and "title" in app.config.get("SOLR_QUERY_TEXT_FIELD_EXTENDED").get("dataset")
        and "title" in app.config.get("SOLR_QUERY_TEXT_FIELD_EXTENDED").get("study")
        and "title" in app.config.get("SOLR_QUERY_TEXT_FIELD_EXTENDED").get("project")
    ):
        assert_with_title = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.solr_orm = app.config["_solr_orm"]
        cls.solr_orm.delete_fields()
        cls.solr_orm.create_fields()
        cls.entities_importer.import_all()

    def test_extend_project_index(self):
        if app.config.get("SOLR_QUERY_SEARCH_EXTENDED"):

            EntitiesIndexExtender.extend_project_index()

            projects = Project.query.all()

            datasets_found = False
            datasets_metadata_found = False

            studies_found = False
            studies_metadata_found = False
            for project in projects:
                if project.datasets:
                    datasets_found = True
                    if project.datasets_metadata:
                        datasets_metadata_found = True
                        if self.assert_with_title:
                            curr_dataset = get_entity("dataset", project.datasets[0])
                            self.assertIn(curr_dataset.title, project.datasets_metadata)

                if project.studies:
                    studies_found = True
                    if project.studies_metadata:
                        studies_metadata_found = True
                        if self.assert_with_title:
                            curr_study = get_entity("study", project.studies[0])
                            self.assertIn(curr_study.title, project.studies_metadata)

                if datasets_metadata_found or studies_metadata_found:
                    break

            self.assertEqual(datasets_found, datasets_metadata_found)
            self.assertEqual(studies_found, studies_metadata_found)

    def test_extend_study_index(self):
        if app.config.get("SOLR_QUERY_SEARCH_EXTENDED"):

            EntitiesIndexExtender.extend_study_index()

            studies = Study.query.all()

            datasets_found = False
            datasets_metadata_found = False

            projects_found = False
            projects_metadata_found = False
            for study in studies:
                if study.datasets:
                    datasets_found = True
                    if study.datasets_metadata:
                        datasets_metadata_found = True
                        if self.assert_with_title:
                            curr_dataset = get_entity("dataset", study.datasets[0])
                            self.assertIn(curr_dataset.title, study.datasets_metadata)
                if app.config.get("SOLR_QUERY_SEARCH_EXTENDED_2_WAY_INDEX"):
                    if study.project_entity:
                        projects_found = True
                        if study.projects_metadata:
                            projects_metadata_found = True
                            if self.assert_with_title:
                                self.assertIn(
                                    study.project_entity.title, study.projects_metadata
                                )

                if datasets_metadata_found or projects_metadata_found:
                    break

            self.assertEqual(datasets_found, datasets_metadata_found)
            if app.config.get("SOLR_QUERY_SEARCH_EXTENDED_2_WAY_INDEX"):
                self.assertEqual(projects_found, projects_metadata_found)

    def test_extend_dataset_index(self):
        if app.config.get("SOLR_QUERY_SEARCH_EXTENDED") and app.config.get(
            "SOLR_QUERY_SEARCH_EXTENDED_2_WAY_INDEX"
        ):

            EntitiesIndexExtender.extend_dataset_index()

            datasets = Dataset.query.all()

            projects_found = False
            projects_metadata_found = False

            studies_found = False
            studies_metadata_found = False
            for dataset in datasets:
                if dataset.study_entity and dataset.study_entity.project_entity:
                    projects_found = True
                    if dataset.projects_metadata:
                        projects_metadata_found = True
                        if self.assert_with_title:
                            self.assertIn(
                                dataset.study_entity.project_entity.title,
                                dataset.projects_metadata,
                            )

                if dataset.study_entity:
                    studies_found = True
                    if dataset.studies_metadata:
                        studies_metadata_found = True
                        if self.assert_with_title:
                            self.assertIn(
                                dataset.study_entity.title, dataset.studies_metadata
                            )

                if projects_metadata_found or studies_metadata_found:
                    break

            self.assertEqual(projects_found, projects_metadata_found)
            self.assertEqual(studies_found, studies_metadata_found)

    @classmethod
    def tearDownClass(cls):
        app.config["_solr_orm"].delete(query="*:*")
        app.config["_solr_orm"].delete_fields()
        app.config["_solr_orm"].commit()
