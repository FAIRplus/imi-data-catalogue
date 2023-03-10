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
    datacatalog.authentication.ldap_authentication
    -------------------

    Contains an implementation of class UserPasswordAuthentication for LDAP authentication

"""
import logging
from typing import Tuple, List, Optional

from ldap.ldapobject import LDAPObject

from . import UserPasswordAuthentication
from .. import app, ldap
from ..exceptions import AuthenticationException

__author__ = "Kavita Rege"

logger = logging.getLogger(__name__)


class LDAPUserPasswordAuthentication(UserPasswordAuthentication):
    """
    Implementation of class UserPasswordAuthentication for LDAP authentication
    """

    def __init__(self, ldap_address: str) -> None:
        """
        Initialize a LDAPUserPasswordAuthentication instance setting the ldap address
        @param ldap_address: address and port of the LDAP server
        """
        self.ldap_address = ldap_address
        logger.info(
            "LDAPUserPasswordAuthentication initialized with address %s", ldap_address
        )

    def get_user_details(self, conn: LDAPObject, username: str) -> List[str]:
        """
        Retrieve user details
        @param username: the name of the user
        @return: raises an exception if unsuccessful,
        returns list containing email and display_name if successful
        """
        logger.debug("getting user details for username %s", username)
        try:
            member_list = []
            member = "uid={},cn=users,cn=accounts,dc=uni,dc=lu".format(username)
            attributes = self.get_attributes_by_dn(
                member, conn, username, ["displayName", "mail"]
            )
            if attributes is None:
                raise AuthenticationException("Invalid user")
            member_list.append(attributes.get("mail"))
            member_list.append(attributes.get("displayName"))
            return member_list
        except ldap.SERVER_DOWN:
            raise AuthenticationException("LDAP server could not be reached")

    def authenticate_user(self, username: str, password: str) -> Tuple[bool, List[str]]:
        """
        Check if username and password matches and if user is a valid user
        @param username: the name of the user
        @param password: the password of the user
        @return: raises an exception if unsuccessful,
        returns True and a list containing email and displayname if successful
        """
        logger.info("authenticating user %s", username)
        try:
            conn = self.get_ldap_connection()
            member = "uid={},cn=users,cn=accounts,dc=uni,dc=lu".format(username)
            conn.simple_bind_s(member, password)

            group_filter = app.config.get("LDAP_USER_GROUPS_FIELD")
            if group_filter:
                search_filter = (
                    "(|(&(objectClass=groupOfNames)(cn={})(member={})))".format(
                        group_filter, member
                    )
                )
            else:
                search_filter = "(member={})".format(member)
            results = conn.search_s(
                app.config.get("LDAP_BASE_DN"), ldap.SCOPE_SUBTREE, search_filter
            )
            try:
                members = results[0][1]["member"]
                if member.encode("UTF8") in members:
                    user_details = self.get_user_details(conn, username)
                    return True, user_details
                else:
                    logger.info("user not in group")
                    raise AuthenticationException("User not authorized")
            except IndexError:
                logger.info("user not authorized")
                raise AuthenticationException("User not authorized")
        except ldap.INVALID_CREDENTIALS:
            logger.info("invalid credentials")
            raise AuthenticationException("Invalid Credentials")
        except ldap.SERVER_DOWN:
            logger.error("cannot reach ldap server")
            raise AuthenticationException("LDAP server could not be reached")

    def get_ldap_connection(self) -> LDAPObject:
        """
        Create the connection via LDAP
        @return: an open connection
        """
        conn = ldap.initialize(self.ldap_address, bytes_mode=False)
        conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        conn.protocol_version = ldap.VERSION3
        conn.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
        return conn

    def get_attributes_by_dn(
        self, dn: str, ad_conn: LDAPObject, uid: str, attributes: List[str]
    ) -> Optional[dict]:
        """
        Retrieve the specified attributes for a dedicated user
        @param dn: AD distinguished name
        @param ad_conn: connection to AD
        @param uid: user id
        @param attributes: list of attributes to retrieve
        @return: the list of attributes values
        """
        result = ad_conn.search_s(
            dn,
            ldap.SCOPE_SUBTREE,
            "(&(objectClass=person)(uid={}))".format(uid),
            attrlist=attributes,
        )
        results = {}
        if not result:
            # return None if user not found
            return None
        for dn, attributes_ad in result:
            for attribute_ad, attribute_ad_value in attributes_ad.items():
                if attribute_ad in attributes and attribute_ad_value:
                    results[attribute_ad] = attribute_ad_value[0].lower().decode("UTF8")

        return results

    @staticmethod
    def get_email_by_dn(dn: str, ad_conn: LDAPObject, uid: str) -> str:
        """
        Retrieve the email address of a specific user
        @param dn: AD distinguished name
        @param ad_conn: connection to AD
        @param uid: user id
        @return: the email address of user uid in dn or an empty string
        """
        email = b""
        result = ad_conn.search_s(
            dn, ldap.SCOPE_BASE, "(&(objectClass=person)(uid={}))".format(uid)
        )
        if result:
            for dn, attrb in result:
                if "mail" in attrb and attrb["mail"]:
                    email = attrb["mail"][0].lower()
                    break
        return email.decode("UTF8")

    @staticmethod
    def get_displayname_by_dn(dn: str, ad_conn: LDAPObject, uid: str) -> str:
        """
        Retrieve the display name of a specific user
        @param dn: AD distinguished name
        @param ad_conn: connection to AD
        @param uid: user id
        @return: the display name of user uid in dn or an empty string
        """
        displayname = ""
        result = ad_conn.search_s(
            dn, ldap.SCOPE_SUBTREE, "(&(objectClass=person)(uid={}))".format(uid)
        )
        if result:
            for dn, attrb in result:
                if "displayName" in attrb and attrb["displayName"]:
                    displayname = attrb["displayName"][0]
                    break
        return displayname.decode("UTF8")
