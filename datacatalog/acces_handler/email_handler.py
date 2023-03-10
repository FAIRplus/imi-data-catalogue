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

from flask import url_for
from flask_login import current_user
from flask_mail import Message

from .access_handler import AccessHandler
from .. import app, mail
from ..forms.request_access_form import RequestAccess
from ..models.user import User

logger = logging.getLogger(__name__)


class EmailAccessHandler(AccessHandler):
    def requires_logged_in_user(self, entity):
        return False

    def supports_listing_accesses(self):
        return False

    def __init__(self, user: User):
        logger.debug("Initializing email access handler")
        super().__init__(user)
        self.name = None
        self.email = None

    def has_access(self, dataset):
        return False

    def apply(self, entity, form):
        subject = "Access request to " + entity.title
        entity_name = entity.__class__.__name__.lower()
        logger.info(
            "Access request by email to entity of type %s, id %s",
            entity_name,
            entity.id,
        )
        url = url_for(
            "entity_details",
            entity_name=entity_name,
            entity_id=entity.id,
            _external=True,
        )
        email = self.email or form.email.data
        if self.email:
            logger.info("User was logged in, id: %s", current_user.id)
        else:
            logger.info("User was not logged in, provided email: %s", email)
        name = self.name or form.name.data
        msg = Message(subject, sender=email, recipients=app.config["EMAIL_RECIPIENT"])

        msg.body = """
        From: %s <%s>

        %s

        %s
        """ % (
            name,
            email,
            form.message.data,
            url,
        )
        mail.send(msg)
        logger.debug("Email sent")

    def get_datasets(self):
        pass

    def create_form(self, dataset, form_data):
        logger.debug("Creating form for email request")
        form = RequestAccess(form_data)
        if self.user.is_authenticated:
            self.email = self.user.email or self.user.id
            self.name = self.user.id
            del form.email
            del form.name
        return form
