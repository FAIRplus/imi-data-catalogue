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
#
# This program was adapted from the DATS validation scripts authored by agbeltran

__author__ = "Danielle Welter"

import json
import logging
import os
from os import listdir
from os.path import isfile, join

from jsonschema import Draft7Validator

from datacatalog import app
from datsvalidator import datsvalidator

logging.basicConfig(filename="json_validation.log", level=logging.INFO)
logger = logging.getLogger(__name__)
DATS_schemasPath = os.path.join(
    os.path.dirname(__file__), app.config.get("DATS_SCHEMAS_FOLDER")
)
DATS_contextsPath = os.path.join(
    os.path.dirname(__file__), app.config.get("DATS_CONTEXTS_FOLDER")
)


def get_schemas_store(path):
    files = [f for f in listdir(path) if isfile(join(path, f))]
    store = {}
    for schema_filename in files:
        if "json" in schema_filename:
            schema_path = os.path.join(DATS_schemasPath, schema_filename)
            with open(schema_path, "r") as schema_file:
                schema = json.load(schema_file)
                store[schema["$id"]] = schema
    return store


def validate_dataset(path, filename, instance, error_printing):
    return datsvalidator.validate_instance(
        path,
        filename,
        f"{app.config.get('DATS_SCHEMAS_FOLDER')}/dataset_schema.json",
        error_printing,
        instance,
    )


def validate_study(path, filename, instance, error_printing):
    return datsvalidator.validate_instance(
        path,
        filename,
        f"{app.config.get('DATS_SCHEMAS_FOLDER')}/study_schema.json",
        error_printing,
        instance,
    )


def validate_project(path, filename, instance, error_printing):
    return datsvalidator.validate_instance(
        path,
        filename,
        f"{app.config.get('DATS_SCHEMAS_FOLDER')}/project_schema.json",
        error_printing,
        instance,
    )


def validate_schema(path, schemaFile):
    try:
        logger.info("Validating schema %s", schemaFile)
        schema_file = open(join(path, schemaFile))
        schema = json.load(schema_file)
        try:
            Draft7Validator.check_schema(schema)
            return True
        except Exception as e:
            logger.error(e)
            return False
        logger.info("done.")
    finally:
        schema_file.close()


def validate_schemas(path):
    result = True
    files = [f for f in listdir(path) if isfile(join(path, f))]
    for schemaFile in files:
        result = result and validate_schema(path, schemaFile)
    return result


def validate_dats_schemas():
    return validate_schemas(DATS_schemasPath)


def validate_dats_contexts():
    logger.info("Validating contexts at %s", os.path.join(DATS_contextsPath, "sdo"))
    result = validate_schemas(os.path.join(DATS_contextsPath, "sdo"))
    logger.info("Validating contexts at %s", os.path.join(DATS_contextsPath, "obo"))
    result = result and validate_schemas(os.path.join(DATS_contextsPath, "obo"))
    return result
