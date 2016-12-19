# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import logging

from openerp import fields, models, api


class TrobzSyncLog(models.Model):
    _name = 'trobz.sync.log'
    _description = 'Synchronization Log'
    _order = 'name'

    WARNING = 'WARNING'
    INFO = 'INFO'
    ERROR = 'ERROR'

    name = fields.Char(string='Name', size=256, compute='_get_sync_log_name',
                       store=True)
    create_date = fields.Datetime(
        string='Start Sync Date', readonly=True, index=True)
    setting_id = fields.Many2one(
        'trobz.sync.setting', string='Setting',
        required=True, ondelete='cascade', index=True)
    log = fields.Text(string='Log', copy=False)
    warning_msg = fields.Integer(
        string='Warning(s)', readonly=True, copy=False)
    error_msg = fields.Integer(
        string='Error(s)', readonly=True, copy=False)
    active = fields.Boolean(string='Active', default=True)

    @api.depends('setting_id', 'create_date')
    def _get_sync_log_name(self):
        """
        Log name is the name of the
        """
        for sync_obj in self:
            if not sync_obj.setting_id:
                continue
            sync_obj.name = sync_obj.create_date + \
                ' (' + sync_obj.setting_id.name + ')'

    @api.model
    def _remove_password(self, setting_id, message):
        """
        Make sure that all the passwords (defined on sync setting)
        are removed from the logging message.
        """
        setting = self.env['trobz.sync.setting'].browse(setting_id)
        if not isinstance(message, (str, unicode)):
            message = unicode(message)
        if setting.password:
            message = message.replace(setting.password, '***')
        if setting.https_password:
            message = message.replace(setting.https_password, '****')
        return message

    @api.model
    def add_log(self, setting_id, message, message_type):
        """
        Add log about the synchronization.
        """
        message = self._remove_password(setting_id, message)
        today = datetime.today().strftime('%Y-%m-%d')
        logs = self.search(
            [('setting_id', '=', setting_id),
             ('create_date', '>=', today),
             ('create_date', '<=', today + ' 23:59:59')],
            limit=1, order='id desc')

        if not logs:
            vals = {'setting_id': setting_id}
            log = self.create(vals)
        else:
            log = logs[0]
        vals = {
            'error_msg': log.error_msg,
            'warning_msg': log.warning_msg,
            'log': log.log
        }
        if message_type == self.ERROR:
            logging.error(message)
            vals['error_msg'] = vals.get('error_msg', 0) + 1
            vals['log'] = (vals.get('log', '') or '') + \
                '<span><span style="color: red;">ERROR:</span> ' + \
                unicode(message) + '</span><br/>'
        elif message_type == self.INFO:
            logging.info(message)
            vals['log'] = (vals.get('log', '') or '') +\
                '<span><span>INFO:</span> ' + unicode(message) +\
                '</span><br/>'
        else:
            logging.warning(message)
            vals['warning_msg'] = vals.get('warning_msg', 0) + 1
            vals['log'] = (vals.get('log', '') or '') + \
                '<span>' +\
                '<span style="color: orange;">WARNING:</span> ' + \
                unicode(message) + '</span><br/>'
        return log.write(vals)

    @api.model
    def _auto_del_log(self):
        ago_7_date = (datetime.now() -
                      timedelta(7)).strftime('%Y-%m-%d 00:00:00')
        sync_logs = self.search([('create_date', '>=', ago_7_date)])
        sync_logs.unlink()
        return True
