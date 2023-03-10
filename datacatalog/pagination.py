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
    datacatalog.pagination
    -------------------

   Module containing the Pagination utility class.
   It is used to handle pagination in jinja templates.

"""
import logging
from math import ceil
from typing import Optional, Generator

__author__ = "Valentin Grouès"

logger = logging.getLogger(__name__)


class Pagination:
    """
    Class to handle pagination of search results and any long list of results
    Pagination is configured by setting the current page number, the number or results per page and the total number
    of entries.
    """

    def __init__(self, page: int, per_page: int, total_count: int) -> None:
        """
        Initialize a Pagination instance by setting the current page, the number of results per page and
        the total number of entries
        @param page: index of the current page
        @param per_page: how many entries per page do we want
        @param total_count: total number of entries
        """
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self) -> int:
        """
        Property that computes the number of pages by dividing the total number or entries by the
        number of entries per page and rounding up
        @return: total number of pages
        """
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self) -> bool:
        """
        Property that return true if we are not on the first page
        @return: boolean showing that we have pages before the current page
        """
        return self.page > 1

    @property
    def has_next(self) -> bool:
        """
        Property that return true if we are not on the last page
        @return: boolean showing that we have pages after the current page
        """
        return self.page < self.pages

    def iter_pages(
        self,
        left_edge: int = 2,
        left_current: int = 2,
        right_current: int = 5,
        right_edge: int = 2,
    ) -> Generator[Optional[int], None, None]:
        """
        Generator used to build navigation links to jump between pages
        If current pages is 6 out of a total number of pages of 20, we will get with the default values:
        1, 2, None, 4, 5, 6, 7, 8, 9, 10, 11, None, 19, 20
        @param left_edge: how many pages should we show on the left side of the navigation menu (first pages)
        @param left_current: how many pages should we show on the left side of the current page
        @param right_current: how many pages should we show on the right side of the navigation menu (last pages)
        @param right_edge: how many pages should we show on the right side of the current page
        """
        last = 0
        for num in range(1, self.pages + 1):
            if (
                num <= left_edge
                or (self.page - left_current - 1 < num < self.page + right_current)
                or num > self.pages - right_edge
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num
