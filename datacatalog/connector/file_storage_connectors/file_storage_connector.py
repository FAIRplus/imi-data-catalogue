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

   Module containing the FileStorageConnector abstract class


"""

from abc import ABCMeta, abstractmethod
from typing import Optional


class FileStorageConnector(metaclass=ABCMeta):
    @abstractmethod
    def list_files(self, folder: str) -> Optional[list]:
        pass

    @staticmethod
    @abstractmethod
    def folder_exists(folder: str) -> bool:
        pass
