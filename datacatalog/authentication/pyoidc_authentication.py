import logging
from urllib.parse import urlencode

from flask import session, redirect
from oic import rndstr

from . import RemoteAuthentication
from .. import app

logger = logging.getLogger(__name__)
from oic.oic import Client
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from oic.oic.message import RegistrationResponse
from flask import request


class PyOIDCAuthentication(RemoteAuthentication):

    def __init__(self, base_url, client_id: str, client_secret: str, idp_url: str) -> None:
        self.oidc_client = Client(client_authn_method=CLIENT_AUTHN_METHOD)
        self.base_url = base_url
        self.redirect_url = self.base_url + '/pyoidc/authz'
        logout_redirect_url = self.base_url + '/pyoidc/logged_out'
        info = {"client_id": client_id,
                "client_secret": client_secret, "redirect_uris": [self.redirect_url],
                "post_logout_redirect_uris": [logout_redirect_url]}
        provider_conf = self.oidc_client.provider_config(idp_url)
        self.provider = provider_conf["issuer"]
        client_reg = RegistrationResponse(**info)
        self.oidc_client.store_registration_info(client_reg)
        from .pyoidc_views import pyoidc_views
        app.register_blueprint(pyoidc_views)
        self.oidc_client.post_logout_redirect_uris = [logout_redirect_url]
        self.oidc_client.redirect_uris = [self.redirect_url]

    def authenticate_user(self):
        next = request.args.get('next', '')
        if next and next[-1] == '?':
            next = next[:-1]
        session["state"] = rndstr()
        session["nonce"] = rndstr()
        redirect_uri = self.redirect_url
        if next:
            redirect_uri += f'?next={next}'
        args = {
            "client_id": self.oidc_client.client_id,
            "response_type": "code",
            "scope": ["openid"],
            "nonce": session["nonce"],
            "redirect_uri": redirect_uri,
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


