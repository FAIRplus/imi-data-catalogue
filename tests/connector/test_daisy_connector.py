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
from unittest.mock import patch, Mock

from datacatalog import app
from datacatalog.connector.daisy_connector import DaisyConnector
from tests.base_test import BaseTest

__author__ = 'Valentin Grouès'

from datacatalog.models.dataset import Dataset
from datacatalog.models.project import Project


class TestDaisyConnector(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.solr_orm = app.config['_solr_orm']
        cls.solr_orm.delete_fields()
        cls.solr_orm.create_fields()

    @patch('datacatalog.connector.daisy_connector.requests.get')
    def test_build_all_datasets(self, mock_get):
        response_content = {
            '$schema': 'https://raw.githubusercontent.com/elixir-luxembourg/json-schemas/master/schemas/elu-dataset.json',
            'items': [{'source': 'example.com', 'id_at_source': '1', 'project': 'MDEG2', 'name': 'MDEG2 data',
                       'external_id': '-', 'description': '....', 'elu_uuid': '3d3eddf8-1488-4b98-b46e-701d4e5e986b',
                       'other_external_id': None, 'data_declarations': [
                    {'title': 'MDEG2', 'data_types': ['Metabolomics', 'Methylation_array', 'Clinical_data'],
                     'data_types_notes': '..\n', 'access_category': None, 'access_procedure': None,
                     'subjects_category': 'controls', 'de_identification': 'anonymization', 'consent_status': 'unknown',
                     'has_special_subjects': True, 'special_subjects_description': '2 year old children',
                     'embargo_date': None, 'storage_end_date': None, 'storage_duration_criteria': None,
                     'use_restrictions': [{'use_class': 'PS', 'use_class_label': None,
                                           'use_restriction_note': 'Use is restricted to projects: MDEG2',
                                           'use_restriction_rule': 'CONSTRAINED_PERMISSION'},
                                          {'use_class': 'PUB', 'use_class_label': None,
                                           'use_restriction_note': 'Acknowledgement required.',
                                           'use_restriction_rule': 'CONSTRAINED_PERMISSION'}]}], 'legal_bases': [],
                       'storages': [{'platform': 'master', 'location': 'smb://atlas.uni.lux/LCSB_SPG/Studies/Gambia',
                                     'accesses': ['Ines Thiele']}], 'transfers': [{
                    'partner': 'London School of Hygiene & Tropical Medicine, Medical Research Council  Unit The Gambia',
                    'transfer_details': None,
                    'transfer_date': None}],
                       'contacts': [{'first_name': 'Ines', 'last_name': 'Thiele', 'email': 'inactive.user@uni.lu',
                                     'role': 'Researcher', 'affiliations': [
                               'University of Luxembourg - Luxembourg Centre for Systems Biomedicine']}]}]}
        mock_get.return_value = Mock(ok=True)
        mock_get.return_value.json.return_value = response_content
        daisy_connector = DaisyConnector(app.config.get("DAISY_API_URLS").get('dataset'), Dataset)
        datasets = list(daisy_connector.build_all_entities())
        self.assertEqual(1, len(datasets))
        first_dataset = datasets[0]
        first_dataset.save()
        self.solr_orm.commit()
        retrieved_dataset = Dataset.query.get(first_dataset.id)
        self.assertEqual('MDEG2 data', retrieved_dataset.title)
        self.assertEqual(2, len(retrieved_dataset.use_restrictions))
        self.assertEqual({'Metabolomics', 'Methylation_array', 'Clinical_data'}, set(retrieved_dataset.data_types))

    @patch('datacatalog.connector.daisy_connector.requests.get')
    def test_build_all_projects(self, mock_get):
        response_content = {
            '$schema': 'https://raw.githubusercontent.com/elixir-luxembourg/json-schemas/master/schemas/elu-project.json',
            'items': [{'source': 'example.com', 'acronym': 'CUSHING Syndrome', 'external_id': None,
                       'name': 'Adrenal tumours', 'description': 'Adrenal tumor sequencing',
                       'has_institutional_ethics_approval': True, 'has_national_ethics_approval': False,
                       'institutional_ethics_approval_notes': None, 'national_ethics_approval_notes': 'Not applicable',
                       'start_date': '2013-10-28', 'end_date': None, 'contacts': [
                    {'first_name': 'Jochen', 'last_name': 'SCHNEIDER', 'email': 'jochen.schneider@uni.lu',
                     'role': 'Principal_Investigator',
                     'affiliations': ['University of Luxembourg - Luxembourg Centre for Systems Biomedicine']},
                    {'first_name': 'Patrick', 'last_name': 'MAY', 'email': 'Patrick.May@uni.lu', 'role': 'Researcher',
                     'affiliations': ['University of Luxembourg - Luxembourg Centre for Systems Biomedicine']}],
                       'publications': [{'citation': 'Elbelt et al., 2014, JCEM', 'doi': None}]},
                      {'source': 'example.com', 'acronym': 'P1 Protect Move (FNR INTER)', 'external_id': '-',
                       'name': 'P1: Markers and Mechanisms of Reduced Penetrance in LRRK2 Mutation Carriers',
                       'description': 'While known PD genes are commonly grouped by mode of transmission as ‘dominant’ or ‘recessive’, actual patterns of inheritance and boundaries between dominant and recessive modes are much less well defined than previously thought. Although individuals may harbour an identical mutation for instance in the LRRK2 gene, their disease manifestation and age at onset may vary considerably. So far, only few factors have emerged, which impact on disease penetrance or constitute signs of advanced progression in LRRK2-PD. In this study, we are using a large set of fibroblasts from affected and unaffected individuals with the common G2019S mutation in LRRK2 to validate the specificity of known penetrance markers (such as LRRK2 autophosphorylation). Moreover, we aim to identify novel cellular signals that allow a reliable prediction of PD onset in non-manifesting carriers. To further explore how central to the disease mechanism these markers are, we are developing iPSC-based neuronal models of LRRK2 PD penetrance.',
                       'has_institutional_ethics_approval': True, 'has_national_ethics_approval': True,
                       'institutional_ethics_approval_notes': 'From the University of Lübeck, and the EURAC Research Bolzano',
                       'national_ethics_approval_notes': None, 'start_date': '2017-01-01', 'end_date': '2019-12-31',
                       'contacts': [{'first_name': 'Anne', 'last_name': 'GRÜNEWALD', 'email': 'anne.gruenewald@uni.lu',
                                     'role': 'Principal_Investigator', 'affiliations': [
                               'University of Luxembourg - Luxembourg Centre for Systems Biomedicine']},
                                    {'first_name': 'Sylvie', 'last_name': 'DELCAMBRE',
                                     'email': 'sylvie.delcambre@uni.lu', 'role': 'Researcher', 'affiliations': [
                                        'University of Luxembourg - Luxembourg Centre for Systems Biomedicine']},
                                    {'first_name': 'Enrico', 'last_name': 'GLAAB', 'email': 'enrico.glaab@uni.lu',
                                     'role': 'Researcher', 'affiliations': [
                                        'University of Luxembourg - Luxembourg Centre for Systems Biomedicine']},
                                    {'first_name': 'Jenny', 'last_name': 'GHELFI', 'email': 'jenny.ghelfi@uni.lu',
                                     'role': 'Researcher', 'affiliations': [
                                        'University of Luxembourg - Luxembourg Centre for Systems Biomedicine']},
                                    {'first_name': 'Patrick', 'last_name': 'MAY', 'email': 'Patrick.May@uni.lu',
                                     'role': 'Researcher', 'affiliations': [
                                        'University of Luxembourg - Luxembourg Centre for Systems Biomedicine']}],
                       'publications': [{
                           'citation': 'Grünewald A, Klein C. Urinary LRRK2 phosphorylation: Penetrating the thicket of Parkinson disease? Neurology 2016; 86:984-5.',
                           'doi': None}, {
                           'citation': 'Ouzren, N., Delcambre, S., Ghelfi, J., Seibler, P., Farrer, M. J., König, I., Aasly, J. O., Trinh, J., Klein, C., & Grünewald, A. (2019). MtDNA deletions discriminate affected from unaffected LRRK2 mutation carriers. Annals of Neurology, 86(2), 324-326.',
                           'doi': 'http://hdl.handle.net/10993/39985'}]},
                      {'source': 'example.com', 'acronym': 'Synspread', 'external_id': '-',
                       'name': 'Roles and mechanisms of synuclein and ataxin-3 spreading in Parkinson and Machado-Joseph diseases',
                       'description': 'Symulates how alpha-syn spreads in the brain',
                       'has_institutional_ethics_approval': False, 'has_national_ethics_approval': False,
                       'institutional_ethics_approval_notes': None,
                       'national_ethics_approval_notes': 'Public data from Allen Brain Atlas are used:\r\nhttps://allensdk.readthedocs.io/en/latest/\r\n\r\nOnly the code to analyse these data are stored at LCSB:\r\nhttps://git-r3lab.uni.lu/SBG/synSpread',
                       'start_date': '2015-01-01', 'end_date': '2020-08-30', 'contacts': [
                          {'first_name': 'Ronan', 'last_name': 'Fleming', 'email': 'inactive.user@uni.lu',
                           'role': 'Principal_Investigator',
                           'affiliations': ['University of Luxembourg - Luxembourg Centre for Systems Biomedicine']}],
                       'publications': [{
                           'citation': 'The connectome is necessary but not sufficient for the spread of alpha-synuclein pathology in rats\r\n View ORCID ProfileMiguel A.P. Oliveira,  View ORCID ProfileSylvain Arreckx,  View ORCID ProfileDonato Di Monte,  View ORCID ProfileGerman A. Preciat,  View ORCID ProfileAyse Ulusoy,  View ORCID ProfileRonan M.T. Fleming\r\ndoi: https://doi.org/10.1101/567222',
                           'doi': 'https://www.biorxiv.org/content/10.1101/567222v1'}]},
                      {'source': 'example.com', 'acronym': 'Fanconi_Anemia', 'external_id': '-',
                       'name': 'Fanconi anemia', 'description': None, 'has_institutional_ethics_approval': True,
                       'has_national_ethics_approval': False, 'institutional_ethics_approval_notes': None,
                       'national_ethics_approval_notes': None, 'start_date': '2012-10-28', 'end_date': None,
                       'contacts': [{'first_name': 'Patrick', 'last_name': 'MAY', 'email': 'Patrick.May@uni.lu',
                                     'role': 'Researcher', 'affiliations': [
                               'University of Luxembourg - Luxembourg Centre for Systems Biomedicine']},
                                    {'first_name': 'Rudi', 'last_name': 'BALLING', 'email': 'Rudi.Balling@uni.lu',
                                     'role': 'Principal_Investigator', 'affiliations': [
                                        'University of Luxembourg - Luxembourg Centre for Systems Biomedicine']}],
                       'publications': [{'citation': 'Ameziane et al., 2015, Nature Communications', 'doi': None}]},
                      {'source': 'example.com', 'acronym': 'SH-SY5Y', 'external_id': '-',
                       'name': 'Systems genomics evaluation of the SH-SY5Y neuroblastoma cell line as a model for Parkinson’s disease',
                       'description': 'The human neuroblastoma cell line, SH-SY5Y, is a commonly used cell line in studies related to neurotoxicity, oxidative stress, and neurodegenerative diseases. Although this cell line is often used as a cellular model for Parkinson’s disease, the relevance of this cellular model in the context of Parkinson’s disease (PD) and other neurodegenerative diseases has not yet been systematically evaluated.\r\n\r\n\r\nWe have used a systems genomics approach to characterize the SH-SY5Y cell line using whole-genome sequencing to determine the genetic content of the cell line and used transcriptomics and proteomics data to determine molecular correlations. Further, we integrated genomic variants using a network analysis approach to evaluate the suitability of the SH-SY5Y cell line for perturbation experiments in the context of neurodegenerative diseases, including PD.\r\n\r\n\r\nThe systems genomics approach showed consistency across different biological levels (DNA, RNA and protein concentrations). Most of the genes belonging to the major Parkinson’s disease pathways and modules were intact in the SH-SY5Y genome. Specifically, each analysed gene related to PD has at least one intact copy in SH-SY5Y. The disease-specific network analysis approach ranked the genetic integrity of SH-SY5Y as higher for PD than for Alzheimer’s disease but lower than for Huntington’s disease and Amyotrophic Lateral Sclerosis for loss of function perturbation experiments.',
                       'has_institutional_ethics_approval': True, 'has_national_ethics_approval': False,
                       'institutional_ethics_approval_notes': '<TBR> To be completed.',
                       'national_ethics_approval_notes': None, 'start_date': '2011-10-28', 'end_date': '2014-10-28',
                       'contacts': [{'first_name': 'Patrick', 'last_name': 'MAY', 'email': 'Patrick.May@uni.lu',
                                     'role': 'Researcher', 'affiliations': [
                               'University of Luxembourg - Luxembourg Centre for Systems Biomedicine']},
                                    {'first_name': 'Rudi', 'last_name': 'BALLING', 'email': 'Rudi.Balling@uni.lu',
                                     'role': 'Principal_Investigator', 'affiliations': [
                                        'University of Luxembourg - Luxembourg Centre for Systems Biomedicine']}],
                       'publications': [{'citation': 'Krishna et al., 2014, BMC Genomics', 'doi': None}]},
                      {'source': 'example.com', 'acronym': 'ADNI', 'external_id': '-', 'name': 'ADNI',
                       'description': None, 'has_institutional_ethics_approval': True,
                       'has_national_ethics_approval': False,
                       'institutional_ethics_approval_notes': 'Information to be completed.',
                       'national_ethics_approval_notes': None, 'start_date': '2016-10-29', 'end_date': None,
                       'contacts': [{'first_name': 'Patrick', 'last_name': 'MAY', 'email': 'Patrick.May@uni.lu',
                                     'role': 'Researcher', 'affiliations': [
                               'University of Luxembourg - Luxembourg Centre for Systems Biomedicine']},
                                    {'first_name': 'Reinhard', 'last_name': 'SCHNEIDER',
                                     'email': 'reinhard.schneider@uni.lu', 'role': 'Principal_Investigator',
                                     'affiliations': [
                                         'University of Luxembourg - Luxembourg Centre for Systems Biomedicine']}],
                       'publications': []}, {'source': 'example.com', 'acronym': 'HeartMed', 'external_id': '-',
                                             'name': 'HeartMed: an ICT platform combining pre-clinical and clinical information for patient-specific modelling in cardiovascular medicine to improve diagnosis and help clinical decision-making',
                                             'description': 'Background: Heart failure is the number one reason for death in the EU. It is a progressive disorder with multiple aetiologies (e.g. volume-pressure overload, ischemic heart disease), subforms (HFpEF, HFrEF) and severities. Patients can be asymptomatic and go undetected and undertreated for years increasing the risk of adverse outcome. Mechanistic physiology-based models have matured to clinical application enabling personalized assessment of the underlying pathophysiological processes. While availability of multidimensional bio-medical data on individual patients (imaging, sensors, omics) has increased dramatically in recent years allowing a progressively fine-granular classification of patients by data-driven models, mechanistic models rely on very specific high quality data that is not always available in the clinic (missing data).\r\nMain objective: The main objective is to enable patient-specific modelling for improved diagnosis and clinical decision-making in cardiovascular medicine.\r\nMethods: We propose a novel concept (the HeartMed platform) that combines data-driven and mechanistic modelling in a step-wise approach.\r\n# Deep-phenomapping will be done for selected animal models and human patients using data from imaging, omics, and sensors\r\n# Heart failure subclasses assessing conformities and differences between the pre- and clinical phenotypes will be defined\r\n# Based on the phenomapping classification, we will combine pre-/clinical information to impute missing data and enable the application of physiology-based mechanistic models of myocardial metabolism and circulation for patient-specific modelling\r\n# Patient-specific models will be used for the assessment of patient-individualized cardiac functionality to improve diagnosis and help clinical decision-making\r\n# In a clinical proof-of-concept study of patients with heart failure, we will use HeartMed to compare model-driven patient classification, diagnostics and treatment with current clinical procedures',
                                             'has_institutional_ethics_approval': True,
                                             'has_national_ethics_approval': True,
                                             'institutional_ethics_approval_notes': 'to be confirmed',
                                             'national_ethics_approval_notes': 'to be confirmed',
                                             'start_date': '2018-08-01', 'end_date': '2023-07-31', 'contacts': [
                        {'first_name': 'Irina-Afrodita', 'last_name': 'BALAUR', 'email': 'irina.balaur@uni.lu',
                         'role': 'Researcher',
                         'affiliations': ['University of Luxembourg - Luxembourg Centre for Systems Biomedicine']},
                        {'first_name': 'Muhammad', 'last_name': 'SHOAIB', 'email': 'muhammad.shoaib@uni.lu',
                         'role': 'Researcher',
                         'affiliations': ['University of Luxembourg - Luxembourg Centre for Systems Biomedicine']},
                        {'first_name': 'Reinhard', 'last_name': 'SCHNEIDER', 'email': 'reinhard.schneider@uni.lu',
                         'role': 'Principal_Investigator',
                         'affiliations': ['University of Luxembourg - Luxembourg Centre for Systems Biomedicine']},
                        {'first_name': 'Venkata Pardhasaradhi', 'last_name': 'SATAGOPAM',
                         'email': 'venkata.satagopam@uni.lu', 'role': 'Researcher',
                         'affiliations': ['University of Luxembourg - Luxembourg Centre for Systems Biomedicine']}],
                                             'publications': []},
                      {'source': 'example.com', 'acronym': 'PRECISESADS', 'external_id': 'TESTID',
                       'name': 'PRECISESADS Sustainability at ELIXIR LU', 'description': None,
                       'has_institutional_ethics_approval': False, 'has_national_ethics_approval': True,
                       'institutional_ethics_approval_notes': None,
                       'national_ethics_approval_notes': 'Each data providing study has its own Ethics approval',
                       'start_date': '2020-02-04', 'end_date': None, 'contacts': [
                          {'first_name': 'Reinhard', 'last_name': 'SCHNEIDER', 'email': 'reinhard.schneider@uni.lu',
                           'role': 'Principal_Investigator',
                           'affiliations': ['University of Luxembourg - Luxembourg Centre for Systems Biomedicine']},
                          {'first_name': 'Wei', 'last_name': 'GU', 'email': 'wei.gu@uni.lu', 'role': 'Researcher',
                           'affiliations': ['University of Luxembourg - Luxembourg Centre for Systems Biomedicine']}],
                       'publications': []}]}
        mock_get.return_value = Mock(ok=True)
        mock_get.return_value.json.return_value = response_content
        daisy_connector = DaisyConnector(app.config.get("DAISY_API_URLS").get('project'), Project)
        projects = list(daisy_connector.build_all_entities())
        self.assertEqual(8, len(projects))
        first_project = projects[0]
        for project in projects:
            project.save()
        self.solr_orm.commit()
        retrieved_project = Project.query.get(first_project.id)
        self.assertEqual('Adrenal tumours', retrieved_project.title)
