# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import time
import xmlrpclib

from openerp import fields, models, api
from openerp.tools.translate import _

from trobz_sync_log import TrobzSyncLog


class TrobzSyncSetting(models.Model):
    _name = 'trobz.sync.setting'
    _inherit = ['mail.thread']
    _description = 'Synchronization Setting'
    _order = 'sequence'

    @api.depends('host', 'port', 'is_https', 'https_user', 'https_password')
    def _get_base_url(self):
        """
        Get base URL based on given input.
        """
        # TODO: Hide https_password on tree view.
        for sync_setting in self:
            protocol = 'http://'
            if sync_setting.is_https:
                protocol = 'https://'
            if sync_setting.https_user and sync_setting.https_password:
                sync_setting.base_url = '%s%s:%s@%s:%s' % (
                    protocol, sync_setting.https_user,
                    sync_setting.https_password,
                    sync_setting.host, sync_setting.port)
            else:
                sync_setting.base_url = '%s%s:%s' % (
                    protocol, sync_setting.host, sync_setting.port)

    sequence = fields.Integer(string='Sequence', default=16)
    name = fields.Char(string='Name', size=256, required=True)
    host = fields.Char(string='Host', size=256, required=True,
                       track_visibility='onchange')
    database = fields.Char(string='Database', size=32, required=True,
                           track_visibility='onchange')
    login = fields.Char(string='Login', size=128, required=True,
                        track_visibility='onchange')
    port = fields.Integer(string='Port', required=True,
                          track_visibility='onchange')
    # TODO: to change to sth more secured
    password = fields.Char(string='Password', size=256,
                           invisible=True, copy=False)
    max_attempts = fields.Integer(string='Max Attempts', default=3)
    sleep_time = fields.Integer(
        string='Sleep Time', default=10,
        help='Sleep time in seconds between each attempt')
    login_handler = fields.Char(
        string='Login Handler', size=64, default='xmlrpc/common',
        help='The handler is used to login at remote server.')
    main_handler = fields.Char(
        string='Main Handler', size=64, default='xmlrpc/object',
        help='The handler is used to do the synchronization')
    active = fields.Boolean(string='Active', default=True)
    is_https = fields.Boolean(string='HTTPS', default=True)
    https_user = fields.Char(string='HTTPS User', size=128,
                             track_visibility='onchange')
    # TODO: to change to sth more secured
    https_password = fields.Char(string='HTTPS Password', size=256,
                                 invisible=True, copy=False)
    base_url = fields.Char(string='Base URL', size=64, compute='_get_base_url',
                           store=True)
    last_check = fields.Selection([('success', 'Success'), ('fail', 'Failed')],
                                  string='Last Check Result',
                                  default='fail', copy=False)
    limit_record = fields.Integer(string='Limit Record', default=1000)
    note = fields.Text(string='Note')
    ir_cron_id = fields.Many2one('ir.cron', string='Scheduled Action',
                                 ondelete='restrict', copy=False)
    # TODO: Add a field to this model to lock it when a scheduler related to
    # it running.

    _sql_constraints = [
        ('uniq_url_db_login', 'unique(host, port, database, login)',
         _('This setting is already existed!')),
    ]

    @api.model
    def create(self, data):
        """
        Create scheduler to do auto synchronization
        """
        sync_setting = super(TrobzSyncSetting, self).create(data)
        ir_cron_obj = self.env['ir.cron']
        if sync_setting:
            vals = {
                'name': 'Synchronize ' + data['name'],
                'interval_number': 1,
                'interval_type': 'days',
                'nextcall': (datetime.now() + timedelta(days=1)).strftime(
                    '%Y-%m-%d 07:01:02'),
                'numbercall': -1,
                'active': False,
                'doall': True,
                'model': 'trobz.sync.setting',
                'function': 'synchronize',
                'args': '([' + str(sync_setting.id) + '])',
            }
            ir_cron_id = ir_cron_obj.create(vals)
            sync_setting.ir_cron_id = ir_cron_id.id
        return sync_setting

    @api.multi
    def unlink(self):
        """
        Remove the related cron jobs of deleted settings.
        """
        cron_set = self.env['ir.cron']
        # Cannot delete the sequences or cron jobs before deleting the setting
        # because we put `ondelete='restrict'` on those fields' definitions.
        for record in self:
            cron_set += record.ir_cron_id
        res = super(TrobzSyncSetting, self).unlink()
        # Unlink related cron jobs
        cron_set.unlink()
        return res

    @api.multi
    def copy(self, default={}):
        """
        Add a suffix " (copy)" after the name.
        Rename the login to "change-me-now"
        """
        if 'name' not in default:
            default.update({'name': self.name + ' (copy)'})
        if 'login' not in default:
            default.update({'login': 'change-me-now'})
        return super(TrobzSyncSetting, self).copy(default)

    @api.multi
    def get_login_uid(self):
        """
        Login in this remote server at this database.
        """
        self.ensure_one()
        log_obj = self.env['trobz.sync.log']
        login_url = '%s/%s' % (self.base_url, self.login_handler)
        for try_time in range(0, self.max_attempts or 1):
            try:
                log_obj.add_log(
                    self.id, message_type=TrobzSyncLog.INFO,
                    message='Prepare to login to %s' % login_url)
                sock_common = xmlrpclib.ServerProxy(login_url, allow_none=1)
                # TODO: to check the case which password is empty
                password = self.password or self._context.get('password', '')
                remote_uid = sock_common.login(
                    self.database, self.login, password)
                log_obj.add_log(
                    self.id, message_type=TrobzSyncLog.INFO,
                    message='Login successfully to %s' % login_url)
                return remote_uid
            except Exception, exc:
                log_obj.add_log(
                    self.id, message=exc, message_type=TrobzSyncLog.ERROR)
                if try_time >= self.max_attempts:
                    continue
                log_obj.add_log(
                    self.id, message_type=TrobzSyncLog.WARNING,
                    message='[%d] Waiting %d seconds...' % (try_time + 1,
                                                            self.sleep_time))
                time.sleep(self.sleep_time)
                continue
        return False

    @api.multi
    def get_proxy(self):
        """
        Get server proxy of given sync setting.
        """
        self.ensure_one()
        log_obj = self.env['trobz.sync.log']
        proxy_url = '%s/%s' % (self.base_url, self.main_handler)
        try:
            log_obj.add_log(
                self.id, message_type=TrobzSyncLog.INFO,
                message='Connecting to %s' % proxy_url)
            sock_query = xmlrpclib.ServerProxy(proxy_url, allow_none=1)
            log_obj.add_log(
                self.id, message_type=TrobzSyncLog.INFO,
                message='Connect successfully to %s' % proxy_url)
            return sock_query
        except Exception, exc:
            log_obj.add_log(self.id, mapping_id=False,
                            message_type=TrobzSyncLog.ERROR, message=exc)
            return False

    @api.multi
    def button_synchronize(self):
        """
        Check password, if not, return a wizard to input password
        """
        self.ensure_one()
        # TODO: Full Synchronization does NOT work
        if self.password:
            # Having password in the sync setting
            # TODO: to test deferred tasks later.
            # return self.deferred_synchronize()
            return self.synchronize()
        # No password in the sync setting, show a wizard to input pass
        form = self.env.ref('trobz_sync.sync_password_prompt_wizard_form')
        return {
            'name': _("Password Prompt"),
            'view_mode': 'form',
            'view_id': form.id,
            'view_type': 'form',
            'res_model': 'sync.password.prompt.wizard',
            'type': 'ir.actions.act_window',
            'context': self._context,
            'target': 'new'
        }

    @api.multi
    def deferred_synchronize(self):
        """
        Run the synchronization with deferred task.
        """
        deferred_obj = self.env['deferred_processing.task']
        deferred_vals = {
            'name': 'Sync setting IDs %s' % str(self.ids),
            'filename': '/',
            'send_email': False
        }
        process_id = deferred_obj.create(deferred_vals).id
        self._cr.commit()
        deferred_obj.new_process(process_id)
        deferred_obj.start_process_object(
            process_id, 'trobz.sync.setting', 'synchronize', self.ids, ())
        return deferred_obj.show_process(process_id)

    @api.multi
    def synchronize(self):
        """
        Synchronize all mappings of this setting.
        """
        mapping_obj = self.env['trobz.sync.mapping']
        mappings = mapping_obj.search(
            [('setting_id', 'in', self.ids)], order='setting_id, sequence')
        return mappings.synchronize()

    @api.multi
    def test_connection(self):
        """
        Test the connection of this sync setting.
        """
        for setting in self:
            remote_uid = setting.get_login_uid()
            if not remote_uid:
                last_check = 'fail'
            else:
                last_check = 'success'
            setting.last_check = last_check
        return True

    @api.onchange('is_https')
    def onchange_is_https(self):
        """
        Reset values of HTTPS User and Password if HTTPS is unchecked.
        """
        if not self.is_https:
            self.https_user = None
            self.https_password = None
        return
