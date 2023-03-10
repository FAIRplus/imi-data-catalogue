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

let domContainer = document.querySelector("#applications-datatable");

function parseData(data){
    data = JSON.parse(data);
    data.map(entry => {
        entry.creationDate = new Date(entry["creation_date_string"]);
    });
    return data;
}

function DisplayTable() {
    const IconCell = ({value}) => {
        const icon = {
            "submitted": "hourglass",
            "approved": "ok-circle",
            "rejected": "remove-circle",
            "closed": "remove-circle",
            "revoked": "remove-circle",
        }[value];
        const color = {
            "submitted": "info",
            "approved": "success",
        }[value] || "default";

        const classString = "glyphicon glyphicon-" + icon + " text-" + color;
        return (
            (icon)
                ? <span title={value} style={{fontSize: "20px"}} className={classString}/>
                : value
        );
    };
    IconCell.propTypes = {
        value: PropTypes.string.IsRequired,
    };

    const LinkCell = ( cell ) => {
        return (
            <a href={cell.row.original["entity_url"]}>
                {cell.value}
            </a>
        );
    };

    let columns = useMemo(
        () => [
            {
                Header: "Id",
                accessor: "ext_id",
                width: "20%",
            },
            {
                Header: "Dataset",
                accessor: "dataset",
                width: "60%",
                Cell: LinkCell,
            },
            {
                Header: "State",
                accessor: "state",
                Cell: IconCell,
                disableGlobalFilter: true,
                disableSortBy: true,
                width: "5%",
            },
            {
                Header: "Created on",
                accessor: "creationDate",
                disableGlobalFilter: true,
                sortType: "datetime",
                Cell: ({value}) => value.toLocaleDateString(),
                width: "15%",
            },
        ]
    );

    const data = parseData(domContainer.getAttribute("data-applications"));

    // TODO: Test once user actions are implemented
    const userActions = domContainer.getAttribute("data-actions-allowed");
    const closeUrl = domContainer.getAttribute("data-close-url");

    if (userActions) {
        columns.push({
            Header: "Actions",
            accessor: "actions",
            disableGlobalFilter: true,
            disableSortBy: true,
            Cell: () => {
                return (
                    <a
                        className={"closeApplication"}
                        data-close-url={closeUrl}
                        href={""}
                    >
                        <span title={"cancel my application"} className={"glyphicon glyphicon-remove text-danger"}/>
                    </a>
                );
            },
        });
    }

    return (
        <ReactTable
            columns={columns}
            data={data}
            defaultSortColumnId={"creationDate"}
            search={true}
            pagination={true}
            sort={true}
        />
    );
}

if (domContainer !== null) {
    ReactDOM.render(<DisplayTable/>, domContainer);
}
