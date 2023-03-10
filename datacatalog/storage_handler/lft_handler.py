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

from .download_handler import DownloadHandler
from ..exceptions import DownloadsHandlerLinksException

logger = logging.getLogger(__name__)

PLATFORM_NAME = "LCSB Aspera"


class LFTStorageHandler(DownloadHandler):
    template = "lft"

    @staticmethod
    def can_handle(storage):
        return storage.get("platform") == PLATFORM_NAME

    def __init__(self, lft_client, namespace_id, base_link_url):
        super().__init__()
        self.base_link_url = base_link_url
        self.lft_client = lft_client
        self.namespace_id = namespace_id

    def get_links(self, user, dataset):
        logger.info(
            "getting links for user %s and entity %s", current_user.id, dataset.id
        )
        try:
            links = self.lft_client.links_list(
                self.namespace_id, dataset.id, user.username
            )
        except Exception as e:
            logger.error(
                "An error occurred while getting list of downloads links for user %s and entity %s",
                current_user.id,
                dataset.id,
                exc_info=e,
            )
            raise DownloadsHandlerLinksException(
                "An error occurred while retrieving the download links"
            )
        results = []
        for link in links:
            link_dict = link.to_dict()
            link_dict["absolute_url"] = self.base_link_url + link_dict.get("url", "")
            results.append(link_dict)
        return results

    def create_link(self, user, dataset):
        logger.info(
            "creating link for user %s and entity %s", current_user.id, dataset.id
        )
        try:
            link = self.lft_client.create_link(
                self.namespace_id, dataset.id, user.username
            )
            link_dict = link.to_dict()
            link_dict["absolute_url"] = self.base_link_url + link_dict.get("url", "")
            return link_dict
        except Exception as e:
            logger.error(
                "An error occurred while creating download link "
                "for user %s and entity %s",
                current_user.id,
                dataset.id,
                exc_info=e,
            )
            raise DownloadsHandlerLinksException(
                "An error occurred while creating a download link"
            )
