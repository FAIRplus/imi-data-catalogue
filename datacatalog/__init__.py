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
import logging
import os
import json
from collections import defaultdict
from datetime import datetime
from logging.config import dictConfig
from typing import Optional, List

import jinja2
import ldap
from datacatalog.solr.solr_orm_fields import SolrField
from flask import Flask, request, redirect, url_for
from flask_assets import Environment
from flask_caching import Cache
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_reverse_proxy_fix.middleware import ReverseProxyPrefixFix
from flask_wtf.csrf import CSRFProtect
from webassets.loaders import PythonLoader as PythonAssetsLoader

from . import assets, settings
from .exceptions import DownloadsHandlerLinksException

logger = logging.getLogger(__name__)

# if not entities are defined in the settings (ENTITIES parameter), the following entities will be used
DEFAULT_ENTITIES = {
    "dataset": "datacatalog.models.dataset.Dataset",
    "study": "datacatalog.models.study.Study",
    "project": "datacatalog.models.project.Project",
}

DEFAULT_USE_RESTRICTIONS_ICONS = {
    "PERMISSION": ("thumb_up", "text-default", "Permissions"),
    "OBLIGATION": ("hardware", "text-default", "Obligations"),
    "CONSTRAINED_PERMISSION": ("info", "text-default", "Constrained permissions"),
    "PROHIBITION": ("block", "text-default", "Prohibitions"),
}

ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)


def get_access_handler(user, entity_name):
    custom_handler_map = app.config.get("CUSTOM_ACCESS_HANDLERS", {})
    if entity_name in custom_handler_map:
        custom_handler_string_class = custom_handler_map[entity_name]
        split = custom_handler_string_class.split(".")
        custom_handler_string_module = ".".join(split[:-1])
        custom_handler_string_class = "".join(split[-1:])
        handler_module = __import__(
            custom_handler_string_module, fromlist=[custom_handler_string_class]
        )
        handler_class = getattr(handler_module, custom_handler_string_class)
        return handler_class.get_instance(current_user)
    access_handler_map = app.config.get("ACCESS_HANDLERS", {"dataset": "Email"})
    access_handler_string = access_handler_map.get(entity_name)
    if access_handler_string and "Rems" in access_handler_string:
        if access_handler_string == "Rems":
            from .acces_handler.rems_handler import RemsAccessHandler

            rems_class = RemsAccessHandler
        elif access_handler_string == "RemsOidc":
            from .acces_handler.rems_oidc_handler import RemsOidcAccessHandler

            rems_class = RemsOidcAccessHandler
        else:
            raise ValueError("Unknown access handler")
        if user.is_authenticated:
            user_rems_id = user.id
        else:
            user_rems_id = "data-catalogue-service"
        all_ids = app.config["entities"][entity_name].query.all_ids()
        return rems_class(
            user,
            api_username=user_rems_id,
            api_key=app.config.get("REMS_API_KEY"),
            host=app.config.get("REMS_URL"),
            form_id=app.config.get("REMS_FORM_ID"),
            workflow_id=app.config.get("REMS_WORKFLOW_ID"),
            verify_ssl=app.config.get("REMS_VERIFY_SSL", True),
            all_ids=all_ids,
        )
    if access_handler_string == "Email":
        from .acces_handler.email_handler import EmailAccessHandler

        return EmailAccessHandler(user)
    return None


def configure_authentication_system() -> None:
    """
    Configure the authentication system
    Loads the authentication method as specified in the AUTHENTICATION_METHOD settings parameter
    """
    authentication_method = app.config.get("AUTHENTICATION_METHOD", "LDAP")
    try:
        if authentication_method == "LDAP":
            from .authentication.ldap_authentication import (
                LDAPUserPasswordAuthentication,
            )

            authentication = LDAPUserPasswordAuthentication(app.config["LDAP_HOST"])
        elif authentication_method == "PYOIDC":
            from .authentication.pyoidc_authentication import PyOIDCAuthentication

            authentication = PyOIDCAuthentication(
                base_url=app.config["BASE_URL"],
                client_id=app.config["PYOIDC_CLIENT_ID"],
                client_secret=app.config["PYOIDC_CLIENT_SECRET"],
                idp_url=app.config["PYOIDC_IDP_URL"],
            )
        else:
            raise ValueError("Unsupported authentication method")
    except Exception as e:
        authentication = None
        logger.error(e)
        app.config["SHOW_LOGIN"] = False
    app.config["authentication"] = authentication


