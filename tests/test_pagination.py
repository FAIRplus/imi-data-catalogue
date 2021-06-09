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
from datacatalog.pagination import Pagination

__author__ = 'Nirmeen Sallam'


class TestPagination(BaseTest):

    pagination = Pagination(1, 2, 10)

    def test_pages(self):
        self.assertEqual(self.pagination.pages, 5)

    def test_has_prev(self):
        self.assertFalse(self.pagination.has_prev)
        self.pagination = Pagination(2, 2, 10)
        self.assertTrue(self.pagination.has_prev)

    def test_has_next(self):
        self.assertTrue(self.pagination.has_next)
        self.pagination = Pagination(5, 2, 10)
        self.assertFalse(self.pagination.has_next)

    def test_iter_pages(self):
        pagination = Pagination(6, 1, 10)
        result = list(pagination.iter_pages(1, 1, 2, 1))
        self.assertEqual(result, [1, None, 5, 6, 7, None, 10])
        result = list(pagination.iter_pages())
        self.assertEqual(result, [1, 2, None, 4, 5, 6, 7, 8, 9, 10])
