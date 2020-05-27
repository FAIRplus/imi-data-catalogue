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
    datacatalog.login_controllers
    -------------------

    HTML endpoints:
        - login
        - logout
"""

from flask import render_template, flash, redirect, url_for, Response
from flask_login import logout_user, login_user, login_required

from .. import app, login_manager
from ..exceptions import AuthenticationException
from ..forms.login_form import LoginForm
from ..models.user import User

logger = app.logger

users = {}
login_manager.login_view = "login"


@app.route('/login', methods=['GET', 'POST'])
def login() -> Response:
    """
    Login a user
    Displays login form for GET request
    Authenticate and redirect the user for POST request
    @return: The form for GET request or failed login, a redirect for successful login attempts
    """
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        try:
            authentication = app.config['authentication']
            success, user_details = authentication.authenticate_user(username, password)
            if success:
                logger.debug('authenticated')
                user = save_user(username, user_details[0], user_details[1])
                login_user(user)
                flash('Logged in successfully', 'success')
                return form.redirect()
        except AuthenticationException as e:
            flash(e, 'error')

    return render_template('login.html', form=form)


@app.login_manager.user_loader
def load_user(user_id: str) -> User:
    """
    Retrieve a user from the cached list of users
    @param user_id: user id
    @return: a User instance
    """
    if user_id in users:
        return users[user_id]
    return None


def save_user(username: str, email: str, display_name: str) -> User:
    """
    Creates a user instance and save it in memory cache
    @param username: name of the user
    @param email: email of the user
    @param display_name: name of the user for display
    @return: a User instance
    """
    user = User(username, email, display_name)
    users[user.id] = user
    return user


@app.route("/logout")
@login_required
def logout() -> Response:
    """
    User logout
    @return: redirect to datacatalog.web_controllers.search endpoint
    """
    logout_user()
    return redirect(url_for('search'))


def clean_users_dict():
    for user in users.items():
        print(user[1])
