import logging

from flask import Blueprint, request, current_app, session, flash, redirect, url_for
from flask_login import login_user, logout_user
from oidcservice.exception import OidcServiceError

from ..exceptions import AuthenticationException

logger = logging.getLogger(__name__)

oidc_rp_views = Blueprint('oidc_rp', __name__, url_prefix='')


@oidc_rp_views.route('/authz_cb/<op_hash>')
def authz_cb(op_hash):
    from ..controllers.login_controllers import save_user
    res = finalize(op_hash, request.args)
    logger.debug(res['userinfo'])
    sub = res['userinfo']['sub']
    user = save_user(sub, res['userinfo']['email'], res['userinfo']['name'])
    login_user(user)
    flash('Logged in successfully', 'success')
    return redirect('/')


@oidc_rp_views.route('/oidc/logged_out')
def oidc_logged_out():
    logout_user()
    return redirect(url_for('home'))


def finalize(op_hash, request_args):
    authentication = current_app.config['authentication']

    rp = authentication.get_rp(op_hash)
    if hasattr(rp, 'status_code') and rp.status_code != 200:
        logger.error(rp.response[0].decode())
        raise AuthenticationException("Wrong status code", status=403)

    session['client_id'] = rp.service_context.get('client_id')

    session['state'] = request_args.get('state')

    if session['state']:
        iss = rp.session_interface.get_iss(session['state'])
    else:
        raise AuthenticationException('Unknown state', 400)

    session['session_state'] = request_args.get('session_state', '')
    try:
        res = authentication.rph.finalize(iss, request_args)
    except OidcServiceError as e:
        # replay attack prevention, is that code was already used before
        raise AuthenticationException(str(e), 403)
    except Exception as e:
        raise AuthenticationException(str(e), 403)

    if 'userinfo' in res:
        endpoints = {}
        for k, v in rp.service_context.get('provider_info').items():
            if k.endswith('_endpoint'):
                endp = k.replace('_', ' ')
                endp = endp.capitalize()
                endpoints[endp] = v

        kwargs = {}

        # Do I support session status checking ?
        _status_check_info = rp.service_context.add_on.get('status_check')
        if _status_check_info:
            # Does the OP support session status checking ?
            _chk_iframe = rp.service_context.get('provider_info').get('check_session_iframe')
            if _chk_iframe:
                kwargs['check_session_iframe'] = _chk_iframe
                kwargs["status_check_iframe"] = _status_check_info['rp_iframe_path']

        # Where to go if the user clicks on logout
        kwargs['logout_url'] = "{}/logout".format(rp.service_context.base_url)

        return res
    else:
        raise AuthenticationException(res['error'], 400)
