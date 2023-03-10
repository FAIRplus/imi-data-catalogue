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

from datacatalog.exceptions import AuthenticationException
from tests.base_test import BaseTest
from datacatalog import app
from datacatalog.authentication.ldap_authentication import (
    LDAPUserPasswordAuthentication,
)

__author__ = "Nirmeen Sallam"


class TestLDAPUserPasswordAuthentication(BaseTest):

    ldapauth = LDAPUserPasswordAuthentication(app.config.get("LDAP_HOST"))
    app.config["AUTHENTICATION_METHOD"] = "LDAP"
    username = app.config.get("LDAP_USERNAME")
    password = app.config.get("LDAP_PASSWORD")

    conn = ldapauth.get_ldap_connection()
    member = "uid={},cn=users,cn=accounts,dc=uni,dc=lu".format(username)
    conn.simple_bind_s(member, password)

    def test_get_user_details(self):
        response = self.ldapauth.get_user_details(self.conn, self.username)
        self.assertIn(self.username.replace(".", " "), response)

    def test_get_user_details_invalid_user(self):
        with self.assertRaises(AuthenticationException) as cm:
            self.ldapauth.get_user_details(self.conn, self.username + "test")
        self.assertEqual("Invalid user", str(cm.exception))

    def test_authenticate_user(self):
        success, user_details = self.ldapauth.authenticate_user(
            self.username, self.password
        )
        self.assertTrue(success)
        self.assertIsNotNone(user_details)

    def test_authenticate_user_invalid_credentials(self):
        with self.assertRaises(AuthenticationException) as cm:
            self.ldapauth.authenticate_user(self.username + "test", self.password)
        self.assertEqual("Invalid Credentials", str(cm.exception))

    def test_get_attributes_by_dn(self):
        attributes = self.ldapauth.get_attributes_by_dn(
            self.member, self.conn, self.username, ["displayName", "mail"]
        )
        self.assertTrue(len(attributes) == 2)
        attributes = self.ldapauth.get_attributes_by_dn(
            self.member, self.conn, self.username + "test", ["displayName", "mail"]
        )
        self.assertIsNone(attributes)

    def test_get_email_by_dn(self):
        email = self.ldapauth.get_email_by_dn(self.member, self.conn, self.username)
        self.assertTrue(email)
        email = self.ldapauth.get_email_by_dn(
            self.member, self.conn, self.username + "test"
        )
        self.assertFalse(email)

    def test_get_displayname_by_dn(self):
        display_name = self.ldapauth.get_displayname_by_dn(
            self.member, self.conn, self.username
        )
        self.assertTrue(display_name)
        display_name = self.ldapauth.get_email_by_dn(
            self.member, self.conn, self.username + "test"
        )
        self.assertFalse(display_name)
