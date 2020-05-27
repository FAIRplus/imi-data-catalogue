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
    datacatalog.authentication
    -------------------

    Package for the abstract class Authentication and its implementations
    Implementations:
        - LDAPAuthentication

"""

from abc import ABCMeta, abstractmethod

__author__ = 'Valentin Grouès'


class Authentication(metaclass=ABCMeta):
    """
    Abstract class specifying methods to implement to authenticate users
    Is used for login process
    """

    @abstractmethod
    def authenticate_user(self, username, password):
        """
        Check if username and password matches and if user is authorized
        @param username: name of the user
        @type username: str
        @param password: password of the user
        @type password: str
        @return an exception if not successful, a tuple containing True and the user details if successful
        """
        pass