def configure_solr_orm(new_app) -> None:
    """
    Configure the solr ORM.
    import all the SolrEntities classes defined in the ENTITIES parameter (or uses DEFAULT_ENTITIES).
    stores in app.config['entities'] a dict where keys are entities names and values are entities classes.
    stores in app.config['_solr_orm'] the solr orm instance that will be used throughout the application
    to access solr.

    """
    entities_string = new_app.config.get("ENTITIES", DEFAULT_ENTITIES)
    entities = {}
    for entity_name, entity_string in entities_string.items():
        split = entity_string.split(".")
        entity_class_string_module = ".".join(split[:-1])
        entity_class_string_class = "".join(split[-1:])
        logger.debug(
            f"Loading entity class {entity_class_string_module} as {entity_name}"
        )
        entity_module = __import__(
            entity_class_string_module, fromlist=[entity_class_string_class]
        )
        entity_class = getattr(entity_module, entity_class_string_class)
        entities[entity_name] = entity_class

    new_app.config["entities"] = entities
    from .solr.solr_orm import SolrORM

    new_app.config["_solr_orm"] = SolrORM(
        app.config["SOLR_ENDPOINT"], app.config["SOLR_COLLECTION"]
    )


def get_downloads_handler():
    if app.config.get("DOWNLOADS_HANDLER") == "LFT":
        from lftclient import LFTClient
        from .storage_handler.lft_handler import LFTStorageHandler

        lft_config = app.config.get("LFT_CONFIG")
        lft = LFTClient(
            host=lft_config["HOST"],
            port=lft_config["PORT"],
            scheme=lft_config["SCHEME"],
            verify_ssl=lft_config["VERIFY_SSL"],
        )
        logger.info("logging in to LFT")
        try:
            lft.login(lft_config["USERNAME"], lft_config["PASSWORD"])
        except Exception as e:
            raise DownloadsHandlerLinksException(e)
        logger.info("logged in")
        return LFTStorageHandler(
            lft, lft_config["NAMESPACE"], lft_config["LINKS_BASE_URL"]
        )


def create_application() -> Flask:
    """
    Loads the application configuration and creates the Flask app
    From settings.py, load the *Config object where * is taken from the DATACATALOG_ENV variable.
    Will use DevConfig if environment variable is not set.
    @return Flask application
    """
    env = os.environ.get(
        "DATACATALOG_ENV", "dev"
    )  # will default to dev env if no var exported
    config_object = getattr(settings, "%sConfig" % env.capitalize())
    logging_config = getattr(config_object, "LOGGING_CONFIG", None)
    if logging_config:
        dictConfig(logging_config)
    new_app = Flask(
        __name__,
        static_folder=getattr(config_object, "STATIC_FOLDER", "static"),
        static_url_path=getattr(config_object, "STATIC_URL_PATH", None),
    )
    new_app.config.from_object(config_object)
    plugin = new_app.config.get("PLUGIN")
    if plugin:
        plugin_settings = __import__(f"{plugin}.settings", fromlist=["PluginConfig"])
        plugin_settings_class = getattr(plugin_settings, "PluginConfig")
        new_app.config.from_object(plugin_settings_class)
    # make sure main settings have priority over plugin settings
    new_app.config.from_object(config_object)
    new_app.config["ENV"] = env
    url_prefix = new_app.config.get("URL_PREFIX")
    if url_prefix:
        new_app.config["REVERSE_PROXY_PATH"] = url_prefix
        ReverseProxyPrefixFix(new_app)
    static_folder_configured = new_app.config.get("STATIC_FOLDER")

    if static_folder_configured:
        new_app.static_folder = static_folder_configured
    new_app.cache = Cache(new_app, config=new_app.config["CACHE_CONFIG"])
    new_app.cache.clear()
    new_app.jinja_env.add_extension("jinja2.ext.i18n")
    default_template_path = os.path.join(new_app.root_path, new_app.template_folder)
    extra_templates_path = new_app.config.get("TEMPLATES_EXTRA_FOLDER")
    if extra_templates_path:
        templates_paths = [extra_templates_path, default_template_path]
    else:
        templates_paths = [default_template_path]
    my_loader = jinja2.ChoiceLoader(
        [
            jinja2.FileSystemLoader(templates_paths),
        ]
    )
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
login_manager.login_message_category = "error"
configure_authentication_system()

