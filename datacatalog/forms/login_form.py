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
    datacatalog.forms.login_form
    -------------------

    Login form

"""
import logging

from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length

from . import RedirectForm

logger = logging.getLogger(__name__)


class LoginForm(RedirectForm):
    """
    Login form with three fields:
    - username
    - password
    - remember me checkbox
    """

    username = StringField(
        "Username",
        [DataRequired(), Length(min=4, max=25)],
        render_kw={"placeholder": "username"},
    )
    password = PasswordField(
        "Password", [DataRequired()], render_kw={"placeholder": "password"}
    )
    remember = BooleanField("Remember me")
