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
    datacatalog.sitemap_generator
    -------------------

    Generate Sitemap
"""
import logging
import os
from typing import Type

import flask.wrappers
from flask import url_for, render_template, make_response

from datacatalog.solr.solr_orm_entity import SolrEntity
from .. import app

__author__ = "Abetare Shabani"

logger = logging.getLogger(__name__)


@app.route("/robots.txt", methods=["GET"])
def generate_robots() -> flask.wrappers.Response:
    """
    Generates robots.txt that tells search engine crawlers which URLs the crawler can
    access on our site.
    @return: flask.wrappers.Response
    """
    default_black_listed = {
        "*": [
            "develop",
            "logout",
            "login",
            "search",
            "user",
            "pyoidc",
            "static",
            "autocomplete",
            "r/",
        ]
    }
    scheme = app.config.get("SCHEME", "http")
    robots_template = render_template(
        "robots.html",
        black_list=app.config.get("ROBOTS_BLACK_LISTED", default_black_listed),
        sitemap=url_for(
            "static", filename="public/sitemap.xml", _external=True, _scheme=scheme
        ),
    )
    response = make_response(robots_template)
    response.headers["Content-type"] = "text/plain"
    return response


def generate_sitemap() -> str:
    """
    Generate dynamically a sitemap for all the url that have GET as their method and
    do not include any authentication identifier.
    lastmod and priority tags omitted on static pages.
    lastmod included on dynamic content such as studies, project, and dataset.
    @return: str
    """
    host_base = app.config["BASE_URL"]

    # Static routes with static content
    static_urls = list()
    # Dynamic routes with dynamic content
    dynamic_urls = list()
    black_listed_urls = ["/user", "pyoidc", "static", "autocomplete", "/r/"]
    for rule in app.url_map.iter_rules():
        _url = str(rule)
        # avoid all rules that are part of the black_listed_urls
        if all(x not in _url for x in black_listed_urls):
            # list all url that have GET as their method with no arguments
            # these urls are counted as static urls where their body does not change

            if "GET" in rule.methods and len(rule.arguments) == 0:
                url = {"loc": f"{host_base}{_url}"}
                static_urls.append(url)

            # list all dynamic url with GET as their method that
            # have one or more than one argument
            elif "GET" in rule.methods and rule.arguments != 0:
                dynamic_urls.extend(get_dynamic_url(rule, host_base))
    return write_sitemap(static_urls, dynamic_urls)


def write_sitemap(static_urls: list, dynamic_urls: list) -> str:
    """
    Write data into file.
    @param static_urls: list of static pages
    @param dynamic_urls: list of dynamic content
    @param filepath: the name of the file to write the sitemap
    @return: str
    """
    try:
        xml_sitemap = render_template(
            "sitemap.xml",
            static_urls=static_urls,
            dynamic_urls=dynamic_urls,
        )
        filepath = os.path.join(
            os.path.dirname(__file__), "../static/public/sitemap.xml"
        )
        with open(filepath, "wt") as f:
            for line in xml_sitemap:
                f.write(line)
        return xml_sitemap
    except FileNotFoundError as e:
        return e


def get_dynamic_url(rule, host_base: str) -> list:
    """
    Gets the url for pages with dynamic content
    @param rule: url
    @param host_base: origin url
    @return: list - of all url from dynamic content
    """

    dynamic_urls = list()
    for entity_name, entity_class in app.config["entities"].items():
        if len(rule.arguments) == 1:
            dynamic_urls.extend(get_single_arg_url(rule, entity_class, host_base))
        elif len(rule.arguments) > 1:
            # urls with request_access as endpoint are only listed if dataset is datasets
            if "request_access" not in rule.endpoint:
                dynamic_urls.extend(get_multi_arg_url(rule, entity_class, host_base))
            else:
                if entity_name == "dataset":
                    dynamic_urls.extend(
                        get_multi_arg_url(rule, entity_class, host_base)
                    )
    return dynamic_urls


def get_single_arg_url(rule, entity_class: Type[SolrEntity], host_base: str) -> list:
    """
    Returns all urls which have one single argument
    @param rule: the current url the search is performed for
    @param entity_class: type of entity: study, dataset, project...
    @param host_base: origin url
    @return: list
    """

    dynamic_urls = list()
    _url = ""
    if "entity_name" in rule.arguments:
        _url = url_for(rule.endpoint, entity_name=entity_class.__name__.lower())
    url = {
        "loc": f"{host_base}{_url}",
    }
    dynamic_urls.append(url)
    return dynamic_urls


def get_multi_arg_url(rule, entity_class: Type[SolrEntity], host_base: str) -> list:
    """
    Returns all the urls which contain dynamic content and
    include more than one argument
    @param rule: the current url the search is being performed on
    @param entity_class: type of entity - study, dataset, project...
    @param host_base: origin url
    @return: list
    """
    entities = entity_class.query.all()
    dynamic_urls = list()
    for entity in entities:
        _url_ = ""
        if "entity_name" and "entity_id" in rule.arguments:
            _url_ = url_for(
                rule.endpoint,
                entity_name=entity_class.__name__.lower(),
                entity_id=entity.id,
            )
        date = entity.modified
        url = {
            "loc": f"{host_base}{_url_}",
            "lastmod": f"{date:%Y-%m-%d}",
        }
        dynamic_urls.append(url)
    return dynamic_urls
