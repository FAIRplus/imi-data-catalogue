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
    datacatalog.models.dataset
    -------------------

   Module containing the Dataset entity


"""
import logging
from collections import defaultdict

from . import EntityWithSlugs
from .. import app, DEFAULT_USE_RESTRICTIONS_ICONS
from ..solr.solr_orm import SolrAutomaticQuery
from ..solr.solr_orm_entity import SolrEntity
from ..solr.solr_orm_fields import SolrField, SolrDateTimeField, SolrFloatField, SolrJsonField

logger = logging.getLogger(__name__)


class Dataset(SolrEntity, EntityWithSlugs):
    """
    Subclass of SolrEntity that is used as default entity
    """
    # specifies the list of compatibles connectors
    COMPATIBLE_CONNECTORS = ['Ckan', 'Limesurvey', 'Geo', 'Json', 'Dats', 'Daisy']

    title = SolrField("title")
    data_standards = SolrField("data_standards", multivalued=True)
    data_types = SolrField("data_types", multivalued=True)
    dataset_created = SolrDateTimeField("dataset_created")
    dataset_modified = SolrDateTimeField("dataset_modified")
    version = SolrField("version", indexed=False)

    dataset_link_href = SolrField("dataset_link_href")
    dataset_link_label = SolrField("dataset_link_label")
    fair_assessment_details = SolrField('fair_assessment_details')
    fair_assessment_details_link = SolrField('fair_assessment_details_link')
    fair_indicators = SolrField("fair_indicators")
    fair_indicators_href = SolrField("fair_indicators_href")
    fair_score_mandatory_indicators = SolrFloatField("fair_score_mandatory_indicators")
    fair_score_overall = SolrFloatField("fair_score_overall")
    fair_score_recommended_indicators = SolrFloatField("fair_score_recommended_indicators")
    fair_evaluation = SolrField("fair_evaluation")
    use_restrictions = SolrJsonField("use_restrictions")
    use_restrictions_class_label = SolrField("use_restrictions_class_label", multivalued=True)
    platform = SolrField("platform")
    query_class = SolrAutomaticQuery
    samples_number = SolrField("samples_number", indexed=False)
    treatment_category = SolrField("treatment_category", multivalued=True)
    treatment_name = SolrField("treatment_name")
    disease = SolrField("disease", multivalued=True)
    samples_type = SolrField("samples_type", multivalued=True)

    def __init__(self, title: str = None, entity_id: str = None) -> None:
        """
        Initialize a new Dataset instance with title and entity_id
        @param title: title of the Dataset
        @param entity_id:  id of the Dataset
        """
        super().__init__(entity_id)
        self.title = title

    def set_computed_values(self):
        results = set()
        for restriction in self.use_restrictions or []:
            class_label = restriction.get('use_class_label')
            if class_label:
                results.add(class_label)
        self.use_restrictions_class_label = list(results)

    @property
    def use_restrictions_by_type(self):
        results = defaultdict(list)
        mapping_icons = app.config.get('USE_RESTRICTIONS_ICONS', DEFAULT_USE_RESTRICTIONS_ICONS)
        icons = {}
        for use_restriction in self.use_restrictions:
            if use_restriction.get('use_restriction_rule'):
                results[use_restriction.get('use_restriction_rule')].append(use_restriction)
        for restriction_type in results:
            icons[restriction_type] = mapping_icons.get(restriction_type)
        return results, icons
