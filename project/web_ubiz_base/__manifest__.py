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
{
    'name': "Web Ubiz Base",

    'summary': """
        Module for Ubiz.vn.""",

    'author': "Thuan LT",

    'website': "helloworld.ubiz.vn",
    'category': 'web',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',

    'depends': [
        'base',
        'web',
        'disable_odoo_online',
    ],
    'qweb': [
        'static/src/xml/web_dialog_size.xml',
        'view/base_view.xml',
    ],
    'data': [
        'view/qweb.xml',
        'view/web_template.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': True,
    'active': True,
}
