import React from "react";
import PropTypes from "prop-types";

export default function Pagination({
    currentPage,
    pageNumber,
    previousPage,
    nextPage,
    gotoPage,
}) {
    const isFirstPage = currentPage === 0;
    const isLastPage = currentPage === pageNumber - 1;

    return (
        <ul className="pagination">
            <li className={isFirstPage ? "disabled" : ""}>
                <a href="#" onClick={(e) => {
                    e.preventDefault();
                    previousPage();
                }}>«</a>
            </li>
            <li style={currentPage < 2 ? {display: "none"} : {}}>
                <a onClick={(e) => {
                    e.preventDefault();
                    gotoPage(currentPage - 2);
                }
                } href="#">{currentPage - 1}</a>
            </li>
            <li style={currentPage < 1 ? {display: "none"} : {}}>
                <a onClick={(e) => {
                    e.preventDefault();
                    gotoPage(currentPage - 1);
                }} href="#">{currentPage}</a>
            </li>
            <li className={"active"}>
                <a>{currentPage + 1}</a>
            </li>
            <li
                style={currentPage >= pageNumber - 1 ? {display: "none"} : {}}>
                <a onClick={(e) => {
                    e.preventDefault();
                    gotoPage(currentPage + 1);
                }
                } href="#">{currentPage + 2}</a>
            </li>
            <li
                style={currentPage >= pageNumber - 2 ? {display: "none"} : {}}>
                <a href="#" onClick={(e) => {
                    e.preventDefault();
                    gotoPage(currentPage + 2);
                }}>{currentPage + 3}</a>
            </li>
            <li className={isLastPage ? "disabled" : ""} onClick={() => nextPage()}>
                <a href="#" onClick={(e) => {
                    e.preventDefault();
                    nextPage();
                }}>»</a>
            </li>
        </ul>
    );
}

Pagination.propTypes = {
    currentPage: PropTypes.number.isRequired,
    pageNumber: PropTypes.number.isRequired,
    previousPage: PropTypes.func.isRequired,
    nextPage: PropTypes.func.isRequired,
    gotoPage: PropTypes.func.isRequired
};
