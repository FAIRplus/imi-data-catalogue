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
import datetime
import logging
from abc import abstractmethod, ABCMeta

from flask_login import current_user

from .storage_handler import StorageHandler

DAYS_THRESHOLD_VALIDITY = 1

logger = logging.getLogger(__name__)


class DownloadHandler(StorageHandler, metaclass=ABCMeta):
    @abstractmethod
    def get_links(self, user, dataset):
        pass

    @abstractmethod
    def create_link(self, user, dataset):
        pass

    def get_or_create(self, user, dataset):
        logger.info(
            "getting or creating link for user %s and entity %s",
            current_user.id,
            dataset.id,
        )
        links = self.get_links(user, dataset)
        if links:
            logger.info(
                "existing links found for user %s and entity %s",
                current_user.id,
                dataset.id,
            )
            valid_links = []
            for link in links:
                if link[
                    "expiration_datetime"
                ] < datetime.datetime.today() + datetime.timedelta(
                    days=DAYS_THRESHOLD_VALIDITY
                ):
                    continue
                valid_links.append(link)
            valid_links.sort(key=lambda x: x["expiration_datetime"], reverse=True)
            if valid_links:
                link = valid_links[0]
                logger.info(
                    "existing and still valid link found for user %s and entity %s: %s",
                    current_user.id,
                    dataset.id,
                    link,
                )
                return link
        logger.info(
            "no valid link found for user %s and entity %s, will create one",
            current_user.id,
            dataset.id,
        )
        return self.create_link(user, dataset)
