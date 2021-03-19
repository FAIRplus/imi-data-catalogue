#  coding=utf-8
#  DataCatalog
#  Copyright (C) 2020  University of Luxembourg
#
#  This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import tempfile
from abc import ABCMeta, abstractmethod

from flask import request
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, BooleanField, SelectField, SelectMultipleField, DateField, \
    FileField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Length, Email, AnyOf, Optional

from .access_handler import AccessHandler, ApplicationState, Application
from .. import app
from ..connector.rems_connector import RemsConnector

logger = app.logger


class RemsAccessHandler(AccessHandler):

    def requires_logged_in_user(self):
        return True

    def supports_listing_accesses(self):
        return True

    def __init__(self, user, api_username=None, api_key=None, host=None, verify_ssl=True, all_ids=None):
        if all_ids is None:
            all_ids = []
        self.all_ids = all_ids
        self.api_username = api_username
        self.rems_connector = RemsConnector(api_username, api_key, host, verify_ssl,
                                            admin_user=app.config["REMS_API_USER"])
        # trying to create user in case it doesn't exist
        if user.is_authenticated:
            result = self.rems_connector.create_user(api_username, user.displayname, user.email)
            logger.error(result)
        super().__init__(user)

    def has_access(self, dataset):
        applications = self.rems_connector.applications(f'resource:{dataset.id}')
        has_submitted = False
        if not applications:
            return False
        for application in applications:
            if application.applicationapplicant.userid != self.api_username:
                continue
            if application.applicationstate[18:] == ApplicationState.approved.value:
                return ApplicationState.approved
            if application.applicationstate[18:] == ApplicationState.submitted.value:
                has_submitted = True
        if has_submitted:
            return ApplicationState.submitted
        return False

    def my_applications(self):
        applications = self.rems_connector.my_applications()
        results = []
        for a in applications:
            if a.applicationstate[18:] != ApplicationState.draft.value and (
                    a.applicationresources[0].resourceext_id in self.all_ids or not self.all_ids):
                application = self.build_application(a)
                results.append(application)
        return results

    def apply(self, dataset, form):
        catalogue_item = self.rems_connector.get_catalogue_item(dataset.id)
        rems_form = self.rems_connector.get_form_for_catalogue_item(catalogue_item.formid)
        field_values = {}
        # create application
        application_id = self.rems_connector.create_application([catalogue_item.id])
        for field in rems_form.formfields:
            rems_field_id = field.fieldid
            wtf_field = FieldBuilder.build_field_builder(field)
            flask_form_value = getattr(form, rems_field_id).data
            field_values[rems_field_id] = wtf_field.transform_value(flask_form_value, self.rems_connector,
                                                                    application_id)
        # save draftFormTemplate
        saved = self.rems_connector.save_application_draft(application_id, rems_form.formid, field_values)
        resource_id = catalogue_item.resource_id
        resource = self.rems_connector.get_resource(resource_id)
        licenses = resource.licenses
        license_ids = []
        for license in licenses:
            license_id = license.id
            license_ids.append(license_id)
        self.rems_connector.accept_license(application_id, license_ids)
        self.rems_connector.submit_application(application_id)

    def get_datasets(self):
        pass

    def create_form(self, dataset, form_data):
        class FormClass(FlaskForm):
            pass

        catalogue_item = self.rems_connector.get_catalogue_item(dataset.id)
        resource_id = catalogue_item.resource_id
        resource = self.rems_connector.get_resource(resource_id)

        form = self.rems_connector.get_form_for_catalogue_item(catalogue_item.formid)
        fields = form.formfields
        for field in fields:
            try:
                wtf_field = FieldBuilder.build_field(field)
            except UnsupportedFieldType:
                logger.error(f"unsupported field type {field.fieldtype}")
                continue
            setattr(FormClass, field.fieldid, wtf_field)
        licenses = resource.licenses
        for license in licenses:
            type = license.licensetype
            license_id = license.id
            title = license.localizations['en']['title']
            url = license.localizations['en']['textcontent']
            label = f"I accept the {title}"
            license_field = BooleanField(label, render_kw={"url": url},
                                         validators=[AnyOf([True], message="You must accept the agreement")])
            field_id = f"license_{license_id}"
            setattr(FormClass, field_id, license_field)
        setattr(FormClass, 'submit', SubmitField("Send"))
        return FormClass(form_data)

    @staticmethod
    def build_application(application):
        resource_id = application.applicationresources[0].resourceext_id
        resource_title = application.applicationresources[0].catalogue_itemtitle['en']
        creation_date = application.applicationcreated
        try:
            state = ApplicationState(application.applicationstate[18:])
        except ValueError as e:
            logger.error(e)
            state = None
        return Application(state, resource_id, resource_title, creation_date)


def get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


class UnsupportedFieldType(Exception):
    pass


