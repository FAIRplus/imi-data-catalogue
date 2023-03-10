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

import json
import os
import tempfile

from datacatalog import app
from datacatalog.connector.dats_connector import DATSConnector
from datacatalog.exporter.dats_exporter import DATSExporter
from datacatalog.importer.entities_importer import EntitiesImporter
from datacatalog.models.dataset import Dataset
from datacatalog.models.project import Project
from datacatalog.models.study import Study
from tests.base_test import BaseTest, get_resource_path
from tests.dats import dats_model

__author__ = "Nirmeen Sallam"


class TestDATSExporter(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.solr_orm = app.config["_solr_orm"]
        cls.solr_orm.delete_fields()
        cls.solr_orm.create_fields()

    def test_build_all_datasets(self):
        dats_exporter = DATSExporter()
        base_folder = get_resource_path("imi_projects_test")

        dats_datasets_connector = DATSConnector(
            base_folder,
            Dataset,
        )

        dats_projects_connector = DATSConnector(
            base_folder,
            Project,
        )

        dats_studies_connector = DATSConnector(
            base_folder,
            Study,
        )

        importer = EntitiesImporter(
            [dats_datasets_connector, dats_studies_connector, dats_projects_connector]
        )
        importer.import_all()

        datasets = list(dats_datasets_connector.build_all_entities())
        for dataset in datasets:
            dats_entity = dats_exporter.export_dats_entity(dataset)
            if len(dats_entity["projectAssets"]) > 0:
                datasets_list = [
                    x.get("title")
                    for x in dats_entity["projectAssets"]
                    if x["@type"] == "Dataset"
                ]
                for child_entity in dats_entity["projectAssets"]:
                    if (
                        child_entity["@type"] == "Study"
                        and len(child_entity.get("output", [])) > 0
                    ):
                        datasets_list += [
                            x.get("title") for x in child_entity["output"]
                        ]

                self.assertIn(dataset.title, datasets_list)

        projects = list(dats_projects_connector.build_all_entities())
        for project in projects:
            dats_entity = dats_exporter.export_dats_entity(project)
            self.assertEqual(dats_entity["title"], project.title)

        studies = list(dats_studies_connector.build_all_entities())
        for study in studies:
            dats_entity = dats_exporter.export_dats_entity(study)
            if len(dats_entity["projectAssets"]) > 0:
                studies_list = [
                    x.get("acronym")
                    for x in dats_entity["projectAssets"]
                    if x["@type"] == "Study"
                ]
                self.assertIn(study.title, studies_list)

    def test_export_type_project_root(self):
        dats_exporter = DATSExporter()

        dataset_title = "Dataset with study and project parents"
        dataset = Dataset(dataset_title, "this-is-a-test-dataset-identifier")
        dataset.save()
        study_title = "Study with project parent and dataset child"
        study = Study(study_title, "this-is-a-test-study-identifier")
        study.save()
        study.datasets = [dataset.id]
        study.save()
        project_title = "Project with study and dataset children"
        project = Project(project_title, "this-is-a-test-project-identifier")
        project.save()
        project.studies = [study.id]
        project.save()
        app.config["_solr_orm"].commit()

        test_project = Project.query.get_or_404("this-is-a-test-project-identifier")
        test_study = Study.query.get_or_404("this-is-a-test-study-identifier")
        test_dataset = Dataset.query.get_or_404("this-is-a-test-dataset-identifier")

        test_dats_project = dats_exporter.export_dats_entity(test_project)
        test_dats_study = dats_exporter.export_dats_entity(test_study)
        test_dats_dataset = dats_exporter.export_dats_entity(test_dataset)

        self.assertEqual(test_dats_project["@type"], "Project")
        self.assertEqual(test_dats_study["@type"], "Project")
        self.assertEqual(test_dats_dataset["@type"], "Project")

    def test_export_type_project_root_no_study(self):
        dats_exporter = DATSExporter()

        dataset_title = "Dataset with study and project parents"
        dataset = Dataset(dataset_title, "this-is-a-test-dataset-identifier")
        dataset.save()
        project_title = "Project with study and dataset children"
        project = Project(project_title, "this-is-a-test-project-identifier")
        project.save()
        project.datasets = [dataset.id]
        project.save()
        app.config["_solr_orm"].commit()

        test_project = Project.query.get_or_404("this-is-a-test-project-identifier")
        test_dataset = Dataset.query.get_or_404("this-is-a-test-dataset-identifier")

        test_dats_project = dats_exporter.export_dats_entity(test_project)
        test_dats_dataset = dats_exporter.export_dats_entity(test_dataset)

        self.assertEqual(test_dats_project["@type"], "Project")
        self.assertEqual(test_dats_dataset["@type"], "Project")

    def test_export_project_children_number(self):
        dats_exporter = DATSExporter()

        study_title = "Study with project parent"
        study1 = Study(study_title, "this-is-first-test-study-identifier")
        study1.save()
        study2 = Study(study_title, "this-is-second-test-study-identifier")
        study2.save()
        study3 = Study(study_title, "this-is-third-test-study-identifier")
        study3.save()

        project_title = "Project with studies children"
        project = Project(project_title, "this-is-a-test-project-identifier")
        project.save()
        project.studies = [study1.id, study2.id, study3.id]
        project.save()
        app.config["_solr_orm"].commit()

        test_project = Project.query.get_or_404("this-is-a-test-project-identifier")
        test_dats_project = dats_exporter.export_dats_entity(test_project)

        self.assertEqual(len(test_dats_project["projectAssets"]), 3)

    def test_export_study_children_number(self):
        dats_exporter = DATSExporter()

        dataset_title = "Dataset with study parent"
        dataset1 = Dataset(dataset_title, "this-is-first-test-dataset-identifier")
        dataset1.save()
        dataset2 = Dataset(dataset_title, "this-is-second-test-dataset-identifier")
        dataset2.save()
        dataset3 = Dataset(dataset_title, "this-is-third-test-dataset-identifier")
        dataset3.save()

        study_title = "Study with dataset children"
        study = Study(study_title, "this-is-a-test-study-identifier")
        study.save()
        study.datasets = [dataset1.id, dataset2.id, dataset3.id]
        study.save()

        project_title = "Project with one Study child"
        project = Project(project_title, "this-is-a-test-project-identifier")
        project.studies = [study.id]
        project.save()
        app.config["_solr_orm"].commit()

        test_study = Study.query.get_or_404("this-is-a-test-study-identifier")
        test_dats_project = dats_exporter.export_dats_entity(test_study)

        self.assertEqual(len(test_dats_project["projectAssets"][0]["output"]), 3)

    def test_validate_exports(self):
        dats_exporter = DATSExporter()

        dataset_title = "Dataset with study and project parents"
        dataset1 = Dataset(dataset_title, "this-is-a-test-dataset-identifier")
        dataset1.data_types = ["Dataset1 type"]
        dataset1.save()
        dataset2 = Dataset(dataset_title, "this-is-second-test-dataset-identifier")
        dataset2.data_types = ["Dataset2 type"]
        dataset2.save()
        study_title = "Study with project parent and dataset child"
        study1 = Study(study_title, "this-is-a-test-study-identifier")
        study1.primary_purpose = "Study1 Name"
        study1.save()
        study1.datasets = [dataset1.id, dataset2.id]
        study1.save()
        study2 = Study(study_title, "this-is-second-test-study-identifier")
        study2.primary_purpose = "Study2 Name"
        study2.save()
        project_title = "Project with study and dataset children"
        project = Project(project_title, "this-is-a-test-project-identifier")
        project.first_name = "DatsExport"
        project.last_name = "Tester"
        project.save()
        project.studies = [study1.id, study2.id]
        project.save()
        app.config["_solr_orm"].commit()

        test_project = Project.query.get_or_404("this-is-a-test-project-identifier")
        test_dats_project = dats_exporter.export_dats_entity(test_project)

        file = None
        try:
            file = tempfile.NamedTemporaryFile(
                mode="w+t", suffix=".json", encoding="utf-8"
            )

            json.dump(test_dats_project, file.file)
            validation = dats_model.validate_project(
                tempfile.gettempdir(),
                file.name,
                test_dats_project,
                0,
            )
            self.assertTrue(validation)

        finally:
            file.close()

    def test_dats_export_filename(self):
        dats_exporter = DATSExporter()
        base_folder = get_resource_path("imi_projects_test")
        dats_projects_connector = DATSConnector(
            base_folder,
            Project,
        )

        projects = list(dats_projects_connector.build_all_entities())
        for project in projects:
            self.assertTrue(
                os.path.exists(
                    f"{base_folder}/{dats_exporter.get_entity_filename(project)}"
                )
            )

    def test_dats_export_from_imported_dats(self):
        self.maxDiff = None
        base_folder = get_resource_path("imi_projects_test")
        dats_exporter = DATSExporter()

        dats_datasets_connector = DATSConnector(
            base_folder,
            Dataset,
        )

        dats_studies_connector = DATSConnector(
            base_folder,
            Study,
        )

        dats_projects_connector = DATSConnector(
            base_folder,
            Project,
        )
        dats_importer = EntitiesImporter(
            [dats_datasets_connector, dats_studies_connector, dats_projects_connector]
        )
        dats_importer.import_all()

        project_num = len(os.listdir(base_folder))
        projects = Project.query.all()
        self.assertEqual(project_num, len(projects))

        for project in projects:
            if (
                project.connector_name
                and project.connector_name.lower() == "datsconnector"
            ):
                dats_exported_entity = dats_exporter.export_dats_entity(project)
                json_path = os.path.join(
                    base_folder,
                    dats_exporter.get_entity_filename(project),
                )

                with open(json_path, "r") as f:
                    imported_data = json.load(f)

                self.assertDictEqual(dats_exported_entity, imported_data)

            else:
                print(
                    f"{project.project_name} not imported with DATSConnector. Skipping..."
                )
                continue

    def tearDown(self):
        app.config["_solr_orm"].delete(query="*:*")
        app.config["_solr_orm"].commit()
