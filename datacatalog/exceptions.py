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
    datacatalog.exceptions
    -------------------

   Module to configure DataCatalog exceptions

"""
__author__ = "Valentin Grouès"


class DataCatalogException(Exception):
    """
    Base class for DataCatalog exceptions
    """

    pass


class DownloadsHandlerLinksException(DataCatalogException):
    """
    Error retrieving downloads links
    """

    pass


class AuthenticationException(DataCatalogException):
    """
    Authentication related exceptions
    """

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class SolrIndexerException(DataCatalogException):
    """
    All exceptions linked to a problem with Solr
    """

    pass


class SolrQueryException(SolrIndexerException):
    """
    Exception for Solr queries errors
    """

    pass


class PostRequestException(DataCatalogException):
    """
    Exception for error happening during post request hook
    """

    pass


class CouldNotCloseApplicationException(DataCatalogException):
    """
    When an access request application could not be closed
    """

    pass


class CouldNotSubmitApplicationException(DataCatalogException):
    """
    When an access request application could not be submitted
    """

    pass
