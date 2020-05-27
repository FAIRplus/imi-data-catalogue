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
    datacatalog.api_controllers
    -------------------

    REST endpoints:
        - api_dataset
        - api_datasets
"""

from flask import abort, jsonify, make_response, request, Response

from .. import app, csrf

__author__ = 'Valentin Grouès'

logger = app.logger


@app.route('/api/<entity_name>/<entity_id>', methods=['GET'])
def api_dataset(entity_name: str, entity_id: str) -> Response:
    """
    Returns a json representation of an entity
    @param entity_name: name of the entity class
    @param entity_id: id of the entity
    @return: entity as json
    """
    entity_class = app.config['entities'][entity_name]
    entity = entity_class.query.get_or_404(entity_id)
    return jsonify(**{"data": entity.to_api_dict()})


@app.route('/api/<entity_name>s', methods=['GET'])
@csrf.exempt
def api_datasets(entity_name: str) -> Response:
    """
    Returns a json representation of all instances for a specific entity class
    Creation of entity from POST request is implemented but not active as POST method is not accepted
    @param entity_name:name of the entity class
    @return: entities as json
    """
    entity_class = app.config['entities'][entity_name]
    if request.method == 'GET':
        entities = entity_class.query.all()
        return jsonify(**{"data": [entity.to_api_dict() for entity in entities]})
    else:
        content_json = request.get_json()
        new_dataset = entity_class.from_json(content_json)
        if request.method == 'POST':
            # check if dataset already exists
            existing_dataset = entity_class.query.get(new_dataset.id)
            if existing_dataset is not None:
                abort(
                    make_response(jsonify(message="a dataset with this id already exists, use PUT method for updates")),
                    400)
        new_dataset.save()
        return jsonify(**{"data": [new_dataset.__dict__]}), 201