# configure static files loader
assets_env = Environment(app)
assets_loader = PythonAssetsLoader(assets)
for name, bundle in assets_loader.load_bundles().items():
    assets_env.register(name, bundle)


@app.before_request
def always_login():
    login_valid = current_user.is_authenticated
    require_login = app.config.get("REQUIRE_LOGIN_ALL", False)
    if (
        require_login
        and request.endpoint
        and "static" not in request.endpoint
        and not login_valid
        and not getattr(app.view_functions[request.endpoint], "is_public", False)
    ):
        return redirect(url_for("login", next=request.full_path))


def public_route(decorated_function):
    decorated_function.is_public = True
    return decorated_function


@app.template_filter("use_restrictions")
def _jinja2_filter_use_restrictions(form):
    mapping_icons = app.config.get(
        "USE_RESTRICTIONS_ICONS", DEFAULT_USE_RESTRICTIONS_ICONS
    )
    result = defaultdict(list)
    icons = {}
    for field in form:
        if field.render_kw and "use_restriction_rule" in field.render_kw:
            result[field.render_kw["use_restriction_rule"]].append(field)
    for restriction_type in result:
        icons[restriction_type] = mapping_icons.get(restriction_type)
    return result, icons


@app.template_filter("render_keywords")
def _jinja_2_filter_render_keywords(keywords: List["SolrField"]) -> str:
    entries = [
        ", ".join(entry) if isinstance(entry, list) else entry
        for entry in keywords
        if entry
    ]
    return json.dumps(
        [
            {"@type": "DefinedTerm", "@id": "", "name": f"{ keyword }"}
            for keyword in entries
        ]
    )


@app.template_filter("dt")
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
        return date.strftime("%Y-%m-%d,  %H:%M")


@app.template_filter("date")
def _jinja2_filter_date(date: datetime) -> Optional[str]:
    """
    Jinja filter for datetime formatting, converts datetime to string containing only the date, no time information.
    Format example: 2020-04-30
    @param date: datetime instance to format
    @return: string containing the formatted date
    """
    return _jinja2_filter_datetime(date, "%Y-%m-%d")


@app.template_filter("yesno")
def _jinja2_filter_yesno(bool_flag: str) -> str:
    """
    Jinja filter to convert a boolean to yes or no string
    @param bool_flag: boolean to convert to string
    @return: yes or no
    """
    return {"true": "yes", "false": "no"}.get(bool_flag, "no")


@app.template_filter("boolean")
def _jinja2_filter_boolean(value: str) -> bool:
    return value.lower() in ["true", "false"]


@app.template_filter()
def email(email_address: str) -> str:
    """
    Jinja filter to obfuscate email addresses:
    valentin.groues@uni.lu => valentin.groues(AT)uni(DOT)lu
    @param email_address: email address to obfuscate
    @return: obfuscated email address
    """
    email_address = email_address.replace("@", " (AT) ")
    last_dot = email_address.rfind(".")
    last_dot_plus_un = last_dot + 1
    email_address = (
        email_address[:last_dot] + " (DOT) " + email_address[last_dot_plus_un:]
    )
    return email_address


@app.template_filter("pluralize")
def pluralize(number: int, singular: str = "", plural: str = "s") -> str:
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


@app.context_processor
def inject_access_handler():
    """
    Used to decide if we show the my applications link in navbar
    """
    handler = get_access_handler(
        current_user, app.config.get("DEFAULT_ENTITY", "dataset")
    )
    show = handler and handler.supports_listing_accesses()
    return dict(show_my_application=show)


# Import all controllers so that routes can be resolved
from . import controllers  # noqa: E402

# Import to register filter
from .storage_handler import all_handlers  # noqa: E402

__all__ = [controllers, assets, app, all_handlers]

# import extra controllers from plugin if CONTROLLERS_EXTRA is set in settings
controllers_extra_strings = app.config.get("CONTROLLERS_EXTRA", [])
for controllers_extra_string in controllers_extra_strings:
    logger.info(f"Importing extra controllers from  {controllers_extra_string}")
    __import__(controllers_extra_string)

# import excel exporter if EXCEL_EXPORTER is set in settings
excel_exporter_strings = app.config.get("EXCEL_EXPORTER")
if excel_exporter_strings:
    exporter_module = __import__(excel_exporter_strings, fromlist=["ExcelExporter"])
    app.excel_exporter = getattr(exporter_module, "ExcelExporter")

if __name__ == "__main__":
    app.run()
