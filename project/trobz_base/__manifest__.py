# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2016 Trobz (<http://trobz.com>).
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
    'name': 'Trobz Base',
    'version': '1.0',
    'category': 'Trobz Standard Modules',
    'summary': 'General features for all projects',
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': [
        'access_right_generator',
        'mail',
        'user_profile',
        'web',
        'trobz_report_base'
    ],
    'data': [
        # data
        'data/base/ir_config_parameter_data.xml',

        # security
        'security/trobz_base_security.xml',

        # view
        # 'view/base/trobz_maintenance_error_view.xml',
        'view/base/ir_module_view.xml',
        'view/base/res_users_view.xml',
        'view/base/res_groups_view.xml',

        # menu - should always in the end of the list
        'menu/trobz_base_menu.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'qweb': [
        'static/src/template/base.xml'
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'active': False,
    'certificate': '',
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
