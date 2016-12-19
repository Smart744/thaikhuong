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

from odoo import models, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def _get_product_attribute_variants(self):
        """
            TO DO: Get attribute categories, attributes and value of attribute
            For attributes categories:
                result += attribute + attribute value
            return result
        """
        self.ensure_one()
        str_return = ""
        if not self.attribute_line_ids:
            return str_return
        attribute_category_list = {}
        for variant in self.attribute_line_ids:
            if variant.attribute_id.attribute_category_id and \
                    variant.attribute_id.attribute_category_id.id not in \
                    attribute_category_list:
                attribute_category_list.update(
                    {variant.attribute_id.attribute_category_id.id: [variant]})
            else:
                attribute_category_list[
                    variant.attribute_id.attribute_category_id.id].append(
                        variant)
        for category_id, attributes in attribute_category_list.iteritems():
            category_obj = self.env['product.attribute.category'].browse(
                category_id)
            str_return += '<strong>' + category_obj.name + ': </strong> <br/>'
            for attribute in attributes:
                values = ''
                for value in attribute.value_ids:
                    values += value.name + ', '
                str_return += '- ' + attribute.attribute_id.name + ': ' + \
                    values + ' <br/>'
        return str_return
