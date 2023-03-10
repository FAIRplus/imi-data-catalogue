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
    datacatalog.solr.facets
    -------------------

   Module containing the facets class and related utility classes:
     - Range
     - Facet
     - FacetRange

"""
import logging

import math

from typing import Tuple, Generator, List

logger = logging.getLogger(__name__)


class Range(object):
    """
    The Range class together with the FacetRange class allows specify intervals of values
    to be displayed as facets rather that each value separately
    """

    def __init__(self, start: float, end: float, gap: float, other: str = None) -> None:
        """
        Initialize a Range instance with start, end , gap and other parameters
        see https://lucene.apache.org/solr/guide/8_4/faceting.html#Faceting-RangeFaceting
        @param start: specifies the lower bound of the ranges
        @param end:specifies the upper bound of the ranges
        @param gap: span of each range expressed as a value to be added to the lower bound
        @param other:  specifies that in addition to the counts for each range constraint between start and end, counts
         should also be computed for these options:
                - before: All records with field values lower then lower bound of the first range.
                - after: All records with field values greater then the upper bound of the last range.
                - between: All records with field values between the start and end bounds of all ranges.
                - none: Do not compute any counts.
                - all: Compute counts for before, between, and after.
        default is none and no counts will be computed for values outside the start-end range
        """
        self.other = other
        self.gap = gap
        self.end = end
        self.start = start

    def iter_intervals(self) -> Generator[Tuple[float, float], None, None]:
        """
        Generator yielding each interval of this range instance as a tuple (interval_start, interval_end)
        """
        number_of_intervals = math.ceil((self.end - self.start) / self.gap)
        for i in range(0, number_of_intervals):
            interval_start = (i * self.gap) + self.start
            interval_end = (i + 1) * self.gap + self.start
            yield interval_start, interval_end


class Facet(object):
    """
    Facet object to configure the solr facets
    see https://lucene.apache.org/solr/guide/8_4/faceting.html
    """

    def __init__(
        self, field_name: str, label: str = None, default_values: List = None
    ) -> None:
        """
        Initialize a Facet instance setting the field name, the label and default values
        @param field_name: the solr field name that we want to build facet for
        @param label: label that will be used as header of the facet on the search page
        @param default_values: can be used to force some default values
        """
        self.using_default = False
        self.label = label
        self.range = range
        self.field_name = field_name
        self.values = []
        self.range = None
        self.default_values = default_values or []

    def set_values(self, values):
        self.values = values
        self.using_default = False
        if values == self.default_values:
            self.using_default = True

    def use_default(self):
        if self.default_values:
            self.set_values(self.default_values)
            self.using_default = True


class FacetRange(Facet):
    """
    Version of the Facet class that allows specifying a range attribute
    Can be used to facet per range of values rather than each individual value
    """

    def __init__(self, field_name: str, label: str, facet_range: Range) -> None:
        """
        Initialize a FacetRange instance setting the field name, the label and the range
        @param field_name: the solr field name that we want to build facet for
        @param label: label that will be used as header of the facet on the search page
        @param facet_range: range instance to configure the intervals
        """
        super().__init__(field_name, label)
        self.range = facet_range
