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
    datacatalog.forms
    -------------------

    Package for forms classes

"""
from urllib.parse import urlparse, urljoin

from flask import redirect, request, Response, url_for
from flask_wtf import FlaskForm
from wtforms import HiddenField

__author__ = 'Valentin Grouès'


def is_safe_url(target_url: str) -> bool:
    """
    Check if the target url is safe to redirect to
    The goal is to protect users from redirect phishing attacks
    This method check if the target_url belongs to the same host as the datacatalog
    It also checks that the scheme is either http or https
    @param target_url: the url to check
    @return: true if the url is considered safe to redirects to
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target_url))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def get_redirect_target() -> str:
    """
    Extract the redirect url from the request
    Will look first in the get parameters and then in the referrer.
    @return: returns the redirect url
    """
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target


class RedirectForm(FlaskForm):
    """
    Class meant to be used as parent class for forms that need to redirect the users after submission
    """
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or url_for('home')

    def redirect(self) -> Response:
        """
        Check if the url is safe and then redirect to user to this url
        Redirects to home if no target found
        @return: the redirect
        """
        if is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or '/')
