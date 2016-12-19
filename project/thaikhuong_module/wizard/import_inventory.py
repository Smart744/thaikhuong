# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, _
import base64
import csv
import cStringIO
from odoo.exceptions import Warning


class ImportInventory(models.TransientModel):
    _name = 'import.inventory'
    _description = 'Import inventory'

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char('Delimeter', default=',',
                            help='Default delimeter is ","')

    def action_import(self):
        """
            TO DO:parse file csv
            if product already exited:
                update qty onhand of product
            else:
                create new line and set real qty for product
        """
        ctx = self._context
        inventory_obj = self.env['stock.inventory']
        inventory_line_obj = self.env['stock.inventory.line']
        product_obj = self.env['product.product']
        if 'active_id' in ctx:
            inventory = inventory_obj.browse(ctx['active_id'])
        if not self.data:
            raise exceptions.Warning(_("You need to select a file!"))
        data = base64.b64decode(self.data)
        file_input = cStringIO.StringIO(data)
        file_input.seek(0)
        reader_info = []
        if self.delimeter:
            delimeter = str(self.delimeter)
        else:
            delimeter = ','
        reader = csv.reader(file_input, delimiter=delimeter,
                            lineterminator='\r\n')
        try:
            reader_info.extend(reader)
        except Exception:
            raise exceptions.Warning(_("Not a valid file!"))
        keys = reader_info[0]
        # check if keys exist
        if not isinstance(keys, list) or ('code' not in keys or
                                          'quantity' not in keys):
            raise exceptions.Warning(
                _("Not 'code' or 'quantity' keys found"))
        del reader_info[0]
        values = {}
        actual_date = fields.Date.today()
        inv_name = self.name + ' - ' + actual_date
        inventory.write({'name': inv_name,
                         'date': fields.Datetime.now(),
                         'imported': True, 'state': 'confirm'})
        for i in range(len(reader_info)):
            val = {}
            field = reader_info[i]
            values = dict(zip(keys, field))

            val['code'] = values['code']
            val['quantity'] = values['quantity']
            product_id = product_obj.search([
                ('barcode', '=', val['code'])])
            if not product_id:
                raise Warning(
                              _("Can't find product with code " +
                                val['code'] + 'at line ' + str(i)))
                continue
            inventory_line = inventory_line_obj.search([
                ('product_id', '=', product_id[0].id),
                ('inventory_id', '=', inventory.id)])
            if not inventory_line:
                vals = {'product_id': product_id[0].id,
                        'inventory_id': inventory.id,
                        'product_qty': val['quantity'],
                        'location_id': inventory.location_id.id}
                inventory_line_obj.create(vals)
            else:
                inventory_line.write({'product_qty': val['quantity']})
