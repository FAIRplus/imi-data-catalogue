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

    Contains an implementation of class Authentication for LDAP authentication

"""
from typing import Tuple, List

from ldap.ldapobject import LDAPObject

from . import Authentication
from .. import app, ldap
from ..exceptions import AuthenticationException

__author__ = 'Kavita Rege'

logger = app.logger


class LDAPAuthentication(Authentication):
    """
    Implementation of class Authentication for LDAP authentication
    """

    def __init__(self, ldap_address: str) -> None:
        """
        Initialize a LDAPAuthentication instance setting the ldap address
        @param ldap_address: address and port of the LDAP server
        """
        self.ldap_address = ldap_address
        logger.info("LDAPAuthentication initialized with address %s", ldap_address)

    def authenticate_user(self, username: str, password: str) -> Tuple[bool, List[str]]:
        """
        Check if username and password matches and if user is a valid user
        @param username: the name of the user
        @param password: the password of the user
        @return: raises an exception if unsuccessful,
        returns True and a list containing email and displayname if successful
        """
        try:
            memberlist = []
            conn = self.get_ldap_connection()
            member = "uid={},cn=users,cn=accounts,dc=uni,dc=lu".format(username)
            conn.simple_bind_s(
                member,
                password
            )

            search_filter = '(|(&(objectClass=groupOfNames)(cn=*{}*)(member={})))'. \
                format(app.config.get('LDAP_USER_GROUPS_FIELD'), member)
            results = conn.search_s(app.config.get('LDAP_BASE_DN'), ldap.SCOPE_SUBTREE, search_filter)
            try:
                members = results[0][1]['member']
                if member.encode('ASCII') in members:
                    email = self.get_email_by_dn(member, conn, username)
                    displayname = self.get_displayname_by_dn(member, conn, username)
                    if email:
                        memberlist.append(email)
                    if displayname:
                        memberlist.append(displayname)
                return True, memberlist
            except IndexError:
                raise AuthenticationException("User not authorized")
        except ldap.INVALID_CREDENTIALS:
            raise AuthenticationException("Invalid Credentials")
        except ldap.SERVER_DOWN:
            raise AuthenticationException("LDAP server could not be reached")

    def get_ldap_connection(self) -> LDAPObject:
        """
        Create the connection via LDAP
        @return: an open connection
        """
        conn = ldap.initialize(self.ldap_address, bytes_mode=False)
        conn.set_option(ldap.OPT_REFERRALS, 0)
        conn.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
        return conn

    @staticmethod
    def get_email_by_dn(dn: str, ad_conn: LDAPObject, uid: str) -> str:
        """
        Retrieve the email address of a specific user
        @param dn: AD distinguished name
        @param ad_conn: connection to AD
        @param uid: user id
        @return: the email address of user uid in dn or an empty string
        """
        email = ''
        result = ad_conn.search_s(dn, ldap.SCOPE_BASE, \
                                  '(&(objectClass=person)(uid={}))'.format(uid))
        if result:
            for dn, attrb in result:
                if 'mail' in attrb and attrb['mail']:
                    email = attrb['mail'][0].lower()
                    break
        return email.decode('ASCII')

    @staticmethod
    def get_displayname_by_dn(dn: str, ad_conn: LDAPObject, uid: str) -> str:
        """
        Retrieve the display name of a specific user
        @param dn: AD distinguished name
        @param ad_conn: connection to AD
        @param uid: user id
        @return: the display name of user uid in dn or an empty string
        """
        displayname = ''
        result = ad_conn.search_s(dn, ldap.SCOPE_SUBTREE, '(&(objectClass=person)(uid={}))'.format(uid))
        if result:
            for dn, attrb in result:
                if 'displayName' in attrb and attrb['displayName']:
                    displayname = attrb['displayName'][0]
                    break
        return displayname.decode('ASCII')
