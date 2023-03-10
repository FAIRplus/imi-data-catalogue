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

from time import time
from unittest.mock import MagicMock

from flask import url_for, session, current_app
from oic.oauth2 import ErrorResponse
from oic.oic import OpenIDSchema, IdToken
from oic.oic.message import (
    AuthorizationResponse,
    AuthorizationErrorResponse,
    AuthorizationRequest,
    AccessTokenResponse,
)

import datacatalog
from datacatalog import app
from datacatalog.authentication.pyoidc_authentication import PyOIDCAuthentication
from datacatalog.authentication.pyoidc_views import pyoidc_logged_out, authz
from datacatalog.exceptions import AuthenticationException
from tests.base_test import BaseTest

__author__ = "Nirmeen Sallam"


def _create_id_token(issuer, client_id, nonce):
    id_token = IdToken(
        **{
            "iss": issuer,
            "sub": "test_sub",
            "name": "Test User",
            "email": "test_user@uni.lu",
            "aud": client_id,
            "nonce": nonce,
            "exp": time() + 60,
        }
    )
    id_token.jws_header = {"alg": "RS256"}
    return id_token


class TestPyOIDCviews(BaseTest):
    AUTH_RESPONSE = AuthorizationResponse(
        **{"code": "test_auth_code", "state": "test_state"}
    )
    AUTH_ERROR_RESPONSE = AuthorizationErrorResponse(
        **{"error": "unauthorized_client", "error_description": "something went wrong"}
    )
    ISSUER = "https://issuer.example.com"
    CLIENT_ID = "client1"
    AUTH_REQUEST = AuthorizationRequest(
        **{"state": "test_state", "nonce": "test_nonce"}
    )
    TOKEN_RESPONSE = AccessTokenResponse(
        **{
            "access_token": "test_token",
            "expires_in": 3600,
            "id_token": _create_id_token(ISSUER, CLIENT_ID, AUTH_REQUEST["nonce"]),
            "id_token_jwt": "test_id_token_jwt",
            "refresh_token": "test_refresh_token",
            "refresh_expires_in": 6000,
        }
    )
    TOKEN_ERROR_RESPONSE = ErrorResponse()
    USERINFO_RESPONSE = OpenIDSchema(
        **{"sub": "test_sub", "email": "test_user@uni.lu", "name": "Test User"}
    )

    with app.app_context():
        authentication = PyOIDCAuthentication(
            current_app.config.get("BASE_URL"),
            current_app.config.get("PYOIDC_CLIENT_ID"),
            current_app.config.get("PYOIDC_CLIENT_SECRET"),
            current_app.config.get("PYOIDC_IDP_URL"),
        )
        app.config["authentication"] = authentication

    def test_authz_should_handle_error_response(self):
        datacatalog.authentication.pyoidc_views.AuthorizationResponse = MagicMock()
        datacatalog.authentication.pyoidc_views.AuthorizationResponse.return_value = (
            self.AUTH_ERROR_RESPONSE
        )

        with self.assertRaises(AuthenticationException):
            authz()

    def test_authz_should_detect_state_mismatch(self):
        session["state"] = "testsessionkey"

        datacatalog.authentication.pyoidc_views.AuthorizationResponse = MagicMock()
        datacatalog.authentication.pyoidc_views.AuthorizationResponse.return_value = (
            self.AUTH_RESPONSE
        )

        with self.assertRaises(AuthenticationException):
            authz()

    def test_authz_should_handle_token_error_response(self):
        session["state"] = "testsessionkey"

        self.AUTH_RESPONSE["state"] = session.get("state")
        datacatalog.authentication.pyoidc_views.AuthorizationResponse = MagicMock()
        datacatalog.authentication.pyoidc_views.AuthorizationResponse.return_value = (
            self.AUTH_RESPONSE
        )

        with self.assertRaises(AuthenticationException):
            authz()

    def test_authz_success(self):
        session["state"] = "testsessionkey"
        self.AUTH_RESPONSE["state"] = session.get("state")
        current_app.config["authentication"].get_token = MagicMock()
        current_app.config[
            "authentication"
        ].get_token.return_value = self.TOKEN_RESPONSE

        current_app.config[
            "authentication"
        ].oidc_client.do_user_info_request = MagicMock()
        current_app.config[
            "authentication"
        ].oidc_client.do_user_info_request.return_value = self.USERINFO_RESPONSE

        datacatalog.authentication.pyoidc_views.login_user = MagicMock()
        datacatalog.authentication.pyoidc_views.login_user.return_value = True

        datacatalog.authentication.pyoidc_views.AuthorizationResponse = MagicMock()
        datacatalog.authentication.pyoidc_views.AuthorizationResponse.return_value = (
            self.AUTH_RESPONSE
        )

        authz()
        flash_message = dict(session["_flashes"]).get("success")

        # Assert
        self.assertIsNotNone(flash_message, session["_flashes"])
        self.assertEqual(flash_message, "Logged in successfully")

    def test_pyoidc_logged_out(self):
        self.assertEqual(url_for("home"), pyoidc_logged_out().location)
