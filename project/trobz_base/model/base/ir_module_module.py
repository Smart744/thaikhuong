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
import logging

from odoo import api, models
_logger = logging.getLogger(__name__)


class IrModuleModule(models.Model):

    _inherit = "ir.module.module"

    @api.multi
    def button_upgrade(self):
        '''
        Overwrite this function to upgrade all installed modules from Trobz
        when upgrading the module "trobz_base"
        '''
        _logger.info("Trobz_button_upgrade is proccessing.........")
        upgrade_ids = self.ids
        # check whether "trobz_base" is in the list
        check_trobz_base = self.search([('name', '=', 'trobz_base'),
                                        ('id', 'in', upgrade_ids)])
        if check_trobz_base:
            # get all installed module with author "Trobz"
            installed_trobz_modules = self.search([('state', '=', 'installed'),
                                                   ('author', '=', 'Trobz')])
            upgrade_ids.extend(installed_trobz_modules.ids)
            """
            uniquifying the ids to avoid:
                Error: "One of the records you are trying to modify has
                already been deleted (Document type: %s)"
            if exist an duplicate id in ids
            """
            upgrade_ids = list(set(upgrade_ids))
        _logger.info("Trobz_button_upgrade ids of modules "
                     "that need to upgrade: %s" % upgrade_ids)
        _logger.info("Trobz_button_upgrade super  "
                     "native button_upgrade...")
        # call super
        upgrade_modules = self.browse(upgrade_ids)
        super(IrModuleModule, upgrade_modules).button_upgrade()
