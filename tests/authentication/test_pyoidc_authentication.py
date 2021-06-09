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

import unittest
from tests.base_test import BaseTest

from datacatalog.authentication.pyoidc_authentication import PyOIDCAuthentication
from datacatalog import app
import urllib

__author__ = 'Nirmeen Sallam'


class TestPyOIDCAuthentication(BaseTest):

    skip_tests_flag = False
    error_msg = ""

    try:
        pyauth = PyOIDCAuthentication(app.config.get('BASE_URL'), app.config.get('PYOIDC_CLIENT_ID'),
                                      app.config.get('PYOIDC_CLIENT_SECRET'),
                                      app.config.get('PYOIDC_IDP_URL'))
    except Exception as e:
        skip_tests_flag = True
        error_msg = e

    @unittest.skipIf(skip_tests_flag, error_msg)
    def test_authenticate_user_redirect(self):
        respone = self.pyauth.authenticate_user()
        self.assertEqual(respone.status_code, 303)
        self.assertTrue(respone.location.startswith(app.config.get('PYOIDC_IDP_URL')))

    @unittest.skipIf(skip_tests_flag, error_msg)
    def test_get_logout_url_redirect(self):
        logout_url = urllib.parse.unquote(self.pyauth.get_logout_url())
        self.assertTrue(logout_url.startswith(app.config.get('PYOIDC_IDP_URL')))
        self.assertIn("redirect_uri=" + app.config.get('BASE_URL'), logout_url)
