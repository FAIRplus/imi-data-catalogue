import base64
import datetime
import logging
from typing import Optional
from urllib.parse import urlencode

import requests
from flask import session, redirect, flash, request, url_for, Response
from flask_login import logout_user

from oic import rndstr
from oic.exception import MessageException
from oic.oauth2 import GrantError, ErrorResponse
from oic.oic import Client, Token
from oic.oic.message import (
    RegistrationResponse,
    TokenErrorResponse,
    AccessTokenResponse,
    OpenIDSchema,
)
from oic.utils.authn.client import CLIENT_AUTHN_METHOD

from . import RemoteAuthentication
from .pyoidc_views import extract_user, extract_accesses
from .. import app
from ..exceptions import AuthenticationException
from .. import login_manager
from ..models.user import User

logger = logging.getLogger(__name__)

SKEW = 2  # for token verification, allow a short time difference with the OIDC server


class PyOIDCAuthentication(RemoteAuthentication):
    def __init__(
        self, base_url, client_id: str, client_secret: str, idp_url: str
    ) -> None:
        logger.info("PyOIDCAuthentication initialized for idp_url %s", idp_url)
        self.oidc_client = Client(client_authn_method=CLIENT_AUTHN_METHOD)
        self.base_url = base_url
        self.redirect_url = self.base_url + "/pyoidc/authz"
        logout_redirect_url = self.base_url + "/pyoidc/logged_out"
        info = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": [self.redirect_url],
            "post_logout_redirect_uris": [logout_redirect_url],
        }
        self.provider_conf = self.oidc_client.provider_config(idp_url)
        self.provider = self.provider_conf["issuer"]
        client_reg = RegistrationResponse(**info)
        self.oidc_client.store_registration_info(client_reg)
        from .pyoidc_views import pyoidc_views

        app.register_blueprint(pyoidc_views)
        self.oidc_client.post_logout_redirect_uris = [logout_redirect_url]
        self.oidc_client.redirect_uris = [self.redirect_url]

    @staticmethod
    @login_manager.unauthorized_handler
    def unauthorized_user() -> Response:
        """
        Callback to replace the default login_manager.unauthorized() behavior and
        avoid the "Please log in" flashed message.
        Due to redirection, this message appeared at the same time as the
        "Successfully logged in" message.

        @return: Response. A redirect response towards the login page.
        """
        return redirect(url_for(login_manager.login_view, next=request.full_path), 302)

    def authenticate_user(self, username=None, password=None):
        logger.info("redirecting user to OIDC server for authentication")
        session["state"] = rndstr()
        session["nonce"] = rndstr()
        redirect_uri = self.get_redirect_uri()
        args = {
            "client_id": self.oidc_client.client_id,
            "response_type": "code",
            "scope": ["openid"],
            "nonce": session["nonce"],
            "redirect_uri": redirect_uri,
            "state": session["state"],
        }

        auth_req = self.oidc_client.construct_AuthorizationRequest(request_args=args)
        login_url = auth_req.request(self.oidc_client.authorization_endpoint)
        return redirect(login_url, 303)

    def get_logout_url(self, user: Optional[User] = None) -> str:
        logout_url = self.oidc_client.end_session_endpoint
        # Specify to which URL the OP should return the user after
        # log out. That URL must be registered with the OP at client
        # registration.
        logout_dict = {
            "post_logout_redirect_uri": self.oidc_client.registration_response[
                "post_logout_redirect_uris"
            ][0],
        }
        if user and user.is_authenticated:
            id_token_hint = user.extra.get("id_token")
            logout_dict["id_token_hint"] = id_token_hint
        logout_url += "?" + urlencode(logout_dict)
        return logout_url

    def check_and_refresh(self, user):
        logger.debug(
            "check access token and eventually refresh token and userinfo for user %s",
            user.id,
        )
        now = datetime.datetime.now()
        expires_in = user.extra.get("expires_in")
        if not expires_in:
            logger.debug("expires_in not found, will not login user")
            user.destroy()
            return None
        if expires_in > now:
            logger.debug("access token, still valid, we don't refresh")
            return user
        logger.debug("access token is not valid anymore")
        refresh_expires_in = user.extra.get("refresh_expires_in")
        if not refresh_expires_in or refresh_expires_in < now:
            logger.info(
                "refresh_expires_in not found, or expired, we don't login user %s",
                user.id,
            )
            flash("Your session expired", category="error")
            user.destroy()
            user.extra = {}
            user.save()
            return None

        logger.debug("refresh_token is still valid, we refresh the tokens")
        try:
            refresh_token = user.extra.get("refresh_token")
            token = Token()
            token.access_token = user.extra.get("access_token")
            token.replaced = False
            token.refresh_token = refresh_token
            refresh_response = self.oidc_client.do_access_token_refresh(
                state=session["state"], token=token
            )
            if isinstance(refresh_response, ErrorResponse):
                reason = refresh_response.get(
                    "error_description", refresh_response.get("error", "error")
                )
                flash(reason, category="error")
                user.extra = {}
                user.save()
                logger.warning(
                    "Was not able to refresh access token for user %s. User will be logged out.",
                    user.id,
                )
                logger.warning(reason)
                return None
            user = extract_user(now, refresh_response)
            logger.debug("refresh successful")
        except GrantError as e:
            flash("Your session expired", category="error")
            logger.warning(
                "Was not able to refresh access token for user %s. User will be logged out.",
                user.id,
            )
            logger.warning(e)
            user.extra = {}
            user.save()
            return None
        return user

    def refresh_user(self, user):
        logger.info("refreshing userinfo for user %s", user.id)
        try:
            access_token = user.extra.get("access_token")
            user_response = requests.request(
                "GET",
                self.oidc_client.userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if not user_response.ok:
                logger.error("error retrieving userinfo: %s", user_response.text)
                raise AuthenticationException("error retrieving userinfo")
            user_info = OpenIDSchema(**user_response.json())
            user_info.verify(keyjar=self.oidc_client.keyjar, skew=SKEW)
            if user_info["sub"] != user.id:
                logger.error(
                    "invalid sub when refreshing user info for user %s", user.id
                )
                raise AuthenticationException("invalid sub")
            user.displayname = user_info["name"]
            user.email = user_info["email"]
            user.accesses = extract_accesses(user_info)
            user.save()
        except (KeyError, MessageException, AuthenticationException) as e:
            logger.error("could not retrieve user info, will logout user")
            logger.error(e)
            logout_user()
            raise AuthenticationException("could not retrieve user info")

    def validate_user(self, user):
        return True

    def get_authentication_headers(self):
        credentials = "{}:{}".format(
            self.oidc_client.client_id, self.oidc_client.client_secret
        )
        basic_auth = "Basic {}".format(
            base64.urlsafe_b64encode(credentials.encode("utf-8")).decode("utf-8")
        )
        return {"Authorization": basic_auth}

    def get_token(self, request_params):
        logger.debug("getting access token")
        auth_header = self.get_authentication_headers()
        token_request = requests.post(
            self.oidc_client.token_endpoint, data=request_params, headers=auth_header
        )
        if not token_request.ok:
            error_description = (
                f"an error occurred while retrieving the authentication token"
                f" (http status: {token_request.status_code})"
            )
            logger.error(token_request.text)
            return TokenErrorResponse(
                error="authentication error",
                error_description=error_description,
            )
        response = token_request.json()

        if "error" in response:
            return TokenErrorResponse(**response)
        else:
            token = AccessTokenResponse(**response)
            token.verify(keyjar=self.oidc_client.keyjar, skew=SKEW)
            return token

    def get_redirect_uri(self):
        logger.debug("building redirect uri")
        redirect_uri = self.redirect_url
        next = request.args.get("next", "")
        if next and next[-1] == "?":
            next = next[:-1]
        if next:
            url_prefix = app.config.get("URL_PREFIX", "")
            if next.startswith(url_prefix):
                url_prefix = ""
            redirect_uri += f"?next={url_prefix}{next}"
        logger.debug("redirect uri is %s", redirect_uri)
        return redirect_uri
