#  coding=utf-8
#  DataCatalog
#  Copyright (C) 2020  University of Luxembourg
#
#  This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging

from flask_login import current_user

from base_test import BaseTest
from datacatalog import get_access_handler, app
from datacatalog.acces_handler.email_handler import EmailAccessHandler
from datacatalog.acces_handler.rems_handler import RemsAccessHandler

logger = logging.getLogger(__name__)


class TestInit(BaseTest):

    def test_default_get_access_handler(self):
        app.config['ACCESS_HANDLERS'] = {'dataset': 'Email'}
        handler = get_access_handler(current_user, "dataset")
        self.assertEqual(handler.template, 'request_access.html')
        self.assertIsInstance(handler, EmailAccessHandler)

    def test_rems_get_access_handler(self):
        app.config['ACCESS_HANDLERS'] = {'dataset': 'Rems'}
        handler = get_access_handler(current_user, "dataset")
        self.assertEqual(handler.template, 'request_access_rems.html')
        self.assertIsInstance(handler, RemsAccessHandler)
