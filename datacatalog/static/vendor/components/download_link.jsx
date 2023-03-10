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

import React, {Component} from "react";
import PropTypes from "prop-types";
import ReactDOM from "react-dom";
import {handleErrors, postData} from "./index.jsx";

let domContainer = document.querySelector(".downloadLinkHolder");
let csrf = document.getElementById("csrf-token").getAttribute("content");

class Alert extends Component {

    constructor(props) {
        super(props);
    }

    render() {
        const {message, removeAlert} = this.props;
        if (!message) return null;
        return <div className="alert alert-dismissible alert-danger" role="alert">
            <button type="button" className="close" onClick={removeAlert}>×</button>
            <strong>{message}</strong>
        </div>;
    }
}

Alert.propTypes = {
    message: PropTypes.string.isRequired,
    removeAlert: PropTypes.func.isRequired
};

class DownloadLink extends Component {

    constructor(props) {
        super(props);
        this.state = {
            open: false,
            loading: false,
            link: null,
            error: null,
            hideAlert: false
        };
    }

    onDownloadClicked = (event) => {
        this.setState({loading: true, error: null});
        const {entityId} = this.props;
        event.preventDefault();
        this.getOrCreateLink(entityId).then((link) => this.openModal(link)).catch((error) => {
            if (Object.hasOwn(error, "message")) {
                error = `An error occurred, please reload the page (${error.message})`;
            }
            this.setState({"loading": false, error, hideAlert: false});
        });
    };
    openModal = (link) => {
        document.body.classList.add("modal-open");
        this.setState({link, open: true, loading: false});
    };
    closeModal = () => {
        document.body.classList.remove("modal-open");
        this.setState({open: false});
    };
    getOrCreateLink = () => {
        const {csrf, entityId, downloadLinkApiUrl} = this.props;
        return postData(downloadLinkApiUrl, {entityId}, csrf).then(handleErrors).then((body) => body.data);
    };

    render() {
        const {hideAlert, error, open, link, loading} = this.state;
        return (
            <>
                {open && <div id={"link_modal"} className="modal fade in" role="dialog" tabIndex="-1">
                    <div className="modal-dialog" role="document">
                        <div className="modal-content">
                            <div className="modal-header">
                                <button type="button" onClick={this.closeModal.bind(this)} className="close"
                                    data-dismiss="modal" aria-hidden="true">×
                                </button>
                                <h3>Your Access Link</h3>
                            </div>
                            <div className="modal-body">
                                <div className={"accessLink__urlBlock"}>
                                    <p className={"accessLink__urlIcon"}><i className="material-icons">link</i></p>
                                    <a className={"accessLink__url"}
                                        href={link.absolute_url}>{link.absolute_url}</a>
                                    <p/>
                                </div>
                                <div className={"accessLink__meta"}>
                                    <div><p className={"accessLink__label"}><i
                                        className="material-icons text-success">vpn_key</i>Password
                                    </p><p className={"accessLink__metaValue"}>{link.page_password}</p></div>
                                    <div>
                                        <p className={"accessLink__label"}><i
                                            className="material-icons text-success">timer</i>Valid until</p>
                                        <p className={"accessLink__metaValue"}>{link.expiration_date_string}</p>
                                    </div>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button onClick={this.closeModal.bind(this)} className="btn btn-raised"
                                    data-dismiss="modal" aria-hidden="true">Close
                                </button>
                            </div>
                        </div>
                    </div>
                </div>}
                <div className="button-link input-group">
                    <div className="input-group-btn">
                        {!loading && <i className="material-icons">download</i>}
                        {loading && <div className="lds-ring">
                            <div></div>
                            <div></div>
                            <div></div>
                            <div></div>
                        </div>}
                    </div>
                    <a className="btn button-link-text"
                        href="#" onClick={this.onDownloadClicked.bind(this)}>Download Data</a>
                </div>
                {!hideAlert && error && <Alert message={error} removeAlert={() => this.setState({hideAlert: true})}/>}
            </>
        );
    }
}

DownloadLink.propTypes = {
    csrf: PropTypes.string.isRequired,
    entityId: PropTypes.string.isRequired,
    downloadLinkApiUrl: PropTypes.string.isRequired,
};

if (domContainer !== null) {
    ReactDOM.render(<DownloadLink csrf={csrf} downloadLinkApiUrl={domContainer.dataset.downloadLinkApiUrl} entityId={domContainer.dataset.entityId}/>, domContainer);
}
