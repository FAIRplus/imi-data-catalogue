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
    datacatalog.models.contact
    -------------------

   Module containing the Contact class used for storing entity contact details information


"""
import logging

logger = logging.getLogger(__name__)


class Contact:
    """
    Contact class to hold information about project contacts.
    """

    def __init__(
        self,
        first_name: str,
        last_name: str,
        email: str,
        affiliation: str,
        business_address: str,
        full_name: str,
        roles: list,
    ) -> None:
        """
        Initialize a Contact instance setting firstname, email, lastname, fullname,
        affiliation, business_address and roles
        @param first_name: firstname of the contact
        @param last_name: lastName of the contact
        @param email: email of the contact
        @param affiliation: the affiliation of the contact in project
        @param business_address: the postal address of the contact
        @param full_name: the first_name + lastname of the contact
        @param roles: list of roles of contact in project
        """
        self.id = full_name
        self.full_name = full_name
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.affiliation = affiliation
        self.business_address = business_address
        if roles is None:
            self.roles = []
        else:
            self.roles = roles

    def to_json(self):
        result = {
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "affiliation": self.affiliation,
            "business_address": self.business_address,
            "roles": self.roles,
        }
        return result

    @staticmethod
    def from_json(data):
        contact = Contact(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            affiliation=data["affiliation"],
            business_address=data["business_address"],
            full_name=data["full_name"],
            roles=data["roles"],
        )
        return contact
