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
    datacatalog.models
    -------------------

   Package containing SolrEntity subclasses and corresponding SolrQuery subclasses


"""
import logging

from .. import app
from ..solr.solr_orm import SolrQuery
from ..solr.solr_orm_fields import SolrField

logger = logging.getLogger(__name__)


class DatasetQuery(SolrQuery):
    """
    SolrQuery child class for the Dataset entity
    """

    # The sort options that will be offered on the search page
    SORT_OPTIONS = ["dataset_created", "title"]
    # labels of the sort options that will be offered on the search page
    SORT_LABELS = ["dataset_created", "title"]
    # allows giving more weight to some fields than others for default search
    BOOST = app.config.get("SOLR_BOOST", "dataset_title^5 dataset_text_^1")
    # default sort option
    DEFAULT_SORT = app.config.get("SOLR_DEFAULT_SORT", "dataset_created")


class EntityWithSlugs:
    slugs = SolrField("slugs", multivalued=True)
