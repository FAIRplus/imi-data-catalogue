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
    datacatalog.connector.entities_connector
    -------------------

   Module containing the WebdavFileStorageConnector class


"""
import logging
import requests
import os
from requests.exceptions import ConnectTimeout
from typing import Optional
from xml.etree import ElementTree
from datetime import datetime
from .file_storage_connector import FileStorageConnector

__author__ = "Francois Ancien"

logger = logging.getLogger(__name__)


class WebdavFileStorageConnector(FileStorageConnector):
    FOLDER_CHECK_TIMEOUT = 1

    def list_files(self, folder: str) -> Optional[list]:
        """
        Returns the list of files stored (folder excluded) in the folder given in parameters

        Parameters:
            folder: The folder to list files from. (default: folder from
        """
        response = requests.request("PROPFIND", folder, headers={"Depth": "1"})

        if response.ok:
            return self.parse_webdav_response(response.content, folder)

        elif response.status_code == 404:
            return []

        else:
            return None

    def folder_exists(self, folder: str) -> bool:
        """
        Checks if the given folder exists.

        Returns:
            bool: True if folder was found, else False
        """
        try:
            response = requests.head(
                folder, allow_redirects=True, timeout=self.FOLDER_CHECK_TIMEOUT
            )
        except ConnectTimeout as e:
            logger.error(e)
            return False

        return response.status_code != 404

    @staticmethod
    def parse_webdav_response(xml_response: str, query_url: str) -> list:
        """
        Parse the response from a PROPFIND query to return the list
        of available files

        Returns:
            list: A list of dictionaries with the following keys:
                - path: The link towards the file for a GET request
                - name: The name of the file
                - size: The size of the files in bytes
                - last_modified: The date of last modification (python datetime)
                - format: a string giving the format of the file
        """
        tree = ElementTree.fromstring(xml_response)
        file_list = []
        for response_tag in tree.iter("{DAV:}response"):
            href = response_tag.find("{DAV:}href")
            propstat = response_tag.find("{DAV:}propstat")
            logger.debug(f"Parsing XML for entry {href.text}")
            logger.debug([i for i in propstat.itertext()])
            for prop in propstat.findall("{DAV:}prop"):
                file_name = os.path.split(href.text)[-1]
                if file_name.startswith("."):
                    continue

                content_type = prop.find("{DAV:}getcontenttype")
                if content_type is None or content_type.text == "httpd/unix-directory":
                    continue

                size = prop.find("{DAV:}getcontentlength")
                date = prop.find("{DAV:}getlastmodified")
                file_list.append(
                    {
                        "path": f"{query_url}/{file_name}",
                        "name": file_name,
                        "size": size.text,
                        # Example of getlastmodified returned by webdav-r3lab: Tue, 19 Nov 2019 16:27:41 GMT
                        "lastModified": datetime.strptime(
                            date.text, "%a, %d %b %Y %H:%M:%S %Z"
                        ).strftime("%Y-%m-%dT%H:%M:%S"),
                        "format": content_type.text,
                    }
                )

        return file_list
