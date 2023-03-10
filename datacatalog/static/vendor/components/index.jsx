// coding=utf-8
// DataCatalog
// Copyright (C) 2020  University of Luxembourg
//
// This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU Affero General Public License as
// published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

"use strict";
import "./download_link.jsx";
import "./search_autocomplete.jsx";
import "./applications_data_table.jsx";
import "./contact_data_table.jsx";
import "./attachments_table.jsx";

export function postData(url, data, csrf) {
    let body;
    const headers = {};
    body = JSON.stringify(data);
    headers["Content-Type"] = "application/json";
    headers["X-CSRFToken"] = csrf;
    return fetch(url, {
        method: "POST",
        cache: "no-cache",
        headers,
        redirect: "error",
        body
    });
}

export function handleErrors(response) {
    return response.text().then(body => {
        let bodyJson, bodyText;
        try {
            bodyJson = body && JSON.parse(body);
        } catch (e) {
            bodyText = body;
        }
        if (!response.ok) {
            const error = (bodyJson && bodyJson.message) || response.statusText.toLowerCase();
            return Promise.reject(error);
        }
        return bodyJson || bodyText;
    });
}
