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
    datacatalog
    -------------------

   DataCatalog root package
   Loads configuration and creates the Flask application

"""
import os
from datetime import datetime
from typing import Optional

import jinja2
import ldap
from flask import Flask
from flask_assets import Environment
from flask_caching import Cache
from flask_login import LoginManager
from flask_mail import Mail
from flask_reverse_proxy_fix.middleware import ReverseProxyPrefixFix
from flask_wtf.csrf import CSRFProtect
from webassets.loaders import PythonLoader as PythonAssetsLoader

from . import assets, settings

# if not entities are defined in the settings (ENTITIES parameter), the following entities will be used
DEFAULT_ENTITIES = {'dataset': 'datacatalog.models.dataset.Dataset', 'study': 'datacatalog.models.study.Study',
                    'project': 'datacatalog.models.project.Project'}

ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)


def configure_authentication_system() -> None:
    """
    Configure the authentication system
    Loads the authentication method as specified in the AUTHENTICATION_METHOD settings parameter
    """
    from .authentication.ldap_authentication import LDAPAuthentication
    authentication_method = app.config.get('AUTHENTICATION_METHOD', 'LDAP')
    if authentication_method == 'LDAP':
        authentication = LDAPAuthentication(app.config['LDAP_HOST'])
    else:
        raise ValueError("Unsupported authentication method")
    app.config['authentication'] = authentication


def configure_solr_orm(new_app) -> None:
    """
    Configure the solr ORM.
    import all the SolrEntities classes defined in the ENTITIES parameter (or uses DEFAULT_ENTITIES).
    stores in app.config['entities'] a dict where keys are entities names and values are entities classes.
    stores in app.config['_solr_orm'] the solr orm instance that will be used throughout the application
    to access solr.

    """
    entities_string = new_app.config.get('ENTITIES', DEFAULT_ENTITIES)
    entities = {}
    for entity_name, entity_string in entities_string.items():
        split = entity_string.split('.')
        entity_class_string_module = ".".join(split[:-1])
        entity_class_string_class = "".join(split[-1:])
        new_app.logger.info(f'Loading entity class {entity_class_string_module} as {entity_name}')
        entity_module = __import__(entity_class_string_module, fromlist=[entity_class_string_class])
        entity_class = getattr(entity_module, entity_class_string_class)
        entities[entity_name] = entity_class

    new_app.config['entities'] = entities
    from .solr.solr_orm import SolrORM
    new_app.config['_solr_orm'] = SolrORM(app.config['SOLR_ENDPOINT'], app.config['SOLR_COLLECTION'])


def create_application() -> Flask:
    """
    Loads the application configuration and creates the Flask app
    From settings.py, load the *Config object where * is taken from the DATACATALOG_ENV variable.
    Will use DevConfig if environment variable is not set.
    @return Flask application
    """
    env = os.environ.get('DATACATALOG_ENV', 'dev')  # will default to dev env if no var exported
    config_object = getattr(settings, '%sConfig' % env.capitalize())
    new_app = Flask(__name__,
                    static_folder=getattr(config_object, 'STATIC_FOLDER', 'static'),
                    static_url_path=getattr(config_object, 'STATIC_URL_PATH', None)
                    )
    new_app.config.from_object(config_object)
    new_app.config['ENV'] = env
    url_prefix = new_app.config.get('URL_PREFIX')
    if url_prefix:
        new_app.config['REVERSE_PROXY_PATH'] = url_prefix
        ReverseProxyPrefixFix(new_app)
    static_folder_configured = new_app.config.get('STATIC_FOLDER')

    if static_folder_configured:
        new_app.static_folder = static_folder_configured
    new_app.cache = Cache(new_app, config=new_app.config['CACHE_CONFIG'])
    new_app.cache.clear()
    new_app.jinja_env.add_extension('jinja2.ext.i18n')
    default_template_path = os.path.join(new_app.root_path, new_app.template_folder)
    extra_templates_path = new_app.config.get('TEMPLATES_EXTRA_FOLDER')
    if extra_templates_path:
        templates_paths = [extra_templates_path, default_template_path]
    else:
        templates_paths = [default_template_path]
    my_loader = jinja2.ChoiceLoader([
        jinja2.FileSystemLoader(templates_paths),
    ])
    new_app.jinja_loader = my_loader
    return new_app


# creates the Flask app
app = create_application()
# configure the ORM
configure_solr_orm(app)
# configure CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)
# configure Flask-Mail to be able to send emails
mail = Mail()
mail.init_app(app)
# configure Flask-Login for authentication, user sessions
login_manager = LoginManager()
login_manager.init_app(app)
configure_authentication_system()

# configure static files loader
assets_env = Environment(app)
assets_loader = PythonAssetsLoader(assets)
for name, bundle in assets_loader.load_bundles().items():
    assets_env.register(name, bundle)


@app.template_filter('dt')
def _jinja2_filter_datetime(date: datetime, fmt: Optional[str] = None) -> Optional[str]:
    """
    Jinja filter for datetime formatting, converts datetime to string
    @param date: datetime instance to format
    @param fmt: expected format of the date (see strftime method documentation)
    @return: string containing the formatted date
    """
    if date is None:
        return None
    if fmt:
        return date.strftime(fmt)
    else:
        return date.strftime('%Y-%m-%d,  %H:%M')


@app.template_filter('date')
def _jinja2_filter_date(date: datetime) -> Optional[str]:
    """
    Jinja filter for datetime formatting, converts datetime to string containing only the date, no time information.
    Format example: 2020-04-30
    @param date: datetime instance to format
    @return: string containing the formatted date
    """
    return _jinja2_filter_datetime(date, '%Y-%m-%d')


@app.template_filter('yesno')
def _jinja2_filter_date(bool_flag: bool) -> str:
    """
    Jinja filter to convert a boolean to yes or no string
    @param bool_flag: boolean to convert to string
    @return: yes or no
    """
    return {True: "yes", False: "no"}.get(bool_flag, 'no')


@app.template_filter()
def email(email_address: str) -> str:
    """
    Jinja filter to obfuscate email addresses:
    valentin.groues@uni.lu => valentin.groues(AT)uni(DOT)lu
    @param email_address: email address to obfuscate
    @return: obfuscated email address
    """
    email_address = email_address.replace('@', ' (AT) ')
    last_dot = email_address.rfind('.')
    email_address = email_address[:last_dot] + ' (DOT) ' + email_address[last_dot + 1:]
    return email_address


@app.template_filter('pluralize')
def pluralize(number: int, singular: str = '', plural: str = 's') -> str:
    """
    Jinja filter to help with dynamic pluralization of words.
    Return singular if number = 1, plural otherwise.
    Usage example:
       - publication{{ results_count | pluralize}} -> 'publication' if results_count = 1,
       'publications' is results_count > 1
       - entit{{ results_count | pluralize(singular='y', plural='ies')}} -> 'entity' if results_count = 1,
       'entities' is results_count > 1
    @param number: number to evaluate if singular or plural form should be returned
    @param singular: singular version of the string
    @param plural: plural version of the string
    @return: singular or plural version of string depending on number value
    """
    if number == 1:
        return singular
    else:
        return plural


# Import all controllers so that routes can be resolved
from . import controllers

__all__ = [controllers, assets, app]

# import extra controllers from plugin if CONTROLLERS_EXTRA is set in settings
controllers_extra_strings = app.config.get('CONTROLLERS_EXTRA', [])
for controllers_extra_string in controllers_extra_strings:
    app.logger.info(f'Importing extra controllers from  {controllers_extra_string}')
    __import__(controllers_extra_string)

# import excel exporter if EXCEL_EXPORTER is set in settings
excel_exporter_strings = app.config.get('EXCEL_EXPORTER')
if excel_exporter_strings:
    exporter_module = __import__(excel_exporter_strings, fromlist=['ExcelExporter'])
    app.excel_exporter = getattr(exporter_module, 'ExcelExporter')

if __name__ == '__main__':
    app.run()
