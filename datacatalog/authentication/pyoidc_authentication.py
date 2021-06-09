import logging
from urllib.parse import urlencode

from flask import session, redirect
from jwkest.jwe import alg2keytype
from oic import rndstr

from . import RemoteAuthentication
from .. import app

logger = logging.getLogger(__name__)
from oic.oic import Client
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from oic.oic.message import RegistrationResponse


class PyOIDCAuthentication(RemoteAuthentication):

    def __init__(self, base_url, client_id: str, client_secret: str, idp_url: str) -> None:
        self.oidc_client = Client(client_authn_method=CLIENT_AUTHN_METHOD)
        self.base_url = base_url
        logout_redirect_url = self.base_url + '/pyoidc/logged_out'
        redirect_url = self.base_url + '/pyoidc/authz'
        info = {"client_id": client_id,
                "client_secret": client_secret, "redirect_uris": [redirect_url],
                "post_logout_redirect_uris": [logout_redirect_url]}
        provider_conf = self.oidc_client.provider_config(idp_url)
        self.provider = provider_conf["issuer"]
        client_reg = RegistrationResponse(**info)
        self.oidc_client.store_registration_info(client_reg)
        from .pyoidc_views import pyoidc_views
        app.register_blueprint(pyoidc_views)
        self.oidc_client.post_logout_redirect_uris = [logout_redirect_url]
        self.oidc_client.redirect_uris = [redirect_url]

    def authenticate_user(self):
        session["state"] = rndstr()
        session["nonce"] = rndstr()
        args = {
            "client_id": self.oidc_client.client_id,
            "response_type": "code",
            "scope": ["openid"],
            "nonce": session["nonce"],
            "redirect_uri": self.oidc_client.redirect_uris[0],
            "state": session["state"]
        }

        auth_req = self.oidc_client.construct_AuthorizationRequest(request_args=args)
        login_url = auth_req.request(self.oidc_client.authorization_endpoint)
        return redirect(login_url, 303)

    def get_logout_url(self) -> str:
        logout_url = self.oidc_client.end_session_endpoint
        # Specify to which URL the OP should return the user after
        # log out. That URL must be registered with the OP at client
        # registration.
        logout_url += "?" + urlencode(
            {"post_logout_redirect_uri": self.oidc_client.registration_response[
                "post_logout_redirect_uris"][0]})
        return logout_url


