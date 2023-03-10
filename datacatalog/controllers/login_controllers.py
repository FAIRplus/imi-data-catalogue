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
import logging
from typing import Optional

from flask import render_template, flash, redirect, url_for, Response, session
from flask_login import logout_user, login_user, login_required, current_user

from .. import app, login_manager, public_route
from ..authentication import LoginType
from ..exceptions import AuthenticationException
from ..forms.login_form import LoginForm
from ..models.user import User

logger = logging.getLogger(__name__)

users = {}
login_manager.login_view = "login"


@public_route
@app.route("/login", methods=["GET", "POST"])
def login() -> Response:
    """
    Login a user
    Displays login form for GET request
    Authenticate and redirect the user for POST request
    @return: The form for GET request or failed login, a redirect for successful login attempts
    """
    session.permanent = True
    authentication = app.config["authentication"]
    if authentication is None:
        logger.error("no authentication backend available")
        raise AuthenticationException(
            "no authentication backend available, cannot login. Try again later."
        )

    if authentication.LOGIN_TYPE == LoginType.FORM:
        form = LoginForm()
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            try:
                success, user_details = authentication.authenticate_user(
                    username, password
                )
                if success:
                    user = save_user(username, user_details[0], user_details[1])
                    login_user(user)
                    logger.info("User %s authenticated", username)
                    flash("Logged in successfully", "success")
                    return form.redirect()
            except AuthenticationException as e:
                flash(e, "error")
        return render_template("login.html", form=form)
    if authentication.LOGIN_TYPE == LoginType.REDIRECT:
        return authentication.authenticate_user()
    logger.error("unknown authentication type %s", authentication.LOGIN_TYPE)
    raise AuthenticationException("unknown authentication type")


@app.login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    """
    Retrieve a user from the session data
    @param user_id: user id
    @return: a User instance
    """
    logger.debug("loading user %s", user_id)
    session_user_id = session["_user_id"]
    if user_id == session_user_id:
        logger.debug("user id %s matches session userid", user_id)
    else:
        logger.warning(
            "user id %s doesn't match session userid %s", user_id, session_user_id
        )
        return None
    users_details = session.get("user_details")
    if users_details:
        logger.debug("user_details session data found for user %s", user_id)
        email = users_details.get("email")
        display_name = users_details.get("display_name")
        accesses = users_details.get("accesses")
        logger.debug(
            "accesses found in session data for user %s: %s",
            user_id,
            ",".join(accesses if accesses is not None else []),
        )
        extra = users_details.get("extra")
        if email and display_name:
            user = User(user_id, email, display_name, accesses=accesses, extra=extra)
            auth = app.config["authentication"]
            if auth.validate_user(user):
                user = auth.check_and_refresh(user)
            return user
    else:
        logger.debug("no session data for this user")
    return None


def save_user(
    username: str, email: str, display_name: str, accesses: list = None, extra=None
) -> User:
    """
    Creates a user instance and save it in the session
    @param username: name of the user
    @param email: email of the user
    @param display_name: name of the user for display
    @param accesses: list of datasets_id the user has access to
    @return: a User instance
    """
    user = User(username, email, display_name, accesses=accesses, extra=extra)
    user.save()
    return user


@app.route("/logout")
@login_required
def logout() -> Response:
    """
    User logout
    @return: redirect to datacatalog.web_controllers.search endpoint
    """
    logger.info("logout for user %s", current_user.id)
    authentication = app.config["authentication"]
    if authentication.LOGIN_TYPE == LoginType.FORM:
        logout_user()
        return redirect(url_for("home"))
    if authentication.LOGIN_TYPE == LoginType.REDIRECT:
        logout_url = authentication.get_logout_url(current_user)
        if logout_url:
            return redirect(logout_url)
        else:
            logout_user()
            return redirect(url_for("home"))

    raise AuthenticationException("unknown authentication type")
