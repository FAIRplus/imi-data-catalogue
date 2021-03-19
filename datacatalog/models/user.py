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
    datacatalog.models.user
    -------------------

   Module containing the User class used for authentication


"""
import logging

from flask_login import UserMixin

logger = logging.getLogger(__name__)


class User(UserMixin):
    """
    User class to hold information about logged in user.
    Extends the Flask-Login UserMixing
    """

    def __init__(self, username: str, email: str, displayname: str, active: bool = True) -> None:
        """
        Initialize a User instance setting username, email, display name and activate status
        @param username: name of the user
        @param email: email of the user
        @param displayname: version of the username for display
        @param active: boolean showing if the user is active or not
        """
        self.id = username
        self.username = username
        self.email = email
        self.displayname = displayname
        self.active = active

    def __repr__(self) -> str:
        return self.displayname

    def get_id(self) -> int:
        """
        Returns the user id or raise an AttributeError exception if id attribute doesn't exist
        @return: user id
        """
        return self.id
