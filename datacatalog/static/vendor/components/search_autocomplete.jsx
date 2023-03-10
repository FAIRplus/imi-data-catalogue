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
import ReactDOM from "react-dom";
import PropTypes from "prop-types";


let domContainer = document.querySelector("#autocomplete_input");

class Autocomplete extends Component {
    constructor(props) {
        super(props);
        this.inputRef = React.createRef();
        this.btnRef = React.createRef();
        const {query, totalEntityTitle, totalTerms, titlesSearchLink} = props;
        //Number of suggested items to appear during entering input query,
        //Total is divided in 2 between search terms and entity titles to appear
        let totalEntityTitleState = totalEntityTitle;
        let totalTermsState = totalTerms;
        if (totalEntityTitle > 0 || totalTerms > 0) {
            if (!totalEntityTitle)
                totalEntityTitleState = 0;
            if (!totalTerms)
                totalTermsState = 0;

        } else {
            totalEntityTitleState = 3;
            totalTermsState = 3;
        }

        this.state = {
            active: 0,
            filtered: [],
            isShow: false,
            inputText: query,
            suggestions: [],
            suggestionsTerms: [],
            totalTermsState,
            totalEntityTitleState
        };

        //get entity title list
        fetch(titlesSearchLink)
            .then((res) => res.json())
            .then((json) => {
                const entityTitles = [];
                for (const entryIndex in json.data) {
                    entityTitles.push({"title": json.data[entryIndex].title, "id": json.data[entryIndex].id});
                }
                this.setState({
                    suggestions: entityTitles
                });
            });
    }

    onInputChange = (e) => {
        const {suggestions, totalTermsState} = this.state;
        const {termsSearchLink, entityName} = this.props;
        const suggestionsList = suggestions.filter(x => x.title !== null);
        const input = e.currentTarget.value;
        const newFilteredSuggestions = suggestionsList.filter(
            suggestion =>
                suggestion.title.toLowerCase().indexOf(input.toLowerCase()) > -1
        );
        //get search term list

        let currLink = termsSearchLink + input.toLowerCase().trim();
        if (input.trim() && totalTermsState > 0) {
            fetch(currLink)
                .then((res) => res.json())
                .then((json) => {
                    let suggestionsList = [];
                    if (json.data.raw_response.suggest["suggest_" + entityName][input.toLowerCase().trim()].numFound > 0) {
                        suggestionsList = json.data.raw_response.suggest["suggest_" + entityName][input.toLowerCase().trim()].suggestions;
                    } else {
                        console.log("no suggested terms found");
                    }
                    const terms = [];
                    const suggestionLowerCase = newFilteredSuggestions.map(function (s) {
                        return s.title.toLowerCase();
                    });
                    for (const suggestedTermIndex in suggestionsList) {
                        const term = suggestionsList[suggestedTermIndex].term;
                        if (suggestionLowerCase.length < 0 || !suggestionLowerCase.includes(term.toLowerCase())) {
                            terms.push(term);
                        }
                    }
                    this.setState({
                        suggestionsTerms: terms
                    });

                });
        }

        this.setState({
            active: 0,
            filtered: newFilteredSuggestions,
            isShow: true,
            inputText: e.currentTarget.value
        });
    };

    onItemClick(e) {
        if (e.title) {
            this.inputRef.current.value = e.title;
        } else {
            this.inputRef.current.value = e;
            this.btnRef.current.click();
        }
    }

    onInputKeyDown = (e) => {
        const {filtered, suggestionsTerms, totalTermsState, totalEntityTitleState} = this.state;
        const {entityLinkPattern} = this.props;
        if (e.keyCode === 13) { // enter key
            e.preventDefault();
            const suggestionsCombined = suggestionsTerms.slice(0, totalTermsState).concat(filtered.slice(0, totalEntityTitleState));
            if (suggestionsCombined.length > 0) {
                this.inputRef.current.value = suggestionsCombined[this.state.active].title;
                if (suggestionsCombined[this.state.active].title) {
                    this.inputRef.current.value = suggestionsCombined[this.state.active].title;
                    window.location.href = entityLinkPattern + suggestionsCombined[this.state.active].id;
                } else {
                    this.inputRef.current.value = suggestionsCombined[this.state.active];
                    this.btnRef.current.click();
                }
            }

        } else if (e.keyCode === 38 && this.state.active !== 0) { // up arrow
            this.setState({active: this.state.active - 1});
        } else if (e.keyCode === 40) { // down arrow
            const {filtered, suggestionsTerms} = this.state;
            const suggestionsCombined = suggestionsTerms.slice(0, totalTermsState).concat(filtered.slice(0, totalEntityTitleState));
            (this.state.active + 1 === suggestionsCombined.length) ? this.setState({active: 0}) : this.setState({active: this.state.active + 1});
        }
    };

