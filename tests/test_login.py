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

# coding='utf-8'

from flask import url_for
from flask_login import current_user

from base_test import BaseTest
from datacatalog import app


class TestLogin(BaseTest):
    print("##############Testing Login ##############################")

    def test_invalid_password_is_rejected(self):
        with self.client:
            response = self.client.post(url_for("login"),
                                        data={"username": app.config.get('LDAP_USERNAME'),
                                              "password": app.config.get('LDAP_PASSWORD')})

            self.assertTrue(response.status_code, 200)
            self.assertTrue(current_user, app.config.get('LDAP_USERNAME'))
