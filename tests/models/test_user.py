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
from datacatalog.models.user import User

__author__ = 'Nirmeen Sallam'


class TestUser(BaseTest):

    def test_get_id(self):
        u = User("test_user", "", "")
        self.assertEqual("test_user", User.get_id(u))

    def test_invalid_user_get_id(self):
        self.assertRaises(AttributeError, User.get_id, "")
        self.assertRaises(AttributeError, User.get_id, 1)
        self.assertRaises(AttributeError, User.get_id, None)