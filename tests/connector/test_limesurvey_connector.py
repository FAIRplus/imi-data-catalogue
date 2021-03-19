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

from base_test import BaseTest
from datacatalog import app
from datacatalog.connector.limesurvey_connector import LimesurveyConnector

__author__ = 'Valentin Grouès'


class TestLimesurveyConnector(BaseTest):

    @unittest.skip('limesurvey import not used anymore')
    def test_build_all_datasets(self):
        limesurvey_connector = LimesurveyConnector(app.config['LIMESURVEY_URL'],
                                                   app.config['LIMESURVEY_USERNAME'],
                                                   app.config['LIMESURVEY_PASSWORD'],
                                                   app.config['LIMESURVEY_SURVEY_ID']
                                                   )
        datasets = list(limesurvey_connector.build_all_entities())
        self.assertTrue(datasets)
