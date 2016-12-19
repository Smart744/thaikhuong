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

from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    expiration_quotation = fields.Char('Expiration Quotation')
    delivery_lead_time = fields.Text('Delivery Lead Time')
    delivery_address = fields.Char('Delivery Address')
    products_of_quotation = fields.Text('Quotation For Products')
    warranty_description = fields.Text('Warranty Description')
