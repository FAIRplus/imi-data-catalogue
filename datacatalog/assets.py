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
    datacatalog.assets
    -------------------

   Module to configure Flask-Assets

"""
from flask_assets import Bundle

typeahead_js = 'vendor/node_modules/typeahead.js/dist/typeahead.bundle.js'
handlebars_js = 'vendor/node_modules/handlebars/dist/handlebars.js'
jqueryui_css = 'vendor/node_modules/jquery-ui-dist/jquery-ui.css'
jqueryui_js = 'vendor/node_modules/jquery-ui-dist/jquery-ui.js'

common_css = Bundle(
    'vendor/node_modules/bootstrap/dist/css/bootstrap.css',
    'vendor/node_modules/bootstrap-material-design/dist/css/ripples.css',
    jqueryui_css,
    Bundle(
        'css/layout.less',
        filters='less'
    ),
    "css/typeahead.css",
    filters='cssmin', output='public/css/common.min.css', debug=False)

common_js = Bundle(
    'vendor/node_modules/jquery/dist/jquery.js',
    'vendor/node_modules/bootstrap/dist/js/bootstrap.js',
    'vendor/node_modules/bootstrap-material-design/dist/js/ripples.js',
    'vendor/node_modules/bootstrap-material-design/dist/js/material.js',
    jqueryui_js,
    handlebars_js,
    typeahead_js,
    'js/main.js',
    filters='closure_js',
    output='public/js/common.min.js', debug=False)

select2_js = Bundle('vendor/select2/js/select2.full.js',
                    'vendor/select2/js/select2.sortable.js',
                    output='public/js/select2.js')

select2_css = Bundle('vendor/select2/css/select2.css',
                     'vendor/select2/css/select2-bootstrap.css',
                     output='public/js/select2.css')
