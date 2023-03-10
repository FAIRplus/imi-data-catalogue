import datetime
import logging

from flask import Blueprint, flash, redirect, url_for, current_app, request, session
from flask_login import logout_user, login_user, current_user
from oic.exception import MessageException
from oic.oauth2 import ErrorResponse, ResponseError
from oic.oic.message import AuthorizationResponse

from ..exceptions import AuthenticationException
from ..models.user import User

logger = logging.getLogger(__name__)

pyoidc_views = Blueprint("pyoidc", __name__, url_prefix="")
PREFIX_ROLE = "ACCESS::"
FIELDS_TO_KEEP = ["access_token", "refresh_token", "expires_in", "refresh_expires_in"]


@pyoidc_views.route("/pyoidc/authz")
def authz():
    now = datetime.datetime.now()
    auth = current_app.config["authentication"]
    try:
        auth_response = auth.oidc_client.parse_response(
            AuthorizationResponse, info=request.args, sformat="dict"
        )
        if isinstance(auth_response, ErrorResponse):
            error = f"{auth_response['error']} - {auth_response['error_description']}"
            logger.info("authentication error: %s", error)
            raise AuthenticationException(error, 400)
    except ResponseError as e:
        logger.error("authentication error", exc_info=e)
        raise AuthenticationException(f"{e}", 400)
    code = auth_response["code"]

    if auth_response.get("state") != session.get("state", "undefined"):
        logger.info("unknown state when doing authentication")
        raise AuthenticationException("Unknown state", 400)
    next = request.args.get("next")

    args = {
        "code": code,
        "redirect_uri": auth.get_redirect_uri(),
        "grant_type": "authorization_code",
        "state": auth_response["state"],
    }
    try:
        token_response = auth.get_token(args)
    except MessageException as e:
        logger.warning("invalid token", exc_info=e)
        raise AuthenticationException("invalid token", 400)
    if isinstance(token_response, ErrorResponse):
        error = f"{token_response['error']} - {token_response['error_description']}"
        logger.error(error)
        raise AuthenticationException(error, 400)
    user = extract_user(now, token_response)
    logger.info("OIDC login successful for user %s", user.id)
    logger.info("Accesses for user %s: %s", user.id, ",".join(user.accesses))
    login_user(user)
    flash("Logged in successfully", "success")
    if next:
        return redirect(next)
    else:
        return redirect(url_for("home"))


def extract_user(now, token_response):
    logger.debug("extracting user info from id_token")
    id_token = token_response["id_token"]
    accesses = extract_accesses(id_token)
    extra = {
        "access_token": token_response["access_token"],
        "id_token": id_token.jwt,
        "refresh_token": token_response["refresh_token"],
        "expires_in": now + datetime.timedelta(seconds=token_response["expires_in"]),
        "refresh_expires_in": now
        + datetime.timedelta(seconds=token_response["refresh_expires_in"]),
    }
    user = User(
        id_token["sub"],
        id_token["email"],
        id_token["name"],
        True,
        accesses,
        extra=extra,
    )
    user.save()
    return user


@pyoidc_views.route("/pyoidc/logged_out")
def pyoidc_logged_out():
    logger.info(
        "logging out current user %s",
        current_user.id if current_user.is_authenticated else "Anonymous",
    )
    auth = current_app.config["authentication"]
    try:
        del auth.oidc_client.authz_req[session["state"]]
    except KeyError:
        pass
    logout_user()
    logger.debug("done. redirecting to home")
    return redirect(url_for("home"))


def parse_role(role):
    if not role:
        return
    if not role.startswith(PREFIX_ROLE):
        return
    return role[len(PREFIX_ROLE) :]


def extract_accesses(id_token):
    logger.debug("extracting accesses from id_token")
    realm_accesses = id_token.get("realm_access")
    accesses = []
    if realm_accesses:
        roles = realm_accesses.get("roles")
        for role in roles:
            access = parse_role(role)
            if access:
                accesses.append(access)
    logger.debug("found the following accesses: %s", ",".join(accesses))
    return accesses
