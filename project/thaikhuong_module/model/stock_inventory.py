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

from odoo import models


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    def button_import(self):
        """
            TO DO: show wizard import
        """
        result = self.env['ir.model.data'].get_object_reference(
            'thaikhuong_module',
            'view_import_inventory')
        view_id = result and result[1] or False
        return {
            'name': 'Import',
            'view_type': 'form',
            'res_model': 'import.inventory',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {
                'active_id': self.id
            }
        }
