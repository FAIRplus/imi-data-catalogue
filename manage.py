#!/usr/bin/env python

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
    manage.py
    -------------------

   Entry points for CLI operations:
      - test: run the unit tests
      - init_index: initialize the solr index by creating the fields
      - update_index: update the solr index by updating the fields
      - clear_index: delete entities from index
      - commit changes: triggers a solr commit
      - import_entities: import entities into solr

"""
import sys
import unittest

from flask_assets import ManageAssets
from flask_script import Manager, Shell

import requests

from datacatalog import app
from datacatalog.connector.extend_entity_index import EntitiesIndexExtender
from datacatalog.exporter.entities_exporter import EntitiesExporter
from datacatalog.importer.entities_importer import EntitiesImporter
from datacatalog.controllers.sitemap_generator import generate_sitemap

manager = Manager(app)

logger = app.logger


@manager.command
def test():
    """
    Run the unit tests from the tests packages
    """
    tests = unittest.TestLoader().discover("tests", pattern="*.py")
    results = unittest.TextTestRunner(verbosity=1).run(tests)
    if not results.wasSuccessful():
        sys.exit(1)


@manager.command
def init_index():
    """
    Initialize the solr schema by creating the fields defined by the different SolrEntity subclasses
    The fields should not exist before executing this operation.

    Drop any existing field in the schema before running anything else in the init index
        purpose: update index in case of error from check_schema
    """
    solr_orm = app.config["_solr_orm"]
    try:
        if solr_orm.check_fields_existence():
            app.logger.info("Existing fields are being deleted")
            solr_orm.delete_fields()
        solr_orm.create_fields()
        solr_orm.solr_config_update()
    except requests.exceptions.HTTPError as e:
        app.logger.warning(e)


@manager.command
def update_index():
    """
    Update the solr schema by updated the fields defined by the different SolrEntity subclasses
    The fields should already exist before executing this operation.
    """
    solr_orm = app.config["_solr_orm"]
    solr_orm.update_fields()


@manager.command
def clear_index(entity_type):
    """
    Delete all instance of the specified entity type.
    Doesn't trigger a commit but will clear the cache.
    @param entity_type: name of the entity type, e.g. dataset
    """
    solr_orm = app.config["_solr_orm"]
    if entity_type == "all":
        query = "*:*"
    else:
        query = f"type:{entity_type}"
    solr_orm.delete(query=query)
    app.cache.clear()


@manager.command
def commit_changes():
    """
    Triggers a solr commit.
    """
    solr_orm = app.config["_solr_orm"]
    solr_orm.commit()


@manager.command
def import_entities(connector_name, entity_name, sitemap=False):
    """
    Import entities of type entity_name using the connector specified by connector_name
    Doesn't trigger a commit but will clear the cache.
    Checks if the schema exits and if it has been populated
    Checks for type mismatch for each field
    @param connector_name: Short name of the connector to use, e.g. Json. See method get_importer_connector
    @param sitemap: flag dedicated for initiating the sitemap
    @type entity_name: type of the entities to import
    """
    solr_orm = app.config["_solr_orm"]
    if solr_orm.check_schema(entity_name):
        if entity_name not in app.config["entities"]:
            app.logger.error("unknown entity name")
            exit(1)
        entity_class = app.config["entities"][entity_name]
        connector = get_importer_connector(connector_name, entity_class)
        if solr_orm.field_type_mismatch(entity_name):
            app.logger.error("Type mismatch run init_index to fix")
            exit(1)
        if not connector:
            app.logger.error("no known connector found")
            exit(1)
        importer = EntitiesImporter([connector])
        importer.import_all()
        if sitemap:
            generate_sitemaps()
        app.cache.clear()
    else:
        app.logger.error("Please run init_index first! ")
        exit(1)


@manager.command
def extend_entity_index(entity_name):
    if entity_name not in app.config["entities"]:
        app.logger.error("unknown entity name")
        exit(1)
    if entity_name.lower() == "project":
        EntitiesIndexExtender.extend_project_index()
    if entity_name.lower() == "study":
        EntitiesIndexExtender.extend_study_index()
    if entity_name.lower() == "dataset":
        EntitiesIndexExtender.extend_dataset_index()


@manager.command
def export_entities(connector_name, entity_name):
    """
    Import entities of type entity_name using the connector specified by connector_name
    @param connector_name: Short name of the connector to use, e.g. Rems.
    @type entity_name: type of the entities to import
    """
    if entity_name not in app.config["entities"]:
        app.logger.error("unknown entity name")
        exit(1)
    entity_class = app.config["entities"][entity_name]
    from datacatalog.connector.rems_connector import RemsConnector

    connector = RemsConnector(
        api_username=app.config.get("REMS_API_USER"),
        api_key=app.config.get("REMS_API_KEY"),
        host=app.config.get("REMS_URL"),
        form_id=app.config.get("REMS_FORM_ID"),
        workflow_id=app.config.get("REMS_WORKFLOW_ID"),
        organization_id=app.config.get("REMS_ORGANIZATION_ID"),
        licenses=app.config.get("REMS_LICENSES"),
        verify_ssl=app.config.get("REMS_VERIFY_SSL", True),
    )
    if not connector:
        app.logger.error("no known connector found")
        exit(1)
    entities = entity_class.query.all()
    exporter = EntitiesExporter([connector])
    exporter.export_all(entities)


@manager.command
def generate_sitemaps():
    """
    Generates a sitemap with each route for each entity.
    """
    try:
        if generate_sitemap():
            app.logger.info("Sitemap was Generated")
    except FileNotFoundError as e:
        app.logger.error(e)


def get_importer_connector(connector_name, entity_class):
    """
    Returns an instance of the connector corresponding to connector_name
    Will check if the entity_class is compatible with the connector asked.
    @param connector_name: the name of the connector asked
    @param entity_class: The class of the entity we want to index
    @return:  instance or None
    @rtype: DatasetConnector
    """
    connector = None
    importer_extra = app.config.get("IMPORTERS_EXTRA", {}).get(connector_name)
    if connector_name not in entity_class.COMPATIBLE_CONNECTORS:
        app.logger.error("connector and entity name not compatible")
        exit(1)
    elif connector_name == "Ckan":
        from datacatalog.connector.ckan_connector import CKANConnector

        connector = CKANConnector(app.config["CKAN_URL"])
    elif connector_name == "Geo":
        from datacatalog.connector.geostudies_connector import GEOStudiesConnector

        connector = GEOStudiesConnector(
            app.config["GEO_FILE_PATH"][entity_class.__name__.lower()], entity_class
        )
    elif connector_name == "Json":
        from datacatalog.connector.json_connector import JSONConnector

        connector = JSONConnector(
            app.config["JSON_FILE_PATH"][entity_class.__name__.lower()], entity_class
        )
    elif connector_name == "Dats":
        from datacatalog.connector.dats_connector import DATSConnector

        connector = DATSConnector(
            app.config["JSON_FILE_PATH"][entity_class.__name__.lower()], entity_class
        )
    elif connector_name == "Daisy":
        from datacatalog.connector.daisy_connector import DaisyConnector

        connector = DaisyConnector(
            app.config["DAISY_API_URLS"][entity_class.__name__.lower()],
            entity_class,
            verify_ssl=app.config.get("DAISY_VERIFY_SSL", True),
        )
    elif connector_name == "Limesurvey":
        from datacatalog.connector.limesurvey_connector import LimesurveyConnector

        connector = LimesurveyConnector(
            app.config["LIMESURVEY_URL"],
            app.config["LIMESURVEY_USERNAME"],
            app.config["LIMESURVEY_PASSWORD"],
            app.config["LIMESURVEY_SURVEY_ID"],
        )
    elif importer_extra:
        # allow specifying custom importers in settings.py IMPORTERS_EXTRA parameter
        split = importer_extra.split(".")
        importer_class_string_module = ".".join(split[:-1])
        importer_class_string_class = "".join(split[-1:])
        importer_module = __import__(
            importer_class_string_module, fromlist=[importer_class_string_class]
        )
        importer_class = getattr(importer_module, importer_class_string_class)
        connector = importer_class.get_default_instance(entity_class)
    return connector


manager.add_command("shell", Shell(use_ipython=True, use_bpython=True))
# work-around bug in flask-assets
app.jinja_env.assets_environment.environment = app.jinja_env.assets_environment
manager.add_command("assets", ManageAssets(app.jinja_env.assets_environment))
manager.run()
