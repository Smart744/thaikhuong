# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2016 Trobz (<http://ubiz.vn>).
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
    'name': 'Project thaikhuong installer',
    'version': '1.0',
    'category': 'Trobz Standard Modules',
    'description': """
This module will install all module dependencies of thaikhuong.
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'trobz_base',
        'web_ubiz_base',
        'sale',
        'purchase',
        'stock',
        'crm',
        'account',
        'l10n_vn',
        'product',
    ],
    'data': [
        # ============================================================
        # SECURITY SETTING - GROUP - PROFILE
        # ============================================================
        # 'security/',
        'security/ir.model.access.csv',
        'security/res_groups_data.xml',
        # ============================================================
        # DATA
        # ============================================================
        # 'data/',
        'data/res_company_data.xml',
        'data/post_object_function_data.xml',
        'data/product_attribute_category_data.xml',
        'data/product_attribute_data.xml',
        'data/report_paper_format.xml',
        # ============================================================
        # VIEWS
        # ============================================================
        # 'view/',
        'view/product_attribute_category_view.xml',
        'view/product_attribute_view.xml',
        'view/sale_order_view.xml',
        'view/product_template_view.xml',
        'view/stock_inventory_view.xml',

        # wizard
        'wizard/import_inventory_view.xml',
        # ============================================================
        # 'report/'
        'report/report_sale_order.xml',
        # ============================================================
        # MENU
        # ============================================================
        # 'menu/',

        # ============================================================
        # FUNCTION USED TO UPDATE DATA LIKE POST OBJECT
        # ============================================================
        # "data/thaikhuong_update_functions_data.xml",
    ],

    'test': [],
    'demo': [],

    'installable': True,
    'active': False,
    'application': True,
}
