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

from datacatalog import app
from datacatalog.authentication.ldap_authentication import LDAPUserPasswordAuthentication
from tests.base_test import BaseTest
from flask import session, current_app, url_for

from datacatalog.controllers.login_controllers import load_user, save_user, login, logout
from datacatalog.exceptions import AuthenticationException

__author__ = 'Nirmeen Sallam'

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class TestLoginControllers(BaseTest):

    ldapauth = LDAPUserPasswordAuthentication(app.config.get('LDAP_HOST'))
    username = app.config.get('LDAP_USERNAME')
    password = app.config.get('LDAP_PASSWORD')
    conn = ldapauth.get_ldap_connection()
    member = "uid={},cn=users,cn=accounts,dc=uni,dc=lu".format(username)
    conn.simple_bind_s(
        member,
        password
    )

    def test_login_LDAP_invalid_form(self):
        current_app.config["authentication"] = self.ldapauth
        with self.client:
            response = self.client.post(url_for("login"),
                                        data={"username": app.config.get('LDAP_USERNAME'),
                                              "password": ''})
            self.assertIn('id="login-form"', response.data.decode('utf-8'))

    def test_login_invalid_auth_object(self):
        authdict = dotdict({'LOGIN_TYPE': 1})
        current_app.config["authentication"] = authdict
        with self.assertRaises(AuthenticationException) as cm: login()
        self.assertEqual("unknown authentication type", str(cm.exception))

    def test_login_LDAP_error(self):
        current_app.config["authentication"] = self.ldapauth
        with self.client:
            response = self.client.post(url_for("login"),
                                        data={"username": "test_error",
                                              "password": "test_error"})
            self.assertIn("Invalid Credentials", response.data.decode())

    def test_login_LDAP_success(self):
        current_app.config["authentication"] = self.ldapauth
        with self.client:
            response = self.client.post(url_for("login"),
                                        data={"username": app.config.get('LDAP_USERNAME'),
                                              "password": app.config.get('LDAP_PASSWORD')})
            self.assertEqual(response.status_code, 302)

    def test_load_user(self):
        session["userid"] = app.config.get('LDAP_USERNAME')
        session["user_details"] = {'email':'test', 'display_name': app.config.get('LDAP_USERNAME')}
        self.assertEqual(load_user(app.config.get('LDAP_USERNAME')).displayname, app.config.get('LDAP_USERNAME'))
        self.assertIsNone(load_user("test_none"))

    def test_save_user(self):
        session.clear()
        save_user(app.config.get('LDAP_USERNAME'), 'test', app.config.get('LDAP_USERNAME'))
        self.assertEqual(session["user_details"].get('display_name'), app.config.get('LDAP_USERNAME'))

    def test_logout(self):
        current_app.config["authentication"] = self.ldapauth
        with self.client:
            self.client.post(url_for("login"),
                             data={"username": app.config.get('LDAP_USERNAME'),
                                   "password": app.config.get('LDAP_PASSWORD')})
            logout_response = self.client.get(url_for("logout"))
            self.assertEqual(logout_response.status_code, 302)



