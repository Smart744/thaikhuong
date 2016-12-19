# -*- coding: utf-8 -*-

import logging
from odoo.tests.common import TransactionCase
_logger = logging.getLogger(__name__)


class TestUpdateConfig(TransactionCase):

    def test_update_config(self):
        """
        Test the function to update the settings.
        """
        _logger.info('Test trobz_base > update_config. Check General Settings '
                     '> Manage multiple companies.')
        self.env['trobz.base'].update_config(
            'base.config.settings', {'group_light_multi_company': True})
        print self.env.user.sudo().has_group('base.group_multi_company')
        assert self.env.user.sudo().has_group('base.group_multi_company'),\
            'trobz_base > update_config failed'

    def test_delete_default_products(self):
        """
        """
        self.env['trobz.base'].delete_default_products(['Service'])
        inactive_prod = self.env['product.product'].search(
            [('name', '=', 'Service'),
             '|', ('active', '=', True), ('active', '=', False)])
        assert inactive_prod and not inactive_prod.active,\
            'trobz_base > delete_default_products failed'
