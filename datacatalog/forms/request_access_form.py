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
    datacatalog.forms.request_access_form
    -------------------

    Form to request access to an entity

"""
import logging

from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, validators, TextAreaField, SubmitField
from wtforms.fields.html5 import EmailField

logger = logging.getLogger(__name__)


class RequestAccess(FlaskForm):
    """
    Form to request access to an entity
    Protected by recaptcha
    fields:
     - name of the requester
     - email of the requester
     - message
     - recaptcha
     - submit button
    """
    name = StringField("Name", [validators.DataRequired("Please enter your name.")])
    email = EmailField("Email",
                       [validators.Email("This field requires a valid email address"), validators.DataRequired()])
    message = TextAreaField("Describe your planned research on the dataset",
                            [validators.DataRequired("Please enter a message.")])
    recaptcha = RecaptchaField()
    submit = SubmitField("Send")
