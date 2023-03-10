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


from tests.base_test import BaseTest
from unittest import mock
from mimetypes import guess_type
from datacatalog.connector.file_storage_connectors.webdav_file_connector import (
    WebdavFileStorageConnector,
)

__author__ = "Francois Ancien"


def mocked_request(*args, **kwargs):
    class MockResponse:
        def __init__(self, content, status_code, headers=None):
            self.content = content
            self.status_code = status_code
            self.ok = status_code not in [404, 500]
            if headers:
                self.headers = headers

    if args[0] == "PROPFIND":
        if args[1] == "http://correct-query.com":
            return MockResponse(
                b'<?xml version="1.0" encoding="utf-8"?>\n<D:multistatus xmlns:D="DAV:">\n<D:response '
                b'xmlns:lp1="DAV:" '
                b'xmlns:lp2="http://apache.org/dav/props/">\n<D:href>/public/datacatalog_documents/project'
                b"/dc9a4cc0-147a-11eb-b51f-8c8590c45a21/</D:href>\n<D:propstat>\n<D:prop>\n<lp1"
                b":resourcetype><D:collection/></lp1:resourcetype>\n<lp1:creationdate>2022-06-20T07:25:12Z"
                b"</lp1:creationdate>\n<lp1:getlastmodified>Mon, 20 Jun 2022 07:25:12 "
                b'GMT</lp1:getlastmodified>\n<lp1:getetag>"0-5e1dc0132efae"</lp1:getetag>\n<D'
                b":supportedlock>\n<D:lockentry>\n<D:lockscope><D:exclusive/></D:lockscope>\n<D:locktype"
                b"><D:write/></D:locktype>\n</D:lockentry>\n<D:lockentry>\n<D:lockscope><D:shared/></D"
                b":lockscope>\n<D:locktype><D:write/></D:locktype>\n</D:lockentry>\n</D:supportedlock>\n<D"
                b":lockdiscovery/>\n<D:getcontenttype>httpd/unix-directory</D:getcontenttype>\n</D:prop>\n"
                b"<D:status>HTTP/1.1 200 OK</D:status>\n</D:propstat>\n</D:response>\n<D:response "
                b'xmlns:lp1="DAV:" '
                b'xmlns:lp2="http://apache.org/dav/props/">\n<D:href>/public/datacatalog_documents/project'
                b"/dc9a4cc0-147a-11eb-b51f-8c8590c45a21/._TestProject3.docx</D:href>\n<D:propstat>\n<D"
                b":prop>\n<lp1:resourcetype/>\n<lp1:creationdate>2022-06-20T07:25:27Z</lp1:creationdate>\n"
                b"<lp1:getcontentlength>4096</lp1:getcontentlength>\n<lp1:getlastmodified>Mon, 20 Jun 2022 "
                b'07:25:12 GMT</lp1:getlastmodified>\n<lp1:getetag>"1000-5e1dc0132495b"</lp1:getetag>\n'
                b"<lp2:executable>T</lp2:executable>\n<D:supportedlock>\n<D:lockentry>\n<D:lockscope><D"
                b":exclusive/></D:lockscope>\n<D:locktype><D:write/></D:locktype>\n</D:lockentry>\n<D"
                b":lockentry>\n<D:lockscope><D:shared/></D:lockscope>\n<D:locktype><D:write/></D:locktype"
                b">\n</D:lockentry>\n</D:supportedlock>\n<D:lockdiscovery/>\n<D:getcontenttype>application"
                b"/vnd.openxmlformats-officedocument.wordprocessingml.document</D:getcontenttype>\n</D"
                b":prop>\n<D:status>HTTP/1.1 200 OK</D:status>\n</D:propstat>\n</D:response>\n<D:response "
                b'xmlns:lp1="DAV:" '
                b'xmlns:lp2="http://apache.org/dav/props/">\n<D:href>/public/datacatalog_documents/project'
                b"/dc9a4cc0-147a-11eb-b51f-8c8590c45a21/._TestProject2.txt</D:href>\n<D:propstat>\n<D:prop"
                b">\n<lp1:resourcetype/>\n<lp1:creationdate>2022-06-20T07:25:27Z</lp1:creationdate>\n<lp1"
                b":getcontentlength>4096</lp1:getcontentlength>\n<lp1:getlastmodified>Mon, 20 Jun 2022 "
                b'07:25:12 GMT</lp1:getlastmodified>\n<lp1:getetag>"1000-5e1dc013218d0"</lp1:getetag>\n'
                b"<lp2:executable>T</lp2:executable>\n<D:supportedlock>\n<D:lockentry>\n<D:lockscope><D"
                b":exclusive/></D:lockscope>\n<D:locktype><D:write/></D:locktype>\n</D:lockentry>\n<D"
                b":lockentry>\n<D:lockscope><D:shared/></D:lockscope>\n<D:locktype><D:write/></D:locktype"
                b">\n</D:lockentry>\n</D:supportedlock>\n<D:lockdiscovery/>\n<D:getcontenttype>text/plain"
                b"</D:getcontenttype>\n</D:prop>\n<D:status>HTTP/1.1 200 "
                b'OK</D:status>\n</D:propstat>\n</D:response>\n<D:response xmlns:lp1="DAV:" '
                b'xmlns:lp2="http://apache.org/dav/props/">\n<D:href>/public/datacatalog_documents/project'
                b"/dc9a4cc0-147a-11eb-b51f-8c8590c45a21/._TestProject.pdf</D:href>\n<D:propstat>\n<D:prop"
                b">\n<lp1:resourcetype/>\n<lp1:creationdate>2022-06-20T07:25:27Z</lp1:creationdate>\n<lp1"
                b":getcontentlength>4096</lp1:getcontentlength>\n<lp1:getlastmodified>Mon, 20 Jun 2022 "
                b'07:25:12 GMT</lp1:getlastmodified>\n<lp1:getetag>"1000-5e1dc0131bd69"</lp1:getetag>\n'
                b"<lp2:executable>T</lp2:executable>\n<D:supportedlock>\n<D:lockentry>\n<D:lockscope><D"
                b":exclusive/></D:lockscope>\n<D:locktype><D:write/></D:locktype>\n</D:lockentry>\n<D"
                b":lockentry>\n<D:lockscope><D:shared/></D:lockscope>\n<D:locktype><D:write/></D:locktype"
                b">\n</D:lockentry>\n</D:supportedlock>\n<D:lockdiscovery/>\n<D:getcontenttype>application"
                b"/pdf</D:getcontenttype>\n</D:prop>\n<D:status>HTTP/1.1 200 "
                b'OK</D:status>\n</D:propstat>\n</D:response>\n<D:response xmlns:lp1="DAV:" '
                b'xmlns:lp2="http://apache.org/dav/props/">\n<D:href>/public/datacatalog_documents/project'
                b"/dc9a4cc0-147a-11eb-b51f-8c8590c45a21/._testProject4.xlsx</D:href>\n<D:propstat>\n<D"
                b":prop>\n<lp1:resourcetype/>\n<lp1:creationdate>2022-06-20T07:25:27Z</lp1:creationdate>\n"
                b"<lp1:getcontentlength>4096</lp1:getcontentlength>\n<lp1:getlastmodified>Mon, 20 Jun 2022 "
                b'07:25:12 GMT</lp1:getlastmodified>\n<lp1:getetag>"1000-5e1dc01329947"</lp1:getetag>\n'
                b"<lp2:executable>T</lp2:executable>\n<D:supportedlock>\n<D:lockentry>\n<D:lockscope><D"
                b":exclusive/></D:lockscope>\n<D:locktype><D:write/></D:locktype>\n</D:lockentry>\n<D"
                b":lockentry>\n<D:lockscope><D:shared/></D:lockscope>\n<D:locktype><D:write/></D:locktype"
                b">\n</D:lockentry>\n</D:supportedlock>\n<D:lockdiscovery/>\n<D:getcontenttype>application"
                b"/vnd.openxmlformats-officedocument.spreadsheetml.sheet</D:getcontenttype>\n</D:prop>\n<D"
                b":status>HTTP/1.1 200 OK</D:status>\n</D:propstat>\n</D:response>\n<D:response "
                b'xmlns:lp1="DAV:" '
                b'xmlns:lp2="http://apache.org/dav/props/">\n<D:href>/public/datacatalog_documents/project'
                b"/dc9a4cc0-147a-11eb-b51f-8c8590c45a21/testProject4.xlsx</D:href>\n<D:propstat>\n<D:prop"
                b">\n<lp1:resourcetype/>\n<lp1:creationdate>2022-06-20T07:25:12Z</lp1:creationdate>\n<lp1"
                b":getcontentlength>0</lp1:getcontentlength>\n<lp1:getlastmodified>Mon, 20 Jun 2022 "
                b'07:25:12 GMT</lp1:getlastmodified>\n<lp1:getetag>"0-5e1dc012bcebb"</lp1:getetag>\n<lp2'
                b":executable>T</lp2:executable>\n<D:supportedlock>\n<D:lockentry>\n<D:lockscope><D"
                b":exclusive/></D:lockscope>\n<D:locktype><D:write/></D:locktype>\n</D:lockentry>\n<D"
                b":lockentry>\n<D:lockscope><D:shared/></D:lockscope>\n<D:locktype><D:write/></D:locktype"
                b">\n</D:lockentry>\n</D:supportedlock>\n<D:lockdiscovery/>\n<D:getcontenttype>application"
                b"/vnd.openxmlformats-officedocument.spreadsheetml.sheet</D:getcontenttype>\n</D:prop>\n<D"
                b":status>HTTP/1.1 200 OK</D:status>\n</D:propstat>\n</D:response>\n<D:response "
                b'xmlns:lp1="DAV:" '
                b'xmlns:lp2="http://apache.org/dav/props/">\n<D:href>/public/datacatalog_documents/project'
                b"/dc9a4cc0-147a-11eb-b51f-8c8590c45a21/TestProject3.docx</D:href>\n<D:propstat>\n<D:prop"
                b">\n<lp1:resourcetype/>\n<lp1:creationdate>2022-06-20T07:25:12Z</lp1:creationdate>\n<lp1"
                b":getcontentlength>0</lp1:getcontentlength>\n<lp1:getlastmodified>Mon, 20 Jun 2022 "
                b'07:25:12 GMT</lp1:getlastmodified>\n<lp1:getetag>"0-5e1dc012af99c"</lp1:getetag>\n<lp2'
                b":executable>T</lp2:executable>\n<D:supportedlock>\n<D:lockentry>\n<D:lockscope><D"
                b":exclusive/></D:lockscope>\n<D:locktype><D:write/></D:locktype>\n</D:lockentry>\n<D"
                b":lockentry>\n<D:lockscope><D:shared/></D:lockscope>\n<D:locktype><D:write/></D:locktype"
                b">\n</D:lockentry>\n</D:supportedlock>\n<D:lockdiscovery/>\n<D:getcontenttype>application"
                b"/vnd.openxmlformats-officedocument.wordprocessingml.document</D:getcontenttype>\n</D"
                b":prop>\n<D:status>HTTP/1.1 200 OK</D:status>\n</D:propstat>\n</D:response>\n<D:response "
                b'xmlns:lp1="DAV:" '
                b'xmlns:lp2="http://apache.org/dav/props/">\n<D:href>/public/datacatalog_documents/project'
                b"/dc9a4cc0-147a-11eb-b51f-8c8590c45a21/TestProject5.zip</D:href>\n<D:propstat>\n<D:prop"
                b">\n<lp1:resourcetype/>\n<lp1:creationdate>2022-06-20T07:25:12Z</lp1:creationdate>\n<lp1"
                b":getcontentlength>0</lp1:getcontentlength>\n<lp1:getlastmodified>Mon, 20 Jun 2022 "
                b'07:25:12 GMT</lp1:getlastmodified>\n<lp1:getetag>"0-5e1dc012cad37"</lp1:getetag>\n<lp2'
                b":executable>T</lp2:executable>\n<D:supportedlock>\n<D:lockentry>\n<D:lockscope><D"
                b":exclusive/></D:lockscope>\n<D:locktype><D:write/></D:locktype>\n</D:lockentry>\n<D"
                b":lockentry>\n<D:lockscope><D:shared/></D:lockscope>\n<D:locktype><D:write/></D:locktype"
                b">\n</D:lockentry>\n</D:supportedlock>\n<D:lockdiscovery/>\n<D:getcontenttype>application"
                b"/zip</D:getcontenttype>\n</D:prop>\n<D:status>HTTP/1.1 200 "
                b'OK</D:status>\n</D:propstat>\n</D:response>\n<D:response xmlns:lp1="DAV:" '
                b'xmlns:lp2="http://apache.org/dav/props/">\n<D:href>/public/datacatalog_documents/project'
                b"/dc9a4cc0-147a-11eb-b51f-8c8590c45a21/TestProject2.txt</D:href>\n<D:propstat>\n<D:prop"
                b">\n<lp1:resourcetype/>\n<lp1:creationdate>2022-06-20T07:25:12Z</lp1:creationdate>\n<lp1"
                b":getcontentlength>0</lp1:getcontentlength>\n<lp1:getlastmodified>Mon, 20 Jun 2022 "
                b'07:25:12 GMT</lp1:getlastmodified>\n<lp1:getetag>"0-5e1dc012a3bc6"</lp1:getetag>\n<lp2'
                b":executable>T</lp2:executable>\n<D:supportedlock>\n<D:lockentry>\n<D:lockscope><D"
                b":exclusive/></D:lockscope>\n<D:locktype><D:write/></D:locktype>\n</D:lockentry>\n<D"
                b":lockentry>\n<D:lockscope><D:shared/></D:lockscope>\n<D:locktype><D:write/></D:locktype"
                b">\n</D:lockentry>\n</D:supportedlock>\n<D:lockdiscovery/>\n<D:getcontenttype>text/plain"
                b"</D:getcontenttype>\n</D:prop>\n<D:status>HTTP/1.1 200 "
                b'OK</D:status>\n</D:propstat>\n</D:response>\n<D:response xmlns:lp1="DAV:" '
                b'xmlns:lp2="http://apache.org/dav/props/">\n<D:href>/public/datacatalog_documents/project'
                b"/dc9a4cc0-147a-11eb-b51f-8c8590c45a21/TestProject.pdf</D:href>\n<D:propstat>\n<D:prop>\n"
                b"<lp1:resourcetype/>\n<lp1:creationdate>2022-06-20T07:25:26Z</lp1:creationdate>\n<lp1"
                b":getcontentlength>59696</lp1:getcontentlength>\n<lp1:getlastmodified>Mon, 20 Jun 2022 "
                b'07:25:12 GMT</lp1:getlastmodified>\n<lp1:getetag>"e930-5e1dc012edfe3"</lp1:getetag>\n'
                b"<lp2:executable>T</lp2:executable>\n<D:supportedlock>\n<D:lockentry>\n<D:lockscope><D"
                b":exclusive/></D:lockscope>\n<D:locktype><D:write/></D:locktype>\n</D:lockentry>\n<D"
                b":lockentry>\n<D:lockscope><D:shared/></D:lockscope>\n<D:locktype><D:write/></D:locktype"
                b">\n</D:lockentry>\n</D:supportedlock>\n<D:lockdiscovery/>\n<D:getcontenttype>application"
                b"/pdf</D:getcontenttype>\n</D:prop>\n<D:status>HTTP/1.1 200 "
                b'OK</D:status>\n</D:propstat>\n</D:response>\n<D:response xmlns:lp1="DAV:" '
                b'xmlns:lp2="http://apache.org/dav/props/">\n<D:href>/public/datacatalog_documents/project'
                b"/dc9a4cc0-147a-11eb-b51f-8c8590c45a21/._TestProject5.zip</D:href>\n<D:propstat>\n<D:prop"
                b">\n<lp1:resourcetype/>\n<lp1:creationdate>2022-06-20T07:25:27Z</lp1:creationdate>\n<lp1"
                b":getcontentlength>4096</lp1:getcontentlength>\n<lp1:getlastmodified>Mon, 20 Jun 2022 "
                b'07:25:12 GMT</lp1:getlastmodified>\n<lp1:getetag>"1000-5e1dc0132e95b"</lp1:getetag>\n'
                b"<lp2:executable>T</lp2:executable>\n<D:supportedlock>\n<D:lockentry>\n<D:lockscope><D"
                b":exclusive/></D:lockscope>\n<D:locktype><D:write/></D:locktype>\n</D:lockentry>\n<D"
                b":lockentry>\n<D:lockscope><D:shared/></D:lockscope>\n<D:locktype><D:write/></D:locktype"
                b">\n</D:lockentry>\n</D:supportedlock>\n<D:lockdiscovery/>\n<D:getcontenttype>application"
                b"/zip</D:getcontenttype>\n</D:prop>\n<D:status>HTTP/1.1 200 "
                b"OK</D:status>\n</D:propstat>\n</D:response>\n</D:multistatus>\n ",
                207,
                headers=kwargs.get("headers", None),
            )
        elif args[1] == "http://error-query.com":
            return MockResponse(
                "An error occurred", 500, headers=kwargs.get("headers", None)
            )
        else:
            return MockResponse(None, 404, headers=kwargs.get("headers", None))

    elif args[0] == "existing_folder":
        return MockResponse("", 200, headers=kwargs)
    elif args[0] == "error_folder":
        return MockResponse("", 500, headers=kwargs)
    else:
        return MockResponse("", 404, headers=kwargs)


