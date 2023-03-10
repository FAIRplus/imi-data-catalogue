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

import React, {useMemo} from "react";
import PropTypes from "prop-types";
import ReactDOM from "react-dom";
import ReactTable from "./ReactTable.jsx";

let domContainer = document.querySelector("#attachments-datatable");

function parseData(data){
    data.map(entry => {
        entry.lastModified = new Date(entry["lastModified"]);
    });
    return data;
}

function formatToIcon(format){
    if (format.includes("pdf"))
        return "picture_as_pdf";
    else if (format.includes("zip") || format.includes("rar") || format.includes("7z"))
        return "folder_zip";
    else if (format.includes("xls")
            || format.includes("csv")
            || format.includes("tab-separated-values")
            || format.includes("spreadsheet"))
        return "table_chart";
    else if (format.includes("text") || format.includes("word") || format.includes("doc"))
        return "text_snippet";
    else if (format.includes("image"))
        return "image";
    else
        return "note";
}

function formatByteSize(bytes){
    if (bytes == 0)
        return "0B";

    const k = 1024;
    const decimals = 1;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + sizes[i];
}

function DisplayError() {
    return(
        <span>An error occurred while retrieving the attached files.</span>
    );
}

function DisplayTable({dataObject}) {
    const IconCell = ({value}) => <i className={"material-icons"}>{formatToIcon(value)}</i>;
    IconCell.propTypes = {
        value: PropTypes.string,
    };

    let columns = useMemo(
        () => [
            {
                Header: "Type",
                accessor: "format",
                disableSortBy: true,
                width: "5%",
                Cell: IconCell,
            },
            {
                Header: "Name",
                accessor: "name",
                width: "65%",
                Cell: ({value}) => decodeURIComponent(value),
            },
            {
                Header: "Size",
                accessor: "size",
                width: "12%",
                Cell: ({value}) => formatByteSize(value),
            },
            {
                Header: "Last modified",
                accessor: "lastModified",
                sortType: "datetime",
                Cell: ({value}) => value.toLocaleDateString(),
                width: "13%",
            },
            {
                Header: "",
                accessor: "download",
                disableSortBy: true,
                Cell: (cell) =>
                    <a
                        href={cell.row.original.path}
                        download={cell.row.original.name}
                    >
                        <i className={"material-icons attachment-download"}>download</i>
                    </a>,
            },
        ]
    );

    if (!dataObject.data.length) {
        return DisplayError();
    }
    else {
        const data = parseData(dataObject.data);

        return (
            <ReactTable
                columns={columns}
                data={data}
                defaultSortColumnId={"name"}
                defaultSortOrder={"asc"}
                sort={true}
            />
        );
    }
}

DisplayTable.propTypes = {
    dataObject: PropTypes.shape({
        data: PropTypes.array.isRequired
    }),
};

if (domContainer !== null) {
    const url = domContainer.getAttribute("data-url");

    const request = new XMLHttpRequest();
    request.open("GET", url);
    request.responseType = "json";
    request.send();

    request.onload = () => {
        ReactDOM.render(<DisplayTable dataObject={request.response} />, domContainer);
    };

    request.onerror = () => {
        console.error(request.response);
        ReactDOM.render(<DisplayError />);
    };
}