    renderAutocomplete() {
        const {filtered, suggestionsTerms, isShow, inputText, totalTermsState, totalEntityTitleState} = this.state;
        const {entityName, entityLinkPattern} = this.props;
        let divider;
        let autocompleteHeaderKeyword;
        let autocompleteHeaderEntity;
        if (filtered.length > 0 && totalTermsState > 0 && suggestionsTerms.length > 0 && totalEntityTitleState > 0) {
            divider = <div className="dropdown-divider"></div>;
        }
        if (filtered.length > 0 && totalEntityTitleState > 0) {
            autocompleteHeaderEntity = <div className="autocomplete_header">{entityName + "s"}</div>;
        }
        if (suggestionsTerms.length > 0 && totalTermsState > 0) {
            autocompleteHeaderKeyword = <div className="autocomplete_header">Keywords</div>;
        }

        if (isShow && inputText &&
                ((filtered.length > 0 && totalEntityTitleState > 0)
                        || (suggestionsTerms.length > 0 && totalTermsState > 0))) {
            return (
                <div className="autocomplete dropdown">
                    {autocompleteHeaderKeyword}
                    {suggestionsTerms.slice(0, totalTermsState).map((suggestion, index) => {
                        let className = "dropdown-item";
                        if (index === this.state.active) {
                            className += " active";
                        }

                        return (
                            <div className={className} key={index} onClick={() => this.onItemClick(suggestion)}>
                                {suggestion}
                            </div>
                        );
                    })
                    }
                    {divider}
                    {autocompleteHeaderEntity}
                    {filtered.slice(0, totalEntityTitleState).map((suggestion, index) => {
                        let className = "dropdown-item";
                        if (suggestionsTerms.slice(0, totalTermsState).length + index === this.state.active) {
                            className += " active";
                        }
                        return (
                            <a href={entityLinkPattern + suggestion.id} id={suggestion.id}
                                key={suggestion.id}>
                                <div className={className}
                                    key={suggestionsTerms.slice(0, totalTermsState).length + index}
                                    data-entity-id={suggestion.id}
                                    onClick={() => this.onItemClick(suggestion)}>
                                    {suggestion.title}
                                </div>
                            </a>
                        );
                    })}
                </div>
            );

        }
        return <></>;
    }

    render() {

        const {inputText} = this.state;


        return (
            <>
                <input title="query" placeholder="enter your query here" type="text" name="query"
                    id="query" className="form-control"
                    value={inputText}
                    onChange={this.onInputChange}
                    onKeyDown={this.onInputKeyDown} ref={this.inputRef}
                    autoComplete={"off"}/>
                <span className="input-group-addon">
                    <button type="submit" className="btn btn-primary btn-raised" id="search-button" ref={this.btnRef}>
                        <i className="material-icons">search</i>
                    </button>
                </span>
                {this.renderAutocomplete()}
            </>
        );
    }

}

Autocomplete.propTypes = {
    query: PropTypes.string.isRequired,
    titlesSearchLink: PropTypes.string.isRequired,
    termsSearchLink: PropTypes.string.isRequired,
    entityLinkPattern: PropTypes.string.isRequired,
    entityName: PropTypes.string.isRequired,
    totalEntityTitle: PropTypes.string.isRequired,
    totalTerms: PropTypes.string.isRequired,
};

if (domContainer !== null) {
    const query = domContainer.getAttribute("data-query");
    const titlesSearchLink = domContainer.getAttribute("data-api-entities-link");
    const termsSearchLink = domContainer.getAttribute("data-api-search-autocomplete-entities-link");
    const entityLinkPattern = domContainer.getAttribute("data-entity-link");
    const totalEntityTitle = domContainer.getAttribute("data-total-entity-titles");
    const totalTerms = domContainer.getAttribute("data-total-terms");
    const entityName = domContainer.getAttribute("data-entity-name");

    ReactDOM.render(<Autocomplete entityName={entityName} totalTerms={totalTerms} totalEntityTitle={totalEntityTitle}
        query={query}
        entityLinkPattern={entityLinkPattern} titlesSearchLink={titlesSearchLink}
        termsSearchLink={termsSearchLink}
    />, domContainer);
}