class FieldBuilder(metaclass=ABCMeta):
    SUPPORTED_FIELD_TYPE = []

    @staticmethod
    def build_field_builder(rems_field):
        field_builders = get_all_subclasses(FieldBuilder)
        types_named = {field_builder.__name__: field_builder for field_builder in field_builders}
        for field_builder in types_named.values():
            if field_builder.can_handle(rems_field):
                fb = field_builder(rems_field)
                return fb
        raise UnsupportedFieldType(
            'no field builder supporting this format has been found ({})'.format(rems_field.fieldtype))

    @staticmethod
    def build_field(rems_field):
        fb = FieldBuilder.build_field_builder(rems_field)
        return fb.build()

    @staticmethod
    @abstractmethod
    def build(rems_field):
        pass

    @classmethod
    def can_handle(cls, rems_field):
        return rems_field.fieldtype in cls.SUPPORTED_FIELD_TYPE

    def __init__(self, rems_field):
        self.rems_field = rems_field
        self.validators = self.get_validators()
        self.label = self.get_label()
        self.render_kw = self.get_render_keywords()

    def get_label(self):
        return self.rems_field.fieldtitle['en']

    def get_validators(self):
        validators = []
        optional = self.rems_field.fieldoptional
        if optional:
            validators.append(Optional())
        else:
            validators.append(DataRequired())
        max_length = self.rems_field.fieldmax_length
        if max_length:
            validators.append(Length(max=max_length))
        return validators

    def get_render_keywords(self):
        render_kw = {}
        if self.rems_field.fieldplaceholder:
            placeholder = self.rems_field.fieldplaceholder['en']
            if placeholder:
                render_kw['placeholder'] = placeholder
        return render_kw

    def transform_value(self, value, rems_connector=None, application_id=None):
        return value


class StringFieldBuilder(FieldBuilder):
    SUPPORTED_FIELD_TYPE = ['text', 'description']

    def build(self):
        return StringField(self.label, validators=self.validators, render_kw=self.render_kw)


class LabelFieldBuilder(FieldBuilder):
    SUPPORTED_FIELD_TYPE = ['label']

    def get_render_keywords(self):
        return {"label": True}

    def build(self):
        return StringField(self.label, validators=[], render_kw=self.render_kw)


class HeaderFieldBuilder(FieldBuilder):
    SUPPORTED_FIELD_TYPE = ['header']

    def get_render_keywords(self):
        return {"header": True}

    def build(self):
        return StringField(self.label, validators=[], render_kw=self.render_kw)


class TextAreaFieldBuilder(FieldBuilder):
    SUPPORTED_FIELD_TYPE = ['texta']

    def build(self):
        return TextAreaField(self.label, validators=self.validators, render_kw=self.render_kw)


class AttachmentFieldBuilder(FieldBuilder):
    SUPPORTED_FIELD_TYPE = ['attachment']

    def get_validators(self):
        validators = super().get_validators()
        supported_suffixes = ['jpg', 'png', 'pdf']
        supported_suffixes_string = ", ".join(['jpg', 'png', 'pdf'])
        validators.append(FileAllowed(supported_suffixes, f'File extension not in {supported_suffixes_string}'))

    def build(self):
        return FileField(self.label, validators=self.validators, render_kw=self.render_kw)

    def transform_value(self, value, rems_connector=None, application_id=None):
        file = request.files[self.rems_field.fieldid]
        temp_dir = tempfile.mkdtemp()
        tmp_file_path = os.path.join(temp_dir, file.filename)
        file.save(tmp_file_path)
        attachment_id = rems_connector.add_attachment(application_id, tmp_file_path)
        return str(attachment_id)


class DateFieldBuilder(FieldBuilder):
    SUPPORTED_FIELD_TYPE = ['date']

    def get_render_keywords(self):
        kw = super().get_render_keywords()
        kw['placeholder'] = 'YYYY-MM-DD'
        return kw

    def build(self):
        return DateField(self.label, validators=self.validators, render_kw=self.render_kw)


class SelectFieldBuilder(FieldBuilder):
    SUPPORTED_FIELD_TYPE = ['option']

    def build(self):
        choices = []
        for option in self.rems_field.fieldoptions:
            choices.append((option.key, option.label['en']))
        return SelectField(self.label, choices=choices, validators=self.validators, render_kw=self.render_kw)


class MultiSelectFieldBuilder(FieldBuilder):
    SUPPORTED_FIELD_TYPE = ['multiselect']

    def build(self):
        choices = []
        for option in self.rems_field.fieldoptions:
            choices.append((option.key, option.label['en']))
        return SelectMultipleField(self.label, choices=choices, validators=self.validators, render_kw=self.render_kw)

    def transform_value(self, value, rems_connector=None, application_id=None):
        return " ".join(value)


class EmailFieldBuilder(FieldBuilder):
    SUPPORTED_FIELD_TYPE = ['email']

    def get_validators(self):
        validators = super().get_validators()
        validators.append(Email())
        return validators

    def build(self):
        return EmailField(self.label, validators=self.validators, render_kw=self.render_kw)
