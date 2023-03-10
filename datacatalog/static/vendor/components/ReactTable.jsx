import React, {useState} from "react";
import {useGlobalFilter, usePagination, useSortBy, useTable, useExpanded} from "react-table";
import styles from "./ReactTable.css";
import Pagination from "./Pagination.jsx";
import PropTypes from "prop-types";

export default function ReactTable({
    columns,
    data,
    defaultSortColumnId,
    defaultSortOrder,
    defaultSearchPlaceHolder,
    search,
    pagination,
    sort,
}) {
    /* React component to display a sortable, filterable, paginated table.
    * Attributes:
    *   columns: Array
    *       List of columns objects. See 'https://react-table.tanstack.com/docs/api/useTable'
    *       for more info about column properties
    *   data: Array
    *       List of objects to display in the table. Each object should be of the format
    *       { column1Header: value1, column2Header: value2, ... }
    *   defaultSortColumnId: String (Optional)
    *       The header of the column with which data will be sorted by default
    *       Default: ""
    *   defaultSortOrder: String (Optional)
    *       The order in which data will be sorted by default. Anything other than
    *        "desc" will be treated as "asc"
    *        Default: "desc"
    *
    *  Returns:
    *    A React component containing the table, search bar and page buttons
    */

    defaultSortColumnId = defaultSortColumnId || "";
    defaultSortOrder = defaultSortOrder || "desc";
    defaultSearchPlaceHolder = defaultSearchPlaceHolder || "";
    search = search || false;
    pagination = pagination || false;
    sort = sort || false;

    function ReactRow({row}){
        return (
            <tr>
                <td colSpan={visibleColumns.length}>
                    <div className="panel-body">
                        <dl>
                            <dt>
                                    Name
                            </dt>
                            <dd>{row.original["full_name"] || "-"}</dd>
                            <dt>
                                    Address
                            </dt>
                            <dd>{row.original["business_address"] || "-"}</dd>
                            <dt>
                                    Phone Number
                            </dt>
                            <dd>-</dd>
                        </dl>
                    </div>
                </td>
            </tr>
        );
    }
    ReactRow.propTypes = {
        row: PropTypes.shape({
            original: PropTypes.shape({
                "full_name": PropTypes.string.isRequired,
                "business_address": PropTypes.string.isRequired,
            }),
        }),
    };


    const PAGE_SIZE_OPTIONS = [5, 10, 25, 50, 100];
    // Check if column width is defined. If not, the displayed table will keep
    // react-table default behavior in regards to column width.
    // Note that if any column.width is defined, all undefined values
    // will default to 150.
    const columnWidthIsDefault = columns.map(c => !c.width).every(Boolean);

    const [filterInput, setFilterInput] = useState("");

    const {
        //      Basic options
        getTableProps,
        getTableBodyProps,
        headerGroups,
        prepareRow,
        rows,
        visibleColumns,
        //      Filtering options
        setGlobalFilter,
        //      Pagination options
        page,
        state: {pageIndex, pageSize, expanded},
        gotoPage,
        previousPage,
        nextPage,
        setPageSize,
        pageCount,
    } = useTable(
        {
            columns,
            data,
            initialState: {
                sortBy: [
                    {
                        id: defaultSortColumnId,
                        desc: defaultSortOrder === "desc",
                    }
                ],
            },
        },
        useGlobalFilter,
        sort && useSortBy,
        useExpanded,
        pagination && usePagination,
    );

    const handleFilterChange = e => {
        const value = e.target.value;
        setGlobalFilter(value);
        setFilterInput(value);
    };

    const displayedRowsString = pagination ? `Showing  ${page.length} of ${data.length} entries: ` : "";
    return (
        <>
            {pagination &&
                    <div className={styles.filterDisplayOptions}>
                        <div>
                            <span>
                                {"Show "}
                                <select
                                    value={pageSize}
                                    onChange={e => {
                                        setPageSize(Number(e.target.value));
                                    }}
                                >
                                    {PAGE_SIZE_OPTIONS.map(pageSize => (
                                        <option key={pageSize} value={pageSize}>
                                            {pageSize}
                                        </option>
                                    ))}
                                </select>
                                {" entries."}
                            </span>
                        </div>
                        {search &&
                                <div>
                                    {"Filter: "}
                                    <input value={filterInput} onChange={handleFilterChange} type="text"
                                        placeholder={defaultSearchPlaceHolder}/>
                                </div>
                        }
                    </div>
            }
            <table className="table table-striped" {...getTableProps()}>
                <thead>
                    {headerGroups.map((headerGroup, index) => (
                        <tr key={index} {...headerGroup.getHeaderGroupProps()}>
                            {headerGroup.headers.map((column, index) => {
                                return (
                                    <th key={index} width={columnWidthIsDefault ? "" : column.width}
                                        {...column.getHeaderProps(sort && column.getSortByToggleProps())}
                                    >
                                        {column.render("Header")}
                                        <span className={
                                            sort && column.canSort
                                                ? (
                                                    column.isSorted
                                                        ? (
                                                            column.isSortedDesc
                                                                ? `glyphicon glyphicon-triangle-bottom ${styles.columnSortButton}`
                                                                : `glyphicon glyphicon-triangle-top ${styles.columnSortButton}`
                                                        )
                                                        : `glyphicon glyphicon-triangle-right ${styles.columnSortButton}`
                                                )
                                                : styles.columnSortButton
                                        }/>
                                    </th>
                                );
                            })}
                        </tr>
                    ))}
                </thead>
                <tbody {...getTableBodyProps()}>
                    { pagination ?
                        page.map((row, i) => {
                            prepareRow(row);
                            return (
                                <tr key={i} {...row.getRowProps()}>
                                    {row.cells.map((cell, index) => {
                                        return <td key={index} {...cell.getCellProps()}>{cell.render("Cell")}</td>;
                                    })}
                                </tr>
                            );
                        }) :
                        rows.map((row, i) => {
                            prepareRow(row);
                            return (
                                <React.Fragment key={i}>
                                    <tr key={i} {...row.getRowProps()}>
                                        {row.cells.map((cell, index) => {
                                            return <td key={index} {...cell.getCellProps()}>{cell.render("Cell")}</td>;
                                        })}
                                    </tr>
                                    {expanded && row.isExpanded ? (
                                        <ReactRow row={row} />
                                    ) : null}
                                </React.Fragment>
                            );
                        })
                    }
                </tbody>
            </table>
            {pagination &&
                <div className={styles.filterDisplayOptions}>
                    <span>{displayedRowsString}</span>
                    <Pagination
                        currentPage={pageIndex}
                        pageNumber={pageCount}
                        previousPage={previousPage}
                        nextPage={nextPage}
                        gotoPage={gotoPage}
                    />
                </div>
            }
        </>
    );
}

ReactTable.propTypes = {
    columns: PropTypes.array.isRequired,
    data: PropTypes.array.isRequired,
    defaultSortColumnId: PropTypes.string,
    defaultSortOrder: PropTypes.string,
    defaultSearchPlaceHolder: PropTypes.string,
    search: PropTypes.bool,
    pagination: PropTypes.bool,
    sort: PropTypes.bool,
};
