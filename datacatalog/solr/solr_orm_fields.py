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
    datacatalog.solr.solr_orm_fields
    -------------------

   Module containing the SolrField class and subclasses for different fields type

"""
import logging

from typing import Optional

logger = logging.getLogger(__name__)


class SolrField:
    """
    Class holding the solr field definition:
        - indexed: should the field be indexed by solr to allow search
        - stored: should the original field value be stored in solr to allow value retrieval
        - name: field name, can contain only alphanumeric characters and _
        - field_type: field type, see solr documentation for list of types, default type is string
        - multivalued: can the field contain multiple values (list)
    """

    def __init__(self, name: str, attribute_name: Optional[str] = None, field_type: str = "string",
                 indexed: bool = True, stored: bool = True,
                 multivalued: object = False) -> None:
        self.multivalued = multivalued
        self.indexed = indexed
        self.stored = stored
        self.name = name
        self.type = field_type
        self.attribute_name = attribute_name or name


class SolrCaseInsensitiveStringField(SolrField):
    """
    SolrField subclass setting solr type to lowercase
    """

    def __init__(self, name: str, attribute_name: Optional[str] = None, indexed: bool = True, stored: bool = True,
                 multivalued: bool = False) -> None:
        super().__init__(name, attribute_name, "lowercase", indexed, stored, multivalued)


class SolrDateTimeField(SolrField):
    """
    SolrField subclass setting solr type to pdate
    """

    def __init__(self, name: str, attribute_name: Optional[str] = None, indexed: bool = True, stored: bool = True,
                 multivalued: bool = False) -> None:
        if multivalued:
            super().__init__(name, attribute_name, "pdates", indexed, stored, multivalued)
        else:
            super().__init__(name, attribute_name, "pdate", indexed, stored, multivalued)


class SolrLongField(SolrField):
    """
    SolrField subclass setting solr type to plong
    """

    def __init__(self, name: str, attribute_name: Optional[str] = None, indexed: bool = True, stored: bool = True,
                 multivalued: bool = False) -> None:
        if multivalued:
            super().__init__(name, attribute_name, "plongs", indexed, stored, multivalued)
        else:
            super().__init__(name, attribute_name, "plong", indexed, stored, multivalued)


class SolrFloatField(SolrField):
    """
    SolrField subclass setting solr type to pfloat
    """

    def __init__(self, name: str, attribute_name: Optional[str] = None, indexed: bool = True, stored: bool = True,
                 multivalued: bool = False) -> None:
        if multivalued:
            super().__init__(name, attribute_name, "pfloats", indexed, stored, multivalued)
        else:
            super().__init__(name, attribute_name, "pfloat", indexed, stored, multivalued)


class SolrIntField(SolrField):
    """
    SolrField subclass setting solr type to pint
    """

    def __init__(self, name: str, attribute_name: Optional[str] = None, indexed: bool = True, stored: bool = True,
                 multivalued: bool = False) -> None:
        if multivalued:
            super().__init__(name, attribute_name, "pints", indexed, stored, multivalued)
        else:
            super().__init__(name, attribute_name, "pint", indexed, stored, multivalued)


class SolrTextField(SolrField):
    """
    SolrField subclass setting solr type to text_end
    """

    def __init__(self, name: str, attribute_name: Optional[str] = None, indexed: bool = True, stored: bool = True,
                 multivalued: bool = False) -> None:
        super().__init__(name, attribute_name, "text_en", indexed, stored, multivalued)


class SolrJsonField(SolrField):
    """
    SolrField subclass setting solr type to text, meant for storing JSON
    """

    def __init__(self, name: str, attribute_name: Optional[str] = None, indexed: bool = True, stored: bool = True,
                 multivalued: bool = False) -> None:
        super().__init__(name, attribute_name, "text_en", indexed, stored, multivalued)


class SolrBooleanField(SolrField):
    """
    SolrField subclass setting solr type to boolean
    """

    def __init__(self, name: str, attribute_name: Optional[str] = None, indexed: bool = True, stored: bool = True,
                 multivalued: bool = False) -> None:
        super().__init__(name, attribute_name, "boolean", indexed, stored, multivalued)


class SolrForeignKeyField(SolrField):
    """
    SolrField subclass for links between entities
    """

    def __init__(self, name: str, entity_name: str, attribute_name: Optional[str] = None,
                 multivalued: bool = False, reversed_by: 'SolrEntity' = None, reversed_multiple: bool = False) -> None:
        self.linked_entity_name = entity_name
        self.reversed_by = reversed_by
        self.reversed_multiple = reversed_multiple
        super().__init__(name, attribute_name, "string", True, True, multivalued)
