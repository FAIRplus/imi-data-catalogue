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

from datacatalog.solr.facets import Range, Facet, FacetRange

__author__ = 'Nirmeen Sallam'


class Test(BaseTest):

    def test_range(self):
        range = Range(0, 50, 20)
        range_iter_intervals = range.iter_intervals()
        self.assertEqual(next(range_iter_intervals),(0,20))
        next(range_iter_intervals)
        self.assertEqual(next(range_iter_intervals), (40, 60))

        range = Range(10, 50, 5)
        range_iter_intervals = range.iter_intervals()
        self.assertEqual(next(range_iter_intervals), (10, 15))

    def test_facet(self):
        facet = Facet("project_description")
        facet.default_values = ["project_start_date"]
        self.assertEqual(facet.field_name, "project_description")

        facet.use_default()
        self.assertEqual(facet.field_name, "project_description")
        self.assertEqual(facet.values, ["project_start_date"])

        facet.set_values(["project_description", "project_start_date"])
        self.assertEqual(facet.values, ["project_description", "project_start_date"])
        self.assertEqual(facet.using_default, False)

        facet.set_values(["project_start_date"])
        self.assertEqual(facet.using_default, True)

    def test_facet_range(self):
        range = Range(20, 50, 10)
        facetrange = FacetRange("project_description", "project_description", range)
        self.assertEqual(facetrange.field_name, "project_description")
