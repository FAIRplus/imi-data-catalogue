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
from abc import abstractmethod, ABCMeta
from enum import Enum

from ..models.user import User

logger = logging.getLogger(__name__)


class AccessHandler(metaclass=ABCMeta):

    def __init__(self, user: User):
        self.user = user
        self.datasets = self.get_datasets()

    @abstractmethod
    def get_datasets(self):
        pass

    @abstractmethod
    def has_access(self, dataset):
        pass

    @abstractmethod
    def apply(self, dataset, form):
        pass

    @abstractmethod
    def create_form(self, dataset, form_data):
        pass

    @abstractmethod
    def supports_listing_accesses(self):
        pass

    @abstractmethod
    def requires_logged_in_user(self):
        pass

    def grant(self, dataset):
        self.datasets.append(dataset)


class ApplicationState(Enum):
    approved = 'approved'
    draft = 'draft'
    closed = 'closed'
    submitted = 'submitted'
    revoked = 'revoked'
    rejected = 'rejected'


class Application:
    def __init__(self, state: ApplicationState, entity_id, entity_title, creation_date):
        self.creation_date = creation_date
        self.entity_id = entity_id
        self.entity_title = entity_title
        self.state = state
