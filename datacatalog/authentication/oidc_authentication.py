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
"""
    datacatalog.authentication.oidc_authentication
    -------------------

    Contains an implementation of class RemoteAuthentication for OIDC authentication

"""
from typing import Tuple, List

from flask import session, redirect
from oidcrp import RPHandler
from oidcrp.configure import Configuration

from . import RemoteAuthentication
from .. import app
from ..exceptions import AuthenticationException

__author__ = 'Valentin Grouès'

logger = app.logger


class OIDCAuthentication(RemoteAuthentication):
    """
    Implementation of class RemoteAuthentication for OIDC authentication
    """

    def __init__(self, service_name: str, config_file: str) -> None:
        """
        Initialize a OIDCAuthentication instance setting the service name
        Service definition will be loaded from config file based on service name
        @param service_name: address and port of the LDAP server
        :type config_file: object
        """
        rp_config = Configuration.create_from_config_file(config_file)
        self.service_name = service_name
        from .oidc_views import oidc_rp_views
        app.register_blueprint(oidc_rp_views)
        # Initialize the oidc_provider after views to be able to set correct urls
        self.rph = RPHandler(rp_config.base_url, rp_config.clients, services=rp_config.services,
                             hash_seed=rp_config.hash_seed, keyjar=None, jwks_path=app.config.get('URL_PREFIX', ''),
                             httpc_params=rp_config.httpc_params)
        # register client so that hash2issuer is not empty in case of multiple python processed
        # (when using gunicorn for instance)
        self.rph.client_setup(service_name, "")
        logger.info("OIDCAuthentication initialized for service %s", service_name)

    def authenticate_user(self) -> Tuple[bool, List[str]]:
        """
        Redirects to OIDC IdP
        @return: raises an exception if unsuccessful
        returns a redirect to OIDC provider
        """
        link = self.service_name
        args = {}
        session['op_hash'] = link
        result = self.rph.begin(link, **args)
        return redirect(result['url'], 303)

    def get_logout_url(self):
        try:
            _info = self.rph.logout(state=session['state'])
        except KeyError:
            return None
        return _info['url']

    def get_rp(self, op_hash):
        try:
            _iss = self.rph.hash2issuer[op_hash]
        except KeyError:
            logger.error('Unkown issuer: {} not among {}'.format(
                op_hash, list(self.rph.hash2issuer.keys())))
            raise AuthenticationException("Unknown hash")
        try:
            rp = self.rph.issuer2rp[_iss]
        except KeyError:
            raise AuthenticationException("Couldn't find client for %s" % _iss)
        return rp
