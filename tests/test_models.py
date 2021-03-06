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

import os

from base_test import BaseTest
from datacatalog import app
from datacatalog.connector.geostudies_connector import GEOStudiesConnector
from datacatalog.connector.json_connector import JSONConnector
from datacatalog.importer.entities_importer import EntitiesImporter
from datacatalog.models.dataset import Dataset
from datacatalog.models.project import Project
from datacatalog.models.study import Study

__author__ = 'Valentin Grouès'


class TestSolrORM(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.solr_orm = app.config['_solr_orm']
        cls.solr_orm.delete_fields()
        cls.solr_orm.create_fields()

    def test_create_dataset(self):
        self.solr_orm.delete(query='*:*')
        title = "Great dataset!"
        dataset = Dataset(title)
        dataset.save()
        self.solr_orm.commit()
        dataset_id = dataset.id
        created = dataset.created
        retrieved_dataset = Dataset.query.get(dataset_id)
        self.assertEqual(title, retrieved_dataset.title)
        self.assertEqual(created.year, retrieved_dataset.created.year)
        self.assertEqual(created.month, retrieved_dataset.created.month)
        self.assertEqual(created.second, retrieved_dataset.created.second)

    def test_import_dataset(self):
        self.solr_orm.delete(query='*:*')
        connector = [JSONConnector(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'records.json'),
                                   Dataset),
                     GEOStudiesConnector(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'geo_studies_test'))]
        datasets_importer = EntitiesImporter(connector)
        datasets_importer.import_all()
        dataset = Dataset.query.all()
        self.assertEquals(80, len(dataset))

    def test_linked_entities(self):
        study1_title = "study1"
        study1 = Study(study1_title)
        study1.save()
        study2_title = "study2"
        study2 = Study(study2_title)
        study2.save()
        project_title = "project1"
        project = Project(project_title)
        project.save()
        project.studies = [study1.id, study2.id]
        project.save()
        self.solr_orm.commit()
        retrieved_project = Project.query.get(project.id)
        self.assertEqual(project_title, retrieved_project.title)
        self.assertIn(study1.id, project.studies)
        self.assertIn(study2.id, project.studies)
        studies_entities = retrieved_project.studies_entities
        self.assertEqual(2, len(studies_entities))
        self.assertEqual(study1_title, studies_entities[0].title)
        self.assertEqual(study2_title, studies_entities[1].title)

    def tearDown(self):
        app.config['_solr_orm'].delete(query='*:*')
        app.config['_solr_orm'].commit()
