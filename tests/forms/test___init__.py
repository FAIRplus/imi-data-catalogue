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

from tests.base_test import BaseTest
import datacatalog.forms as dcForms
from flask import request


__author__ = 'Nirmeen Sallam'


class Test(BaseTest):

    def test_is_safe_url(self):
        host_url = request.host_url[:-1]
        is_safe_url = dcForms.is_safe_url(host_url+"/datasets")
        self.assertTrue(is_safe_url)

        is_safe_url = dcForms.is_safe_url(host_url+"test/")
        self.assertFalse(is_safe_url)

    def test_get_redirect_target(self):
        self.assertEqual(dcForms.get_redirect_target(), None)

    def test_redirect_form(self):
        redirectforms = dcForms.RedirectForm()
        self.assertEqual(redirectforms.redirect().location,"/")
