import logging

from flask import Blueprint, flash, redirect, url_for, current_app, request, session
from flask_login import logout_user, login_user
from oic.oauth2 import ErrorResponse
from oic.oic.message import AuthorizationResponse

from ..exceptions import AuthenticationException

logger = logging.getLogger(__name__)

pyoidc_views = Blueprint('pyoidc', __name__, url_prefix='')


@pyoidc_views.route('/pyoidc/authz')
def authz():
    from ..controllers.login_controllers import save_user
    auth = current_app.config['authentication']
    auth_response = auth.oidc_client.parse_response(AuthorizationResponse, info=request.args, sformat="dict")
    if isinstance(auth_response, ErrorResponse):
        raise AuthenticationException(f"{auth_response['error']} - {auth_response['error_description']}", 400)
    code = auth_response["code"]

    if auth_response["state"] != session["state"]:
        raise AuthenticationException('Unknown state', 400)
    args = {
        "code": code
    }

    token_response = auth.oidc_client.do_access_token_request(state=auth_response["state"], request_args=args,
                                                              authn_method="client_secret_basic")
    if isinstance(token_response, ErrorResponse):
        raise AuthenticationException(f"{token_response['error']} - {token_response['error_description']}", 400)
    userinfo = auth.oidc_client.do_user_info_request(state=auth_response["state"])
    if isinstance(userinfo, ErrorResponse):
        raise AuthenticationException(f"{userinfo['error']} - {userinfo['error_description']}", 400)
    user = save_user(userinfo['sub'], userinfo['email'], userinfo['name'])
    login_user(user)
    flash('Logged in successfully', 'success')
    return redirect(url_for('home'))


@pyoidc_views.route('/pyoidc/logged_out')
def pyoidc_logged_out():
    auth = current_app.config['authentication']
    try:
        del auth.oidc_client.authz_req[session['state']]
    except KeyError:
        pass
    logout_user()
    return redirect(url_for('home'))
