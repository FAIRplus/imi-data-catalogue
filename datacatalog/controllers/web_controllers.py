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
    datacatalog.web_controllers
    -------------------

    HTML endpoints:
        - entities_search
        - search
        - entity_details
        - about
        - request_access
"""
import json
import logging
import re
from typing import List, Tuple

from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
    Response,
    Request,
    send_from_directory,
    jsonify,
    abort,
)
from flask_login import current_user, login_required
from flask_wtf.csrf import CSRFError
from slugify import slugify
from werkzeug.wrappers import response

from .. import login_manager, get_access_handler, app
from ..acces_handler.access_handler import ApplicationState
from ..exceptions import (
    CouldNotCloseApplicationException,
    SolrQueryException,
    AuthenticationException,
    DataCatalogException,
)
from ..exporter.dats_exporter import DATSExporter
from ..pagination import Pagination
from ..solr.facets import Facet
from ..solr.solr_orm_entity import SolrEntity

logger = logging.getLogger(__name__)

RESULTS_PER_PAGE = 5
FAIR_VALUES = app.config.get("FAIR_VALUES")
FAIR_VALUES_SHOW = app.config.get("FAIR_VALUES_SHOW")
FAIR_EVALUATIONS_SHOW = app.config.get("FAIR_EVALUATIONS_SHOW")


def make_key():
    return request.full_path


# errors handlers


@app.errorhandler(CSRFError)
def csrf_error(reason) -> Response:
    logger.warning("CSRF error")
    explanation = "The session might have timed out, try to go back and refresh the page before doing any action"
    return (
        render_template(
            "error.html", message="Error 400 - " + str(reason), explanation=explanation
        ),
        400,
    )


@app.errorhandler(AuthenticationException)
def authentication_errors(reason) -> Response:
    logger.warning("Authentication error %s", reason)
    return (
        render_template(
            "error.html",
            message=f"Authentication Error - {reason.status}",
            explanation=reason,
        ),
        reason.status,
    )


@app.errorhandler(404)
def page_not_found(e) -> Response:
    """
    Customize the 404 pages
    @param e: the exception that triggered the 404
    @type e: Exception
    @return: a custom 404 page
    @rtype:  str
    """
    logger.debug("Page not found", exc_info=e)
    return (
        render_template(
            "error.html", message="Error 404 - Page not found", show_home_link=True
        ),
        404,
    )


@app.errorhandler(500)
def internal_server_error(e) -> Response:
    """
    Customize the 500 pages
    @param e: the exception that triggered the 500
    @type e: Exception
    @return: a custom 500 page
    @rtype:  str
    """
    logger.error("Internal server error", exc_info=e)
    return (
        render_template(
            "error.html",
            message="Error 500 - Internal server error",
            show_home_link=True,
        ),
        500,
    )


@app.route("/<entity_name>s", methods=["GET"])
@app.cache.cached(timeout=0, query_string=True)
def entities_search(entity_name: str) -> Response:
    """
    Generic search endpoint for any entity
    @param entity_name:  the name of the entity we want to browse/search
    @return: html page showing the search results and facets
    """
    try:
        entity_class = app.config["entities"][entity_name]
    except KeyError:
        logger.error("unkown entity name %s", entity_name)
        abort(404)
    logger.debug("entities search for entity name %s", entity_name)
    search_examples = app.config.get("SEARCH_EXAMPLES", {}).get(entity_name)
    exporter = getattr(app, "excel_exporter", None)
    return default_search(
        request,
        exporter=exporter,
        entity=entity_class,
        template="search_" + entity_name + ".html",
        search_examples=search_examples,
    )


@app.route("/", methods=["GET"])
def home() -> Response:
    """
    Search view for default entity, home page
    @return: html page showing the search results and facets for default entity
    """
    no_landing = app.config.get("NO_LANDING", False)
    if no_landing:
        exporter = getattr(app, "excel_exporter", None)
        default_entity = app.config["entities"][
            app.config.get("DEFAULT_ENTITY", "dataset")
        ]
        return default_search(request, exporter=exporter, entity=default_entity)
    else:
        return landing()


def landing():
    entities = app.config["entities"]
    counts_entities = {}
    for entity_name, entity_class in entities.items():
        counts_entities[entity_name] = entity_class.query.count()
    return render_template("landing.html", counts_entities=counts_entities)


@app.route("/search", methods=["GET"])
def search() -> Response:
    """
    Search view for default entity, home page
    @return: html page showing the search results and facets for default entity
    """
    exporter = getattr(app, "excel_exporter", None)
    default_entity = app.config["entities"][app.config.get("DEFAULT_ENTITY", "dataset")]
    return default_search(request, exporter=exporter, entity=default_entity)


def default_search(
    search_request: Request,
    extra_filter: List[str] = None,
    template: str = None,
    facets_order: List[str] = None,
    results_per_page: int = None,
    exporter: object = None,
    entity: SolrEntity = None,
    search_examples: List[str] = None,
) -> Response:
    """
    Compute search results and render the search template
    @param search_request: the flask request object
    @param extra_filter: can be used to apply extra filters on the search, example ['status': 'completed']
    @param template: allows overriding the template used: default is search_`entity_name`.html
    @param facets_order: to override the default facets
    @param results_per_page: number of results per page
    @param exporter: to allow custom exporter (e.g. excel exporter)
    @param entity: the entity class
    :param search_examples: will be showed as queries examples below the search field
    @return: HTML page showing search results
    """
    query = search_request.args.get("query", "").strip()
    searcher = entity.query
    entity_type = searcher.entity_name
    logger.debug("searching entity %s with query %s", entity_type, query)
    if template is None:
        template = "search_" + entity_type + ".html"
    searcher_default_sort, searcher_default_sort_order = searcher.get_default_sort(
        query
    )
    page = search_request.args.get("page", "1").strip()
    sort_by = search_request.args.get("sort_by", searcher_default_sort)
    sort_order = search_request.args.get("order", searcher_default_sort_order)
    export_excel = "export_excel" in search_request.args and exporter

    results_per_page = results_per_page or app.config.get("RESULTS_PER_PAGE", 20)
    sort_options, sort_labels = searcher.get_sort_options()
    try:
        page = int(page)
    except ValueError:
        page = 1
    if (
        page < 1
        or sort_order not in ["asc", "desc"]
        or (sort_by and sort_by not in sort_options)
    ):
        return render_template("error.html", message="wrong parameters"), 400
    if export_excel:
        rows = 100000
        start = 0
    else:
        rows = results_per_page
        start = (page - 1) * results_per_page
    facets_order = facets_order or app.config.get("FACETS_ORDER", {}).get(
        entity_type, []
    )
    # only do facet when some records are present as solr triggers an error if not
    if searcher.count() > 0:
        facets = searcher.get_facets(facets_order)
        for facet in facets.values():
            if facet.field_name in search_request.args:
                values = search_request.args.getlist(facet.field_name)
                facet.set_values(values)
            else:
                facet.use_default()
    else:
        facets = {}
    try:
        fq = None
        if extra_filter:
            fq = [extra_filter]
        if entity_type:
            entity_filter = "type:" + entity_type
            if not fq:
                fq = []
            fq.append(entity_filter)

        results = searcher.search(
            query,
            rows=rows,
            start=start,
            sort=sort_by,
            sort_order=sort_order,
            facets=facets.values(),
            fuzzy=True,
            fq=fq,
        )
    except (NotImplementedError, SolrQueryException) as e:
        logger.error(str(e), exc_info=e)
        return render_template(
            "error.html",
            message="a problem occurred while querying the indexer",
            explanation="see log for more details",
        )

    if export_excel:
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        excel_exporter = exporter()
        return excel_exporter.export_results_as_xlsx(
            entity_type, getattr(results, entity_type + "s")
        )
    pagination = Pagination(page, results_per_page, results.hits)
    ordered_facets = []
    for (attribute_name, label) in facets_order:
        facet = facets.get(attribute_name, None)
        if facet is not None:
            ordered_facets.append(facet)

    return render_template(
        template,
        results=results,
        pagination=pagination,
        sort_options=sort_options,
        sort_labels=sort_labels,
        selected_sort=sort_by,
        sort_order=sort_order,
        facets=ordered_facets,
        fair_values=FAIR_VALUES,
        fair_values_show=FAIR_VALUES_SHOW,
        fair_evaluations_show=FAIR_EVALUATIONS_SHOW,
        search_examples=search_examples,
    )


@app.route("/e/<entity_name>/<entity_id>", methods=["GET"])
@app.cache.cached(timeout=0)
def entity_details(entity_name: str, entity_id: str) -> Response:
    """
    Show the detailed view of a specific entity
    Template used is `entity_name`.html
    @param entity_name: name of the entity class
    @param entity_id: id of the entity
    @return: HTML page
    """
    try:
        values = get_entity_with_facets(entity_name, entity_id)
    except SolrQueryException as e:
        logger.error(str(e), exc_info=e)
        return render_template(
            "error.html",
            message="a problem occurred while querying the indexer",
            explanation="see log for more details",
        )
    if isinstance(values, response.Response):
        return values
    results, facets = values
    entity = results.entities[0]
    entity_class = entity.__class__
    searcher = entity.query
    searcher_default_sort, searcher_default_sort_order = searcher.get_default_sort("")
    available_field_names = [x.field_name for x in facets]
    solr_fields = app.config["_solr_orm"].get_fields_for_class(entity_class)
    facets_base_url = {
        key: url_for(
            "entities_search",
            entity_name=entity_name,
            query="",
            sort_by=searcher_default_sort,
            order=searcher_default_sort_order,
        )
        + f"&{key}="
        if key in available_field_names
        else None
        for key in solr_fields.keys()
    }

    kwargs = {
        entity_name: entity,
        "facets": facets,
        "facets_url": facets_base_url,
        "results": results,
        "has_access": False,
        "attachments_exist": False,
    }

    if hasattr(entity, "contacts"):
        kwargs["contacts"] = [contact.to_json() for contact in entity.contacts or []]

    if app.config.get("PUBLIC_FILE_STORAGE_ROOT"):
        kwargs["attachment_url"] = url_for(
            "api_entity_attachments", entity_name=entity_name, entity_id=entity_id
        )
        kwargs["attachments_exist"] = entity.attachment_exists()

    if current_user.is_authenticated:
        logger.info(
            "User %s visiting entity page %s: %s",
            current_user.id,
            entity_name,
            entity_id,
        )
        handler = get_access_handler(current_user, entity_name)
        if handler and handler.supports_listing_accesses():
            access = handler.has_access(entity)
            logger.info(
                "User %s %s access to %s %s",
                current_user.id,
                "has" if access else "doesn't have",
                entity_id,
                entity_name,
            )
            kwargs["has_access"] = access

    return render_template(
        entity_name + ".html", fair_evaluations_show=FAIR_EVALUATIONS_SHOW, **kwargs
    )


@app.route("/r/<entity_name>/<slug_name>", methods=["GET"])
@app.cache.cached(timeout=0)
def entity_by_slug(entity_name: str, slug_name: str) -> Response:
    try:
        entity_class = app.config["entities"][entity_name]
    except KeyError:
        abort(404)
    entity = entity_class.query.get_by_slug_or_404(slugify(slug_name))
    return redirect(
        url_for("entity_details", entity_name=entity_name, entity_id=entity.id),
        code=301,
    )


def get_entity(entity_name: str, entity_id: str) -> SolrEntity:
    """
    Retrieve an entity from Solr and create an instance of the corresponding Entity
    @param entity_name: name of the entity class
    @param entity_id: id of the entity
    @return: an instance of the corresponding entity or 404 if not found
    """
    try:
        entity_class = app.config["entities"][entity_name]
    except KeyError:
        abort(404)
    entity = entity_class.query.get_or_404(entity_id)
    return entity


def get_entity_with_facets(
    entity_name: str, entity_id: str
) -> Tuple[SolrEntity, List[Facet]]:
    facets_order = app.config.get("FACETS_ORDER", {}).get(entity_name, [])
    try:
        entity_class = app.config["entities"][entity_name]
    except KeyError:
        abort(404)
    searcher = entity_class.query
    # only do facet when some records are present as solr triggers an error if not
    facets = searcher.get_facets(facets_order)
    for facet in facets.values():
        facet.use_default()
    fq = [
        "id:{}_{} or {}_former_ids:{}".format(
            entity_name, entity_id, entity_name, entity_id
        )
    ]
    results = searcher.search(query="", fq=fq, rows=1, facets=facets.values())
    ordered_facets = []
    if len(results.entities) == 0:
        abort(404)
    entity = results.entities[0]
    # check if URL doesn't match current id (using a former id)
    if entity.id != entity_id:
        # in this case, redirect to current id
        return redirect(
            url_for("entity_details", entity_name=entity_name, entity_id=entity.id)
        )
    for (attribute_name, label) in facets_order:
        facet = facets.get(attribute_name, None)
        if facet is not None:
            values = getattr(entity, attribute_name)
            if values:
                facet.set_values(values)
            ordered_facets.append(facet)
    return results, ordered_facets


@app.route("/about", methods=["GET"])
@app.cache.cached(timeout=0)
def about() -> Response:
    """
    Static about page
    @return: HTML page
    """
    return render_template("about.html")


@app.route("/help", methods=["GET"])
@app.cache.cached(timeout=0)
def help() -> Response:
    """
    Static help page
    @return: HTML page
    """
    return render_template("help.html")


@app.route("/e/<entity_name>/<entity_id>/export_dats_entity", methods=["GET"])
def export_dats_entity(entity_name: str, entity_id: str) -> Response:
    try:
        dats_exporter = DATSExporter()
        entity = get_entity(entity_name, entity_id)
        dats_output = dats_exporter.export_dats_entity(entity)
        title = re.sub("[^A-Za-z0-9]+", "_", entity.title)
        filename = title + "_" + entity_name + ".json"
        response = jsonify(dats_output)
        response.headers["Content-Disposition"] = f"attachment;filename={filename}"
        return response
    except Exception as e:
        logger.error(
            "error during dats export of entity %s (%s)",
            entity_id,
            entity_name,
            exc_info=e,
        )
        flash(
            "The export of metadata as DATS is currently not available. Please try again later.",
            category="error",
        )
        return redirect(
            url_for("entity_details", entity_name=entity_name, entity_id=entity_id)
        )


@app.route("/request_access/<entity_name>/<entity_id>", methods=["GET", "POST"])
def request_access(entity_name: str, entity_id: str) -> Response:
    """
    Form to request access to an entity by email
    display the form for a GET request
    send an email and redirects to the home page for a POST request
    @param entity_name: the type of entity we want access to
    @param entity_id: the id of the dataset the user want to request to
    @return: redirects to / or form
    """
    specified_type = request.args.get("type")
    entity = get_entity(entity_name, entity_id)
    title = f"'{entity.title}'"
    url_submit = url_for("request_access", entity_name=entity_name, entity_id=entity_id)
    kwargs = {
        "entity": entity,
        "entity_name": entity_name,
        "entity_id": entity_id,
        "entity_title": title,
        "url_submit": url_submit,
    }
    handler = get_access_handler(current_user, entity_name)
    if not handler:
        logger.error("no access handler found")
        return (
            render_template(
                "error.html",
                message="Error 400 - No compatible request handlers for this entity",
            ),
            400,
        )
    template = handler.template
    logger.info(
        "Using handler %s with template %s", handler.__class__.__name__, template
    )
    if handler.requires_logged_in_user(entity) and not current_user.is_authenticated:
        logger.info("Redirecting user to login")
        here = request.full_path
        redirect_url = url_for("login") + f"?next={here}"
        return redirect(redirect_url), 302

    form = handler.create_form(entity, request.form)
    if form is None:
        logger.error(
            "could not build a form for this request: %s, %s", entity_name, entity_id
        )
        return (
            render_template(
                "error.html",
                message="Error 400 - Could not find a form for this dataset",
                explanation="Check if the datasets have been correctly exported",
            ),
            400,
        )
    if specified_type:
        title += f" - {specified_type}"
        url_submit += f"?type={specified_type}"
    if request.method == "POST":
        if not form.validate():
            if hasattr(form, "recaptcha") and form.recaptcha.errors:
                flash("The Captcha response parameter is missing.", category="error")
            logger.info("invalid form")
            return render_template(template, form=form, **kwargs)
        else:
            if current_user.is_authenticated:
                current_user_id = current_user.id
            else:
                current_user_id = "Anonymous"
            try:
                handler.apply(entity, form)
                logger.info(
                    "access request sent for entity %s (%s) - User %s",
                    entity_id,
                    entity_name,
                    current_user_id,
                )
                flash("Access request sent successfully.", category="success")
                return redirect(url_for("search"))
            except DataCatalogException as e:
                logger.error(
                    "An exception occurred while applying for access for entity %s (%s) - User %s",
                    entity_id,
                    entity_name,
                    current_user_id,
                    exc_info=e,
                )
                return (
                    render_template(
                        "error.html",
                        message="Error 400 - An error occurred while creating access request",
                    ),
                    400,
                )

    elif request.method == "GET":
        return render_template(template, form=form, **kwargs)


@app.route("/static_plugin/<path:filename>")
def custom_static(filename):
    return send_from_directory(app.config["CUSTOM_STATIC_PATH"], filename)


@app.route("/user/my-data-access-requests/<entity_name>")
@login_required
def my_applications(entity_name):
    handler = get_access_handler(current_user, entity_name)
    actions_allowed = handler.ALLOW_USER_ACTIONS
    applications = handler.my_applications()
    entities_with_access = []
    entity_class = app.config["entities"][entity_name]
    for entity_id in current_user.accesses:
        entity = entity_class.query.get(entity_id)
        if entity:
            entities_with_access.append(entity)
    if handler.HIDE_APPROVED:
        # in this case, we remove approved applications from list
        applications = [
            a for a in applications if a.state is not ApplicationState.approved
        ]
    applications = json.dumps(
        [
            {
                "ext_id": a.external_id,
                "dataset": a.entity_title,
                "state": a.state.value,
                "creation_date_string": a.creation_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "entity_url": url_for(
                    "entity_details",
                    entity_id=a.entity_id,
                    entity_name=entity_name,
                ),
            }
            for a in applications
        ]
    )
    return render_template(
        "my_applications.html",
        applications=applications,
        entity_name=entity_name,
        entities_with_access=entities_with_access,
        actions_allowed=actions_allowed,
    )


@app.route(
    "/user/my_applications/<entity_name>/<application_id>/close", methods=["POST"]
)
@login_required
def close_application(entity_name, application_id):
    handler = get_access_handler(current_user, entity_name)
    if not handler.ALLOW_USER_ACTIONS:
        return "forbidden", 403
    try:
        result = handler.close_application(application_id)
    except CouldNotCloseApplicationException as e:
        flash("an error occurred, application was not closed", "error")
        logger.error(
            "Error while closing the application %s for user %s and entity_name %s",
            application_id,
            current_user.id,
            entity_name,
            exc_info=e,
        )
        return str(e), 400
    if result is True:
        logger.info(
            "application %s was closed by user %s", application_id, current_user.id
        )
        flash("application was closed", "success")
        return "ok", 200
    else:
        flash("an error occurred, application was not closed", "error")
        logger.error(
            "Error while closing the application %s for user %s and entity_name %s",
            application_id,
            current_user.id,
            entity_name,
        )
        return "error", 400
