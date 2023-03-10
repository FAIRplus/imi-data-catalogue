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
        - api_entity
        - api_entities
"""
import logging

from flask import jsonify, request, Response
from flask_login import current_user, login_required

from .. import app, csrf, get_access_handler, get_downloads_handler
from ..exceptions import DownloadsHandlerLinksException, AuthenticationException

__author__ = "Valentin Grouès"

logger = logging.getLogger(__name__)


@app.route("/api/<entity_name>/<entity_id>", methods=["GET"])
def api_entity(entity_name: str, entity_id: str) -> Response:
    """
    Returns a json representation of an entity
    @param entity_name: name of the entity class
    @param entity_id: id of the entity
    @return: entity as json
    """
    entity_class = app.config["entities"][entity_name]
    entity = entity_class.query.get_or_404(entity_id)
    return jsonify(**{"data": entity.to_api_dict()})


@app.route("/api/<entity_name>/<entity_id>/attachments", methods=["GET"])
def api_entity_attachments(entity_name: str, entity_id: str) -> Response:
    """
    Returns a json representation of an entity attachment files
    @param entity_name: name of the entity class
    @param entity_id: id of the entity
    @return: list of attachments as a json
    """
    entity_class = app.config["entities"][entity_name]
    entity = entity_class.query.get_or_404(entity_id)
    if entity.attachment_exists():
        return jsonify(**{"data": entity.list_attached_files()})
    else:
        return jsonify(**{"data": []})


@app.route("/api/<entity_name>s", methods=["GET"])
@csrf.exempt
def api_entities(entity_name: str) -> Response:
    """
    Returns a json representation of all instances for a specific entity class
    @param entity_name:name of the entity class
    @return: entities as json
    """
    entity_class = app.config["entities"][entity_name]
    entities = entity_class.query.all()
    return jsonify(**{"data": [entity.to_api_dict() for entity in entities]})


@app.route("/api/downloadLink", methods=["POST"])
@login_required
def download_link() -> Response:
    request_data = request.get_json()
    if not request_data:
        return jsonify({"message": "wrong parameters"}), 400
    entity_id = request_data.get("entityId")
    logger.info(
        "User %s trying to create a download link for entity %s",
        current_user.id,
        entity_id,
    )
    entity_name = app.config.get("DEFAULT_ENTITY", "dataset")
    default_entity = app.config["entities"][entity_name]
    entity = default_entity.query.get(entity_id)
    if entity is None:
        logger.warning("%s %s does not exist", entity_name, entity_id)
        return jsonify({"message": f"{entity_name} not found"}), 404
    handler = get_access_handler(current_user, entity_name)
    if handler and handler.supports_listing_accesses():
        auth = app.config["authentication"]
        try:
            auth.refresh_user(current_user)
        except AuthenticationException as e:
            logger.info("session expired for user %s", current_user.id)
            return jsonify({"message": str(e) + ". Try reloading the page."}), 403
        access = handler.has_access(entity)
        if not access:
            logger.warning("user is not authorized for this %s", entity_name)
            return jsonify({"message": "not authorized"}), 403
        try:
            downloads_handler = get_downloads_handler()
            link = downloads_handler.get_or_create(current_user, entity)
            logger.info(
                "link created for user %s and %s %s: %s",
                current_user.id,
                entity_name,
                entity_id,
                link,
            )
            return jsonify({"data": link})
        except DownloadsHandlerLinksException as e:
            logger.error("error creating the link", exc_info=e)
            return jsonify({"message": "could not create access link"}), 500
    else:
        logger.warning("no handler")
        return jsonify({"message": "no handler"}), 500


@app.route("/api/autocomplete/<entity_name>/<query>", methods=["GET"])
@csrf.exempt
def api_search_autocomplete_entities(entity_name: str, query: str) -> Response:
    """
    Returns a json representation of all instances for a specific entity class
    @param query: search query
    @param entity_name:name of the entity class
    @return: suggested terms as json
    """

    params = {
        "suggest": "true",
        "suggest.build": "true",
        "suggest.dictionary": "suggest_" + entity_name,
        "suggest.q": query,
    }
    results = app.config["_solr_orm"].indexer.search(
        "*:*", search_handler="suggest", **params
    )
    return jsonify(**{"data": results.__dict__})
