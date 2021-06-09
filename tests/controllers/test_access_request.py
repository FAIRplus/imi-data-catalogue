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


import unittest

from flask import url_for

from tests.base_test import BaseTest
from datacatalog import app, mail
from datacatalog.models.dataset import Dataset

app.testing = True


class TestAccessRequest(BaseTest):
    TESTING = True

    def setUp(self):
        self.assertTrue(self.app.testing)
        self.solr_orm = app.config['_solr_orm']
        self.solr_orm.delete(query='*:*')
        self.solr_orm.delete_fields()
        self.solr_orm.create_fields()
        title = "Great dataset!"
        dataset = Dataset(title)
        dataset.save()
        self.solr_orm.commit()
        self.dataset_id = dataset.id

    def test_email_request_access(self):
        with app.test_client() as client:
            app.config['ACCESS_HANDLERS'] = {'dataset': 'Email'}
            rv = client.post(url_for('request_access', entity_name='dataset', entity_id=self.dataset_id))
            self.assertEqual(rv.status_code, 200)

    @unittest.skip('Not included in the test')
    def test_mail(self):
        with mail.record_messages() as outbox:
            mail.send_message(subject="testing",
                              body="test",
                              recipients=["to@elixir-luxembourg.org"])
            assert len(outbox) == 1
            assert outbox[0].subject == "testing"

    def tearDown(self):
        app.config['_solr_orm'].delete(query='*:*')
        app.config['_solr_orm'].commit()
