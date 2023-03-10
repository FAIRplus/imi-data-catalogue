#  coding=utf-8
#  DataCatalog
#  Copyright (C) 2020  University of Luxembourg
#
#  This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging

from flask_login import current_user

from .access_handler import ApplicationState
from .rems_handler import RemsAccessHandler

logger = logging.getLogger(__name__)


class RemsOidcAccessHandler(RemsAccessHandler):
    HIDE_APPROVED = True

    def has_access(self, dataset):
        logger.info(
            "Checking if user %s has access to dataset %s", current_user.id, dataset.id
        )
        application_state = super().has_access(dataset)
        logger.debug("RemsAccessHandler access from rems: %s", application_state)
        oidc_access = dataset.id in current_user.accesses
        logger.debug("access status from OIDC accesses: %s", oidc_access)
        if oidc_access:
            logger.info("approved access found")
            return ApplicationState.approved
        elif application_state is ApplicationState.submitted:
            logger.info("no approved access found but pending application")
            return application_state
        else:
            logger.info("no approved access found nor pending application")
            return False
