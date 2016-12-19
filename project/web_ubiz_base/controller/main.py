# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2016 Trobz (<http://helloworld.ubiz.vn>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import jinja2
import logging
import os
import json
import sys

try:
    import xlwt
except ImportError:
    xlwt = None

import openerp
from openerp import http

_logger = logging.getLogger(__name__)

if hasattr(sys, 'frozen'):
    # When running on compiled windows binary,
    # we don't have access to package loader.
    path = os.path.realpath(os.path.join(
        os.path.dirname(__file__), '..', 'view'))
    loader = jinja2.FileSystemLoader(path)
else:
    loader = jinja2.PackageLoader('openerp.addons.web_ubiz_base', "view")

env = jinja2.Environment(loader=loader, autoescape=True)
env.filters["json"] = json.dumps


class DatabaseSelector(openerp.addons.web.controllers.main.Database):

    def _render_template(self, **d):
        """
        TO DO: Change database manager html
            Change Logo select database
            Change Title
        """
        d.setdefault('manage', True)
        d['insecure'] = openerp.tools.config['admin_passwd'] == 'admin'
        d['list_db'] = openerp.tools.config['list_db']
        d['langs'] = openerp.service.db.exp_list_lang()
        # databases list
        d['databases'] = []
        try:
            d['databases'] = http.db_list()
        except openerp.exceptions.AccessDenied:
            monodb = super(DatabaseSelector, self).db_monodb()
            if monodb:
                d['databases'] = [monodb]
        return env.get_template("ubiz_database_manager.html").render(d)