class TestWebdavConnector(BaseTest):
    @mock.patch(
        "datacatalog.connector.file_storage_connectors.webdav_file_connector.requests.request",
        side_effect=mocked_request,
    )
    def test_webdav_connector_request(self, mock_req):
        url = "http://test-query.com"
        connector = WebdavFileStorageConnector()
        connector.list_files(url)
        self.assertIn(
            mock.call("PROPFIND", url, headers={"Depth": "1"}),
            mock_req.call_args_list,
        )

    @mock.patch(
        "datacatalog.connector.file_storage_connectors.webdav_file_connector.requests.head",
        side_effect=mocked_request,
    )
    def test_webdav_connector_folder_exists(self, mock_req):
        connector = WebdavFileStorageConnector()
        self.assertTrue(connector.folder_exists("existing_folder"))
        self.assertTrue(connector.folder_exists("error_folder"))
        self.assertFalse(connector.folder_exists("missing_folder"))
        self.assertIn(
            mock.call("existing_folder", allow_redirects=True, timeout=1),
            mock_req.call_args_list,
        )

    @mock.patch(
        "datacatalog.connector.file_storage_connectors.webdav_file_connector.requests.request",
        side_effect=mocked_request,
    )
    def test_webdav_connector_listed_files(self, mock_req):
        connector = WebdavFileStorageConnector()
        returned_files = connector.list_files("http://correct-query.com")
        call_args = mock_req.call_args.args
        self.assertEqual(len(returned_files), 5)
        self.assertEqual(mock_req.side_effect(*call_args).status_code, 207)

        for file in returned_files:
            self.assertTrue(
                {"path", "name", "size", "format", "lastModified"}.issubset(
                    set(file.keys())
                )
            )

    @mock.patch(
        "datacatalog.connector.file_storage_connectors.webdav_file_connector.requests.request",
        side_effect=mocked_request,
    )
    def test_webdav_connector_files_format(self, mock_req):
        connector = WebdavFileStorageConnector()
        returned_files = connector.list_files("http://correct-query.com")
        call_args = mock_req.call_args.args
        self.assertEqual(mock_req.side_effect(*call_args).status_code, 207)
        for file in returned_files:
            self.assertEqual(guess_type(file["name"])[0], file["format"])

    @mock.patch(
        "datacatalog.connector.file_storage_connectors.webdav_file_connector.requests.request",
        side_effect=mocked_request,
    )
    def test_webdav_connector_no_files(self, mock_req):
        connector = WebdavFileStorageConnector()
        returned_files = connector.list_files("http://empty-query.com")
        call_args = mock_req.call_args.args

        self.assertEqual(returned_files, [])
        self.assertEqual(mock_req.side_effect(*call_args).status_code, 404)

    @mock.patch(
        "datacatalog.connector.file_storage_connectors.webdav_file_connector.requests.request",
        side_effect=mocked_request,
    )
    def test_webdav_connector_error(self, mock_req):
        connector = WebdavFileStorageConnector()
        returned_files = connector.list_files("http://error-query.com")
        call_args = mock_req.call_args.args

        self.assertEqual(returned_files, None)
        self.assertEqual(mock_req.side_effect(*call_args).status_code, 500)
