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
    datacatalog.solr.solr_orm
    -------------------

   Module containing the following classes:
     - SolrORM: update and create solr fields using the solr api
     - SolrQuery: base class to query solr

"""
import json
import logging

from datetime import datetime
from typing import Type, Dict, List, Tuple, Optional, Union

import pysolr
import requests
from flask import Response
from pysolr import Solr, SolrError
from requests import HTTPError
from werkzeug.exceptions import abort

from .facets import Facet, FacetRange
from .solr_orm_entity import DATETIME_FORMAT, DATETIME_FORMAT_NO_MICRO, SolrEntity
from .solr_orm_fields import SolrField, SolrForeignKeyField, SolrJsonField
from .solr_orm_schema import SolrSchemaAdmin
from .. import app
from ..exceptions import SolrQueryException

# suffix added to the query string enable fuzzy search
# fuzzy search tolerance can be configured with FUZZY_SEARCH_LEVEL config parameter
# default is 4

FUZZY_SEARCH_SUFFIX = "~{}".format(app.config.get("FUZZY_SEARCH_LEVEL", 4))

logger = logging.getLogger(__name__)

__author__ = "Valentin Grouès"


class SolrQuery(object):
    """
    Class to handle search and retrieval of entities from Solr
    """

    # The sort options that will be offered on the search page
    SORT_OPTIONS = []
    # The sort options labels that will be offered on the search page
    SORT_LABELS = []
    # default sort option
    DEFAULT_SORT = ""
    # default sort order
    DEFAULT_SORT_ORDER = "asc"
    # allows giving more weight to some fields than others for default search
    BOOST = None

    def __init__(self, class_object: Type[SolrEntity], solr_orm) -> None:
        """
        Initialize a SolrQuery instance setting the SolrEntity class and the SolrORM instance
        @param class_object: SolrEntity class indicating which entity we are searching or retrieving
        @param solr_orm: SolrORM instance holding the solr connection
        """
        self.class_object = class_object
        self.entity_name = class_object.__name__.lower()
        self.solr_orm = solr_orm

    def search_holding_entities(self, target_entity_id, field_name, source_entity_type):
        params = {
            "fq": [
                f'type:"{source_entity_type}"',
                f'{source_entity_type}_{field_name}:"{target_entity_id}"',
            ]
        }
        results = self.solr_orm.indexer.search("*:*", **params)
        entities = []
        for doc in results.docs:
            entity = self._build_instance(doc)
            entities.append(entity)
        results.entities = entities
        return results

    def search(
        self,
        query: str,
        rows: int = 50,
        start: int = 0,
        sort: str = DEFAULT_SORT,
        sort_order: str = "desc",
        fq: List[str] = None,
        facets: List[Facet] = None,
        fuzzy: bool = False,
    ) -> pysolr.Results:
        """
        Execute a solr search
        @param query: solr query string
        @param rows: maximum number of results to return, default to 50
        @param start: used for pagination of the results, default to 0
        @param sort: field to sort on, default to DEFAULT_SORT class attribute
        @param sort_order: sort order, desc or asc, default to desc
        @param fq: list of specific filters to apply.
        See https://lucene.apache.org/solr/guide/8_4/common-query-parameters.html#fq-filter-query-parameter
        @param facets: list of facets to retrieve
        @param fuzzy:boolean triggering fuzzy search to be active or not
        @return: a pysolr.Results instance containing the search results
        """
        if sort_order or sort:
            order = sort_order or "desc"
            if sort:
                sort_with_order = sort + " " + order
            else:
                sort_with_order = "score " + order
        else:
            sort_with_order = ""
        if fq is None:
            fq = []
        params = {
            "sort": sort_with_order,
            "defType": "edismax",
            "qf": self.__class__.BOOST,
            "fq": fq,
        }

        query = query.strip()
        q = "*:*"
        if query:
            if ":" in query:  # for queries like "dataset_disease:*corona*"
                fq.append(query)
            else:
                if fuzzy:
                    fuzzy_terms = "OR {}_textfuzzy_:{}{}".format(
                        self.entity_name, query, FUZZY_SEARCH_SUFFIX
                    )
                    query = "({}_text_:'{}' {})".format(
                        self.entity_name, query, fuzzy_terms
                    )
                else:
                    query = "{}_text_:'{}'".format(
                        self.entity_name, FUZZY_SEARCH_SUFFIX
                    )

                if (
                    "score" in sort_with_order
                ):  # If sort has 'score' add to “scoring” query 'q'
                    q = query
                else:
                    fq.append(query)
        if rows:
            params["rows"] = rows
        if start:
            params["start"] = start

        if facets:
            params["facet"] = "on"
            params["facet.field"] = []
            params["facet.range"] = []
            for facet in facets:
                if isinstance(facet, FacetRange):
                    params[
                        "f.{}_{}.facet.range.start".format(
                            self.entity_name, facet.field_name
                        )
                    ] = facet.range.start
                    params[
                        "f.{}_{}.facet.range.end".format(
                            self.entity_name, facet.field_name
                        )
                    ] = facet.range.end
                    params[
                        "f.{}_{}.facet.range.gap".format(
                            self.entity_name, facet.field_name
                        )
                    ] = facet.range.gap
                    params[
                        "f.{}_{}.facet.range.other".format(
                            self.entity_name, facet.field_name
                        )
                    ] = facet.range.other
                    params["facet.range"].append(self.entity_name, facet.field_name)
                    for value in facet.values:
                        fq.append(
                            "{}_{}:{}".format(self.entity_name, facet.field_name, value)
                        )
                else:
                    for value in facet.values:
                        value = value.replace('"', '\\"')
                        fq.append(
                            '{}_{}:"{}"'.format(
                                self.entity_name, facet.field_name, value
                            )
                        )
                    params["facet.field"].append(
                        "{}_{}".format(self.entity_name, facet.field_name)
                    )
        try:
            results = self.solr_orm.indexer.search(q, **params)
            entities = []
            for doc in results.docs:
                entity = self._build_instance(doc)
                entities.append(entity)
            results.entities = entities
            # replace facets fields name to remove prefix
            facet_fields = results.facets.get("facet_fields")
            new_facets_fields = {}
            if facet_fields:
                for field_name, facet_value in facet_fields.items():
                    start_index = len(self.entity_name + "_")
                    new_facets_fields[field_name[start_index:]] = facet_value
                results.facets["facet_fields"] = new_facets_fields
        except SolrError as e:
            raise SolrQueryException(e)
        return results

    def get_default_sort(self, query: str) -> Tuple[str, str]:
        """
        For a given query, return the default
        sort attribute and order as a tuple.
        If query is not empty, we want to sort by sort by relevance
         of the search results, descending order.
        If query is empty, sort by default sort attribute (self.DEFAULT_SORT)
        @param query: query string
        @return: sort attribute and order
        """
        if query:
            return "", "desc"
        else:
            return self.entity_name + "_" + self.DEFAULT_SORT, self.DEFAULT_SORT_ORDER

    def get_facets(self, facet_list: List[Tuple[str, str]]) -> List[Facet]:
        """
        Build a list of Facet instances from a list of attributes and facet labels
        @param facet_list: a list containing tuples with field name and facet label
        @return: list of Facet instances
        """
        facets = {}
        for (attribute_name, label) in facet_list:
            solr_field = self.class_object._solr_fields.get(attribute_name, None)
            if solr_field is not None:
                facets[attribute_name] = Facet(solr_field.name, label)
        return facets

    def get_sort_options(self) -> Tuple[List[str], List[str]]:
        """
        Returns a tuple where the first element is the list of sorting options and the second element
        is a list of the corresponding labels
        @return: tuple
        """
        options = self.SORT_OPTIONS
        prefix = self.class_object.__name__.lower()
        options_with_prefix = [
            prefix + "_" + option if option != "id" else "id" for option in options
        ]
        return options_with_prefix, getattr(self, "SORT_LABELS", [])

    def get(self, entity_id: str) -> Optional[SolrEntity]:
        """
        Retrieve from solr and build a SolrEntity instance for a given entity id
        @param entity_id: id of the entity to retrieve from solr
        @return: a self.class_object instance or None if not found
        """
        results = self.solr_orm.indexer.search(
            q='id:"{}_{}"'.format(self.entity_name, entity_id), rows=1
        )
        if results.hits == 0:
            return None
        doc = results.docs[0]
        new_instance = self._build_instance(doc)
        return new_instance

    def get_by_slug(self, slug: str) -> Optional[SolrEntity]:
        """
        Retrieve from solr and build a SolrEntity instance for a given entity slug
        @param slug: slug of the entity to retrieve from solr
        @return: a self.class_object instance or None if not found
        """

        results = self.solr_orm.indexer.search(
            q='{}_slugs:"{}"'.format(self.entity_name, slug), rows=1
        )
        if results.hits == 0:
            return None
        doc = results.docs[0]
        new_instance = self._build_instance(doc)
        return new_instance

    def get_by_slug_or_404(self, slug: str) -> Union[SolrEntity, Response]:
        """
        Similar as get_by_slug method but returns a 404 page if entity not found
        @param slug: slug of the entity to retrieve from solr
        @return: a self.class_object instance or a 404 response if not found
        """
        new_instance = self.get_by_slug(slug)
        if new_instance is None:
            abort(404)
        return new_instance

    def _build_instance(self, doc):
        new_instance = self.class_object()
        for attribute_name, field in self.class_object._solr_fields.items():
            solr_value = doc.get(self.entity_name + "_" + field.name, None)
            if solr_value is not None and field.type == "pdate":
                try:
                    solr_value = datetime.strptime(solr_value, DATETIME_FORMAT)
                except ValueError:
                    solr_value = datetime.strptime(solr_value, DATETIME_FORMAT_NO_MICRO)
            elif solr_value is not None and isinstance(field, SolrJsonField):
                if field.model:
                    for count, value in enumerate(solr_value):
                        data = json.loads(value)
                        solr_value[count] = field.model.from_json(data)
                else:
                    solr_value = json.loads(solr_value)
            setattr(new_instance, attribute_name, solr_value)
        doc_id = doc.get("id", None)
        # remove prefix from id (entity_name_)
        if doc_id:
            start_index = len(self.entity_name) + 1
            doc_id = doc_id[start_index:]
        setattr(new_instance, "id", doc_id)
        return new_instance

    def get_or_404(self, entity_id: str) -> Union[SolrEntity, Response]:
        """
        Similar as get method but returns a 404 page if entity not found
        @param entity_id: id of the entity to retrieve from solr
        @return: a self.class_object instance or a 404 response if not found
        """
        new_instance = self.get(entity_id)
        if new_instance is None:
            abort(404)
        return new_instance

    def count(self) -> int:
        """
        Total number of entities from solr
        @return: total count of entities as an integer
        """
        results = self.solr_orm.indexer.search(
            q="type:" + self.entity_name, fl="numFound"
        )
        return results.hits

    def all(self) -> List[SolrEntity]:
        """
        Retrieve from solr all the entities of the underlying SolrEntity as defined by self.class_object
        @return: a list of solr entities
        """
        # TODO, use pagination and yield results
        results = self.solr_orm.indexer.search(
            q="type:" + self.entity_name, rows=1000000
        )
        instances = []
        for result in results:
            instances.append(self._build_instance(result))
        return instances

    def all_ids(self) -> List[SolrEntity]:
        """
        Retrieve from solr all the entities  ids of the underlying SolrEntity as defined by self.class_object
        @return: a list of solr entities
        """
        results = self.solr_orm.indexer.search(
            q="type:" + self.entity_name, fl="id", rows=1000000
        )
        start_index = len(self.entity_name) + 1
        return [r["id"][start_index:] for r in results.docs]


class SolrAutomaticQuery(SolrQuery):
    def __init__(self, class_object: Type[SolrEntity], solr_orm) -> None:
        """
        Initialize a SolrQuery instance setting the SolrEntity class and the SolrORM instance
        @param class_object: SolrEntity class indicating which entity we are searching or retrieving
        @param solr_orm: SolrORM instance holding the solr connection
        """
        super().__init__(class_object, solr_orm)
        self.entity_name = class_object.__name__.lower()
        if not self.__class__.SORT_OPTIONS:
            self.__class__.SORT_OPTIONS = ["title", "id"]
        # labels of the sort options that will be offered on the search page
        if not self.__class__.SORT_LABELS:
            self.__class__.SORT_LABELS = ["title", "id"]
        # allows giving more weight to some fields than others for default search
        if not self.__class__.BOOST:
            boosts = app.config.get("SOLR_BOOST", {})
            boost = boosts.get(self.entity_name)
            self.__class__.BOOST = (
                boost or f"{self.entity_name}_title^5 {self.entity_name}_text_^1"
            )
        # default sort option
        if not self.__class__.DEFAULT_SORT:
            default_sorts = app.config.get("SOLR_DEFAULT_SORT", {})
            default_sort = default_sorts.get(self.entity_name)
            self.__class__.DEFAULT_SORT = default_sort or "title"


class SolrORM(object):
    """
    Class abstracting access to solr api to create, update and delete solr fields
    """

    # default field to use for default search
    DEFAULT_QUERY_FIELDS = ["title"]

    def __init__(self, url: str, collection: str) -> None:
        """
        Initialize a SolrORM instance with the solr url and solr collection to use
        @param url: hostname and port of a solr instance
        @param collection: solr core
        """
        self.url = url
        self.collection = collection
        self.indexer = Solr("{}/{}".format(url, collection))
        self.indexer_schema = SolrSchemaAdmin(
            "{}/{}/schema".format(self.url, collection)
        )
        logger.info(
            "Initializing SolrORM with solr url %s and collection %s", url, collection
        )

        SolrEntity._solr_orm = self

        # we loop over solr entity subclasses to set some internal variables
        # for each solrEntity subclass, _solr_fields will contain a list of solr fields
        # query will contain a SolrQuery instance or one of its subclasses instance as defined in the  query_class
        # attribute of each solrEntity subclass
        for entity_class in SolrEntity.__subclasses__():
            entity_class.reversed_field = {}
        for entity_class in SolrEntity.__subclasses__():
            if not hasattr(entity_class, "_solr_fields"):
                entity_class._solr_fields = self.get_fields_for_class(entity_class)
            for field in entity_class._solr_fields.values():
                # we record of solrforeignkeyfield having reversed_by attributes in the target entity
                if isinstance(field, SolrForeignKeyField) and field.reversed_by:
                    reversed_attributes = field.reversed_by
                    target_entity_class = app.config["entities"].get(
                        field.linked_entity_name
                    )
                    if target_entity_class:
                        source_entity_class_name = entity_class.__name__.lower()
                        target_entity_class.reversed_field[reversed_attributes] = (
                            source_entity_class_name,
                            field.name,
                            field.reversed_multiple,
                        )

            if hasattr(entity_class, "query_class"):
                entity_class.query = entity_class.query_class(entity_class, self)
            else:
                entity_class.query = SolrQuery(entity_class, self)
        pass

    def check_schema(self, entity_name: str) -> bool:
        """
        Check for missing fields for each entity
        """
        try:
            entity_class = app.config["entities"][entity_name.lower()]
            if entity_class.__name__.lower() == entity_name.lower() and hasattr(
                entity_class, "_solr_fields"
            ):
                fields = entity_class._solr_fields
                for field in fields.values():
                    ret = requests.get(
                        f"{self.indexer_schema.url}/fields/{entity_name.lower()}_{field.name}"
                    )
                    if not ret.ok:
                        logger.error(
                            "The field %s is required.",
                            field.name,
                        )
                        return False
                return True
        except KeyError as e:
            logger.error(e)

    def check_fields_existence(self) -> bool:
        """
        Checks if there is any existing field within schema
        Runs on init_index where it initiates the delete
        function in case of there being any
        existing field
        """

        def get_field(field_name: str) -> str:
            for entity_name in app.config["entities"].keys():
                if field_name.startswith(entity_name):
                    return field_name

        ret = requests.get(self.indexer_schema.url + "/fields")
        for field in ret.json()["fields"]:
            if get_field(field["name"]):
                return True

    def field_type_mismatch(self, entity_name: str) -> bool:
        for field in app.config["entities"].get(entity_name)._solr_fields.values():
            ret = requests.get(
                f"{self.indexer_schema.url}/fields/{entity_name.lower()}_{field.name}"
            )
            return ret.json()["field"]["type"] != field.type

    def create_fields(self):
        """
        We loop over solr entity subclasses to create the corresponding fields
        """
        logger.info("Creating solr fields")
        self._create_or_update_fields(update=False)

    def update_fields(self):
        """
        We loop over solr entity subclasses to update the corresponding fields
        """
        logger.info("Updating solr fields")
        self._create_or_update_fields(update=True)

    def delete_fields(self):
        """
        We loop over solr entity subclasses to delete the corresponding fields
        """
        # get subclasses
        logger.info("Deleting solr fields")
        for solr_entity_class in SolrEntity.__subclasses__():
            # fields = self.get_fields_for_class(solr_entity_class)
            if not hasattr(solr_entity_class, "_solr_fields"):
                solr_entity_class._solr_fields = self.get_fields_for_class(
                    solr_entity_class
                )
            self._delete_fields_for_class(solr_entity_class)
        try:
            self.indexer_schema.delete_field("type")
        except HTTPError as e:
            logger.debug(e)

    def _create_or_update_fields(self, update=False):
        # get subclasses
        if not update:
            self.indexer_schema.create_field(
                "type", "string", index=True, store=True, multivalued=False
            )
        for solr_entity_class in app.config["entities"].values():
            logger.debug(solr_entity_class)
            # fields = self.get_fields_for_class(solr_entity_class)
            if not hasattr(solr_entity_class, "_solr_fields"):
                solr_entity_class._solr_fields = self.get_fields_for_class(
                    solr_entity_class
                )
            self._create_or_update_fields_for_class(solr_entity_class, update)
        # self.indexer_schema.update_field("_text_", "text_en", index=True, store=False, multivalued=True)
        # self.indexer_schema.update_field("_textfuzzy_", "text_en_splitting_tight", index=True, store=False,
        #                                 multivalued=True)
        logger.debug("done")

    def get_fields_for_class(
        self, solr_entity_class: Type[SolrEntity]
    ) -> Dict[str, SolrField]:
        """
        For a specific SolrEntity subclass, returns a dict where keys are
        the attributes names and values are the SolrField instances
        @param solr_entity_class: SolrEntity subclass
        @return: the dict with attributes and corresponding solr fields
        """
        attributes = dict()
        self._find_fields(solr_entity_class, attributes)
        return attributes

    def _find_fields(self, solr_entity_class, attributes):
        for name, value in solr_entity_class.__dict__.items():
            if isinstance(value, SolrField):
                attributes[name] = value
        for superclass in solr_entity_class.__bases__:
            if superclass != object:
                self._find_fields(superclass, attributes)

    def _create_or_update_fields_for_class(self, solr_entity_class, update):
        fields = solr_entity_class._solr_fields
        entity_name = solr_entity_class.__name__.lower()
        solr_query_fields = app.config.get("SOLR_QUERY_TEXT_FIELD", {}).get(entity_name)
        if not solr_query_fields:
            solr_query_fields = self.DEFAULT_QUERY_FIELDS

        for field in fields.values():
            if update:
                self.indexer_schema.update_field(
                    entity_name + "_" + field.name,
                    field.type,
                    field.indexed,
                    field.stored,
                    field.multivalued,
                )
            else:
                self.indexer_schema.create_field(
                    entity_name + "_" + field.name,
                    field.type,
                    field.indexed,
                    field.stored,
                    field.multivalued,
                )
        try:
            headers = {"Content-type": "application/json", "Content-Type": "text/xml"}
            params = {"commit": "true", "indent": "true"}

            data = {"delete-field": {"name": entity_name + "_text_"}}
            requests.post(
                self.indexer_schema.url,
                headers=headers,
                data=json.dumps(data),
                params=params,
            )
            data = {"delete-field": {"name": entity_name + "_textfuzzy_"}}

            requests.post(
                self.indexer_schema.url,
                headers=headers,
                data=json.dumps(data),
                params=params,
            )

            # Adding the Text field if it does not exists

            data_add_copyfield = {
                "add-field": {
                    "name": entity_name + "_text_",
                    "type": "text_en",
                    "indexed": "true",
                    "multiValued": "true",
                    "stored": "false",
                }
            }
            response_add_copyfield = requests.post(
                self.indexer_schema.url,
                headers=headers,
                data=json.dumps(data_add_copyfield),
                params=params,
            )
            data_add_copyfield2 = {
                "add-field": {
                    "name": entity_name + "_textfuzzy_",
                    "type": "text_en_splitting_tight",
                    "indexed": "true",
                    "multiValued": "true",
                    "stored": "false",
                }
            }
            response_add_copyfield2 = requests.post(
                self.indexer_schema.url,
                headers=headers,
                data=json.dumps(data_add_copyfield2),
                params=params,
            )

            data_add_fieldtype = {
                "add-field-type": {
                    "name": "autocomplete_text",
                    "class": "solr.TextField",
                    "positionIncrementGap": "100",
                    "analyzer": {
                        "tokenizer": {"class": "solr.KeywordTokenizerFactory"},
                        "filters": [{"class": "solr.LowerCaseFilterFactory"}],
                    },
                }
            }
            requests.post(
                self.indexer_schema.url,
                headers=headers,
                data=json.dumps(data_add_fieldtype),
                params=params,
            )

            data_add_copyfield3 = {
                "add-field": {
                    "name": entity_name + "_autocomplete_text_",
                    "type": "autocomplete_text",
                    "indexed": "true",
                    "multiValued": "true",
                    "stored": "false",
                }
            }
            response_add_copyfield3 = requests.post(
                self.indexer_schema.url,
                headers=headers,
                data=json.dumps(data_add_copyfield3),
                params=params,
            )

            # if the text field exists but have copy fields attached. Deleting all the copy fields
            if not response_add_copyfield.status_code == 200:
                for source in solr_query_fields:
                    data_delete_copyfield = {
                        "delete-copy-field": {
                            "source": entity_name + "_" + source,
                            "dest": entity_name + "_text_",
                        }
                    }
                    requests.post(
                        self.indexer_schema.url,
                        headers=headers,
                        params=params,
                        data=json.dumps(data_delete_copyfield),
                    )

            if not response_add_copyfield2.status_code == 200:
                for source in solr_query_fields:
                    data_delete_copyfield2 = {
                        "delete-copy-field": {
                            "source": entity_name + "_" + source,
                            "dest": entity_name + "_textfuzzy_",
                        }
                    }
                    requests.post(
                        self.indexer_schema.url,
                        headers=headers,
                        params=params,
                        data=json.dumps(data_delete_copyfield2),
                    )

            if not response_add_copyfield3.status_code == 200:
                for source in solr_query_fields:
                    data_delete_copyfield3 = {
                        "delete-copy-field": {
                            "source": entity_name + "_" + source,
                            "dest": entity_name + "_autocomplete_text_",
                        }
                    }
                    requests.post(
                        self.indexer_schema.url,
                        headers=headers,
                        params=params,
                        data=json.dumps(data_delete_copyfield3),
                    )

            # recreating all the copy fields with _text_ and _textfuzzy_ as dest field
            for source in solr_query_fields:
                data_create_copyfield = {
                    "add-copy-field": {
                        "source": entity_name + "_" + source,
                        "dest": entity_name + "_text_",
                    }
                }
                requests.post(
                    self.indexer_schema.url,
                    headers=headers,
                    params=params,
                    data=json.dumps(data_create_copyfield),
                )
                data_create_copyfield2 = {
                    "add-copy-field": {
                        "source": entity_name + "_" + source,
                        "dest": entity_name + "_textfuzzy_",
                    }
                }
                requests.post(
                    self.indexer_schema.url,
                    headers=headers,
                    params=params,
                    data=json.dumps(data_create_copyfield2),
                )

                data_create_copyfield3 = {
                    "add-copy-field": {
                        "source": entity_name + "_" + source,
                        "dest": entity_name + "_autocomplete_text_",
                    }
                }
                requests.post(
                    self.indexer_schema.url,
                    headers=headers,
                    params=params,
                    data=json.dumps(data_create_copyfield3),
                )

        except requests.exceptions.HTTPError as e:
            print(e)

    def add(self, entity_dict: dict) -> str:
        """
        Add an entity to the solr index
        Beware that this method doesn't trigger a commit
        @param entity_dict: a representation of a SolrEntity as a dict
        @return: a string containing the response body from solr
        """
        return self.indexer.add([entity_dict])

    def delete(self, entity_id: str = None, query: SolrQuery = None) -> str:
        """
        Delete an entity from the solr index
        Beware that this method doesn't trigger a commit
        @param entity_id: id of the SolrEntity to delete
        @return: a string containing the response body from solr
        """
        if entity_id is not None:
            query = None
        return self.indexer.delete(id=entity_id, q=query)

    def commit(self, soft_commit: bool = False) -> str:
        """
        Triggers a solr commit
        @param soft_commit: if true, only a soft commit will be triggered
        @return: a string containing the response body from solr
        """
        logger.debug("Solr commit")
        return self.indexer.commit(softCommit=soft_commit)

    def _delete_fields_for_class(self, entity_class):
        fields = entity_class._solr_fields
        entity_name = entity_class.__name__.lower()
        solr_query_fields = app.config.get("SOLR_QUERY_TEXT_FIELD", {}).get(entity_name)
        if not solr_query_fields:
            solr_query_fields = self.DEFAULT_QUERY_FIELDS
        headers = {"Content-type": "application/json", "Content-Type": "text/xml"}
        params = {"commit": "true", "indent": "true"}
        for source in solr_query_fields:
            logger.debug("deleting copy field for %s", source)
            data_delete_copyfield = {
                "delete-copy-field": [
                    {
                        "source": entity_name + "_" + source,
                        "dest": entity_name + "_text_",
                    },
                    {
                        "source": entity_name + "_" + source,
                        "dest": entity_name + "_textfuzzy_",
                    },
                    {
                        "source": entity_name + "_" + source,
                        "dest": entity_name + "_autocomplete_text_",
                    },
                ]
            }
            ret = requests.post(
                self.indexer_schema.url,
                headers=headers,
                params=params,
                data=json.dumps(data_delete_copyfield),
            )

            if not ret.ok:
                logger.debug(ret.content)
        data = {
            "delete-field": [
                {"name": entity_name + "_text_"},
                {"name": entity_name + "_textfuzzy_"},
                {"name": entity_name + "_autocomplete_text_"},
            ]
        }
        requests.post(
            self.indexer_schema.url,
            headers=headers,
            data=json.dumps(data),
            params=params,
        )

        for field in fields.values():
            try:
                self.indexer_schema.delete_field(entity_name + "_" + field.name)
            except HTTPError as e:
                logger.warning("error deleting field %s", field.name, exc_info=e)

    def solr_config_update(self):
        headers = {"Content-type": "application/json"}
        params = {"commit": "true", "indent": "true"}

        suggesters = []
        for entity_name in app.config.get("entities").keys():
            suggesters.append(
                {
                    "name": f"suggest_{entity_name}",
                    "lookupImpl": "AnalyzingInfixLookupFactory",
                    "field": f"{entity_name}_autocomplete_text_",
                    "suggestAnalyzerFieldType": "autocomplete_text",
                    "buildOnStartup": "false",
                    "highlight": "false",
                }
            )
        search_component = {
            "name": "suggest",
            "class": "solr.SuggestComponent",
            "suggester": suggesters,
        }

        request_handler = {
            "name": "/suggest",
            "class": "solr.SearchHandler",
            "startup": "lazy",
            "defaults": {"suggest": "true", "suggest.count": 10},
            "components": ["suggest"],
        }

        data_add_searchcomponent = {"add-searchcomponent": search_component}

        data_add_requesthandler = {"add-requesthandler": request_handler}
        response_add_search_component = requests.post(
            self.url + "/" + self.collection + "/config",
            headers=headers,
            params=params,
            data=json.dumps(data_add_searchcomponent),
        )
        response_add_request_handler = requests.post(
            self.url + "/" + self.collection + "/config",
            headers=headers,
            params=params,
            data=json.dumps(data_add_requesthandler),
        )

        # if the component already exists do an update
        if not response_add_search_component.status_code == 200:
            data_update_search_component = {"update-searchcomponent": search_component}
            requests.post(
                self.url + "/" + self.collection + "/config",
                headers=headers,
                params=params,
                data=json.dumps(data_update_search_component),
            )

        if not response_add_request_handler.status_code == 200:
            data_update_request_handler = {"update-requesthandler": request_handler}
            requests.post(
                self.url + "/" + self.collection + "/config",
                headers=headers,
                params=params,
                data=json.dumps(data_update_request_handler),
            )
