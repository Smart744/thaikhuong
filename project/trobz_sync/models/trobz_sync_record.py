# -*- coding: utf-8 -*-

from datetime import datetime

from openerp import fields, models, api
from openerp.tools.translate import _

from trobz_sync_log import TrobzSyncLog


class TrobzSyncRecord(models.Model):
    _name = 'trobz.sync.record'
    _inherit = ['mail.thread']
    _description = 'Synchronization Record'
    _order = 'mapping_id,id_src'

    name = fields.Char(string='Name', size=256,
                       compute="_get_sync_record_name", store=True)
    mapping_id = fields.Many2one('trobz.sync.mapping', string='Mapping',
                                 required=True, track_visibility='onchange',
                                 index=True, ondelete='cascade')
    id_src = fields.Integer(string='Source ID', track_visibility='onchange')
    id_remote = fields.Integer(string='Remote ID', required=True,
                               index=True, track_visibility='onchange')
    date = fields.Datetime(string='Last Synchronization Date', readonly=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('success', 'Success'), ('fail', 'Failed')],
        string='Last Synchronization Status', default='draft')
    is_deleted = fields.Boolean(string='Deleted Record', default=False)
    active = fields.Boolean(string='Active', default=True)
    note = fields.Text(string='Note')

    @api.depends('mapping_id', 'id_src')
    def _get_sync_record_name(self):
        """
        Record name is the name of the record (to be synchronized)
        and the mapping name.
        """
        for record in self:
            if not record.mapping_id:
                continue
            record_name = record.mapping_id.name + ' - '
            if not record.id_src:
                record_name += '?'
            else:
                record_name += str(record.id_src)
            record.name = record_name

    _sql_constraints = [
        ('uniq_id_src_mapping_id', 'unique(id_remote, mapping_id)',
         _('This record is already existed!')),
    ]

    @api.multi
    def mark_fail_record(self, message):
        """
        Mark this record as failed to be synchronized.
        """
        self.ensure_one()
        self.env['trobz.sync.log'].add_log(
            self.mapping_id.setting_id.id, message, TrobzSyncLog.ERROR)
        self.write({'state': 'fail', 'date': datetime.now(), 'note': message})
        self._cr.commit()
        return True
