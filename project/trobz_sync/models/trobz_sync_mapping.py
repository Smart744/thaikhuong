# -*- coding: utf-8 -*-

from datetime import datetime
import copy

from openerp import fields, models, api
from openerp.tools.translate import _
from openerp.tools.safe_eval import safe_eval
from openerp.exceptions import ValidationError

from trobz_sync_log import TrobzSyncLog


class TrobzSyncMapping(models.Model):
    _name = 'trobz.sync.mapping'
    _inherit = ['mail.thread']
    _description = 'Synchronization Map'
    _order = 'setting_seq, sequence'

    # Column
    name = fields.Char(string='Name', size=256, required=True)
    sequence = fields.Integer(string='Sequence', default=16)
    setting_seq = fields.Integer(
        string="Setting Sequence", compute='_compute_setting_seq', store=True)
    src_model_id = fields.Many2one(
        'ir.model', string='Source Model', required=True,
        track_visibility='onchange')
    remote_model = fields.Char(
        string='Remote Model', size=64, required=True,
        track_visibility='onchange')
    setting_id = fields.Many2one(
        'trobz.sync.setting', string='Setting', required=True,
        track_visibility='onchange', ondelete='cascade', index=True)
    # TODO: to create a new model for the fields' mapping.
    # It should have at least three info:
    # - src_field (m2o ir.model.field)
    # - remote_field (char)
    # - default_value
    # So 3 fields src_fields, remote_fields and defaults can be replaced.
    # Other fields like reference_fields and ignore_fields may also be removed.
    src_fields = fields.Text(
        string='Source Fields', required=True, track_visibility='onchange',
        help='List of fields to be synchronized.')
    remote_fields = fields.Text(
        string='Remote Fields', track_visibility='onchange',
        help='List of fields to be synchronized on the remote system. '
        'By default, it is the same as the source fields. Note that, '
        'the order of fields is important!')
    last_sync_date = fields.Datetime(
        string='Last Synchronization Date', index=True)
    reference_fields = fields.Text(
        string='Reference Fields', compute='_get_ref_fields')
    ignore_fields = fields.Text(
        string='Ignore Fields', compute='_get_ref_fields')
    defaults = fields.Text(
        string='Default Values', track_visibility='onchange',
        help='Dictionary of source fields and their default values')
    filter_domain = fields.Text(
        string='Conditions', track_visibility='onchange', copy=False,
        help='List of filters to filter remote data')
    use_specific_sync = fields.Boolean(
        'Specific Synchronization', track_visibility='onchange',
        help='Use specific synchronization method for this mapping')
    sync_function = fields.Char(
        string='Sync Function', size=64, track_visibility='onchange',
        help='Specific method to be used for synchronization. This method '
        'should be defined in an osv_memory model that has name in '
        'this pattern sync.source.model')
    unique_fields = fields.Text(
        string='Unique Fields', track_visibility='onchange',
        help='List of fields that mark a record as unique. '
        'Fields that listed here should also appear in the source '
        'and remote fields. One2Many or Many2Many should not be included '
        'in this list.')
    specific_mapping = fields.Text(
        string='Specific Mapping', track_visibility='onchange',
        help='Indicate a specific mapping for each source relation fields')
    post_script = fields.Text(
        string='Post Synchronization Script', track_visibility='onchange',
        help='A function to be run at the end of mapping synchronization.')
    active = fields.Boolean(string='Active', default=True)
    has_active_field = fields.Boolean(
        string='Has Active Field', compute='_compute_has_active_field',
        help='Indicate that both source model and '
        'remote model have the active field.', store=True)
    success_records = fields.Integer(string='Success Records', readonly=True)
    fail_records = fields.Integer(string='Fail Records', readonly=True)
    total_records = fields.Integer(string='Total Records', readonly=True)

    _sql_constraints = [
        ('uniq_src_model_id_remote_model_filter_domain',
         'unique(src_model_id, remote_model, filter_domain)',
         _('This map is already existed!')),
    ]

    @api.depends('src_model_id', 'src_fields', 'remote_fields')
    def _get_ref_fields(self):
        """
        Select reference fields in the list of src_fields.
        Reference fields are fields that have type of: Many2One, One2Many,
            Many2Many, or Reference
        reference fields: calendar.attendee, crm.lead, crm.claim,
            subscription.subscription, ir.actions.server,
            ir.property, res.request
        """
        for mapping in self:
            ref_fields = {}
            ignore_fields = []
            src_fields = safe_eval(mapping.src_fields)
            remote_fields = safe_eval(mapping.remote_fields)
            fields_dict = self.env[mapping.src_model_id.model].fields_get(
                allfields=src_fields)
            for field, field_def in fields_dict.iteritems():
                # Values of Functional and Related fields are ignored.
                # TODO: This is not correct if we insert or update data using
                # SQL queries.
                # TODO: function in field_def seems wrong.
                if 'function' in field_def\
                        or field_def['type'] in ['one2many']:
                    ignore_fields.append(field)
                elif field_def['type'] in [
                    'many2one', 'many2many', 'reference'] or\
                        'relation' in field_def:
                    # index will fire an exception when field cannot be found
                    # in src_fields
                    src_idx = src_fields.index(field)
                    try:
                        ref_fields.update({
                            remote_fields[src_idx]: field
                        })
                    except:
                        raise ValidationError(
                            _('The number of remote fields must be equal to '
                              'the number of source fields.'))
            mapping.reference_fields = str(ref_fields)
            mapping.ignore_fields = str(ignore_fields)
        return

    @api.depends('src_model_id')
    def _compute_has_active_field(self):
        """
        Check if the given model has active field.
        """
        for mapping in self:
            if not mapping.src_model_id:
                # This case happens during the onchange process.
                continue
            src_obj = self.env[mapping.src_model_id.model]
            fields_dict = src_obj.fields_get(allfields=['active'])
            if fields_dict:
                mapping.has_active_field = True
            else:
                mapping.has_active_field = False
        return

    @api.depends('setting_id.sequence')
    def _compute_setting_seq(self):
        for mapping in self:
            if not mapping.setting_id:
                # This case happens during the onchange process.
                continue
            mapping.setting_seq = mapping.setting_id.sequence
        return

    @api.model
    def _get_mapping_name(self, src_model, remote_model, src_model_id=None):
        """
        Return the suggesting name of a mapping. Suggesting name has
        this pattern "source model - remote model".
        """
        if not src_model and src_model_id:
            src_model = self.env['ir.model'].browse(src_model_id).name
        return src_model + ' - ' + remote_model

    @api.onchange('src_model_id', 'remote_model')
    def _onchange_src_model_id_remote_model(self):
        """
        Name of a synchronization map is "source model - remote model".
        """
        for mapping in self:
            if not mapping.src_model_id or not mapping.remote_model:
                # This case happens during the onchange process.
                continue
            mapping.name = self._get_mapping_name(
                mapping.src_model_id.name, mapping.remote_model)
        return

    @api.model
    def create(self, vals):
        """
        If a name is not given, auto compute a name.
        """
        if 'name' not in vals:
            vals.update({
                'name': self._get_mapping_name(None, vals['remote_model'],
                                               vals['src_model_id'])
            })
        return super(TrobzSyncMapping, self).create(vals)

    @api.multi
    def button_synchronize(self):
        """
        Handle the event of clicking on the button Synchronize.
        If no password is defined on the setting, display a wizard to
        ask for password before running the synchronization.
        """
        self.ensure_one()
        if self.setting_id.password:
            # Having password in the sync setting
            # TODO: to test deferred tasks later.
            # return self.deferred_synchronize()
            return self.sudo().synchronize()
        # TODO: to check if this wizard still works
        # No password in the sync setting
        # Show the wizard to input password
        mod_obj = self.env['ir.model.data']
        form_id = mod_obj.get_object_reference(
            'trobz_sync', 'sync_password_prompt_wizard_form')
        form_res = form_id and form_id[1] or False
        context = dict(self._context)
        # use this context when calling this function
        # in the password prompt wizard
        context.update(sync_from_mapping=True)
        return {
            'name': _("Password Prompt"),
            'view_mode': 'form',
            'view_id': form_res,
            'view_type': 'form',
            'res_model': 'sync.password.prompt.wizard',
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new',
        }

    @api.multi
    def deferred_synchronize(self):
        """
        Run the synchronization with deferred task.
        # TODO: to test this function later because it requires deferred_task
        to work.
        """
        deferred_obj = self.env['deferred_processing.task']
        deferred_vals = {
            'name': 'Sync setting IDs %s' % str(self.ids),
            'filename': '/',
            'send_email': False
        }
        process = deferred_obj.create(deferred_vals)
        process_id = process.id
        self._cr.commit()
        deferred_obj.sudo().new_process(process_id)
        deferred_arg = (self.ids)
        deferred_obj.sudo().start_process_object(
            process_id, 'trobz.sync.mapping',
            'synchronize', self.ids, deferred_arg
        )
        return deferred_obj.show_process(process_id)

    @api.multi
    def synchronize(self):
        """
        Synchronize all records related to this mapping.
        """
        handler_ids = {}
        settings = {}
        remote_uid = False
        log_obj = self.env['trobz.sync.log']
        for mapping in self.sorted():
            if self._context.get('is_sync_all'):
                mapping.last_sync_date = False
            if mapping.setting_id.id not in handler_ids:
                setting = mapping.setting_id
                settings.update({
                    setting.id: setting
                })
                remote_uid = setting.get_login_uid()
                if not remote_uid:
                    raise Warning(_('Cannot login with the given credentials'))
                handler_ids.update({
                    setting.id: setting.get_proxy()
                })
                handler = handler_ids[setting.id]
            else:
                setting = settings[mapping.setting_id.id]
                handler = handler_ids[mapping.setting_id.id]
            # Analyze statistics of records succeeded and failed
            # Sync deleted records
            mapping.sync_deleted_record(handler, remote_uid)
            # Main synchronization method
            # TODO: to refactor by using 'search_read` to reduce
            # the number of connections between two servers.
            # Merge two functions get_ids_remote_server and
            # get_values_remote_server.
            # get all ids
            remote_ids = mapping.get_ids_remote_server(
                handler, remote_uid,
                mapping.filter_domain and safe_eval(mapping.filter_domain)
                or [])
            if not remote_ids:
                log_obj.add_log(
                    mapping.setting_id.id, message='Nothing to synchronize',
                    message_type=TrobzSyncLog.WARNING,
                )
                mapping.last_sync_date = datetime.now()
                continue
            # Limit records to synchronize
            limit_record = setting['limit_record'] or len(remote_ids)
            from_idx = 0
            to_idx = limit_record
            while from_idx < len(remote_ids):
                remote_data = mapping.get_values_remote_server(
                    sock_query=handler, remote_uid=remote_uid,
                    object_ids=remote_ids[from_idx:to_idx])
                if not mapping.use_specific_sync:  # Standard synchronization
                    mapping.simple_import(remote_data)
                else:  # Specific synchronization method for this mapping
                    # TODO: to test this option later because TFA does NOT have
                    # a need to use this option.
                    sync_src_obj = self.env['sync.' + mapping.src_model_id.
                                            model]
                    method = getattr(sync_src_obj, mapping.sync_function)
                    method(self._cr, self._uid, remote_data,
                           context=self._context)
                # Continue
                from_idx = to_idx
                to_idx += limit_record

            # Post Script
            mapping._run_post_script(handler, remote_uid)
            # Statistics
            record_obj = self.env['trobz.sync.record']
            success_records = record_obj.search_count(
                [('state', '=', 'success'), ('mapping_id', '=', mapping.id)])
            total_records = record_obj.search_count(
                [('mapping_id', '=', mapping.id)])
            mapping.write({
                'last_sync_date': datetime.now(),
                'total_records': total_records,
                'success_records': success_records,
                'fail_records': total_records - success_records
            })
        return True

    @api.multi
    def sync_deleted_record(self, sock_query, remote_uid):
        """
        Records that are deleted on remote server
        should also be deleted on source server.
        """
        self.ensure_one()
        record_obj = self.env['trobz.sync.record']
        log_obj = self.env['trobz.sync.log']
        # Get all remote_ids of this mapping
        record_ids = record_obj.search([('mapping_id', '=', self.id),
                                        ('id_remote', '!=', False)])
        if not record_ids:
            return

        ids_remote = map(lambda r: r.id_remote, record_ids)
        remote_model = self.remote_model
        remote_database = self.setting_id.database
        remote_password = self.setting_id.password or \
            self._context.get('password')
        # Ask remote server for ids that no longer exist
        try:
            search_vals = [('id', 'in', ids_remote)]
            # Take into account the active field
            if self.has_active_field:
                active_vals = [
                    '|', ('active', '=', True), ('active', '=', False)]
                search_vals.extend(active_vals)
            remote_object_ids = sock_query.execute(
                remote_database, remote_uid, remote_password,
                remote_model, 'search', search_vals)
            remote_deleted_ids = set(ids_remote) - set(remote_object_ids)
        except Exception as exc:
            log_obj.add_log(self.setting_id.id, message=exc,
                            message_type=TrobzSyncLog.ERROR)
            return False
        # Delete these ids and mark equivalent records as deleted and inactive
        # records.
        src_obj = self.env[self.src_model_id.model]
        for remote_deleted_id in remote_deleted_ids:
            todelete_sync_record = False
            try:
                todelete_sync_record = record_obj.search(
                    [('mapping_id', '=', self.id),
                     ('id_remote', '=', remote_deleted_id)]
                )
                todelete_record = src_obj.browse(todelete_sync_record.id_src)
                todelete_record.unlink()
                todelete_sync_record.write(
                    {'state': 'success', 'is_deleted': True, 'active': False})
            except Exception as exc:
                self._cr.rollback()
                if todelete_sync_record:
                    todelete_sync_record.mark_fail_record(exc)
                else:
                    log_obj.add_log(self.setting_id.id, message=exc,
                                    message_type=TrobzSyncLog.ERROR)
        return True

    @api.multi
    def get_ids_remote_server(self, sock_query, remote_uid,
                              filter_domain=None):
        """
        Get ids of all records not yet synchronized
        """
        self.ensure_one()
        remote_model = self.remote_model
        setting = self.setting_id
        remote_database = setting.database
        remote_password = setting.password or self._context.get('password')
        log_obj = self.env['trobz.sync.log']
        filter_domain = self.construct_filter_domain(filter_domain)
        try:
            # User can provide extra domain to search for remote objects
            object_ids = sock_query.execute(
                remote_database, remote_uid, remote_password,
                remote_model, 'search', filter_domain
            )
        except Exception as exc:
            log_obj.add_log(setting.id, message=exc,
                            message_type=TrobzSyncLog.ERROR)
            return []
        # Get all objects that failed to be synchronized last times.
        record_obj = self.env['trobz.sync.record']
        failed_records = record_obj.search(
            [('mapping_id', '=', self.id), ('state', 'in', ('fail', 'draft'))])

        # TODO: to test performance of the three methods below
#         object_ids += [object_id for object_id in map(
#             lambda r: r.id_remote not in object_ids and r.id_remote or None,
#             failed_records) if object_id is not None]
        object_ids += map(lambda r: r.id_remote, failed_records)
        object_ids = list(set(object_ids))
#         for fail_record in failed_records:
#             if fail_record.id_remote in object_ids:
#                 continue
#             object_ids.append(fail_record.id_remote)
        return object_ids

    @api.multi
    def construct_filter_domain(self, filter_domain=None):
        """
        Construct the filter domain
        """
        self.ensure_one()
        if not isinstance(filter_domain, (list, tuple)):
            raise ValidationError(_('Invalid search domain'))

        # Check if source model has the active field
        has_active_field = self.has_active_field
        # Check if the active is in filter_domain
        has_active_filter = False
        if has_active_field:
            for fd in filter_domain:
                if isinstance(fd, (tuple, list)) and fd[0] == 'active':
                    has_active_filter = True
                    break
        if self.last_sync_date:
            filter_domain.append(('write_date', '>', self.last_sync_date))
        if has_active_field and not has_active_filter:
            filter_domain += ['|', ('active', '=', True),
                              ('active', '=', False)]
        return filter_domain

    @api.multi
    def get_values_remote_server(self, sock_query, remote_uid, object_ids):
        """
        Read data based on list object_ids.
        """
        self.ensure_one()
        remote_model = self.remote_model
        src_fields = safe_eval(self.src_fields)
        remote_fields = safe_eval(self.remote_fields)
        default_fields_info = self.defaults and safe_eval(self.defaults) or {}
        default_fields = []
        for field_val in default_fields_info.itervalues():
            if 'remote' not in field_val:
                continue
            default_fields.append(field_val['remote'])
        setting = self.setting_id
        remote_database = setting.database
        remote_password = setting.password or self._context.get('password', '')
        log_obj = self.env['trobz.sync.log']
        try:
            # Return the information of remote objects.
            fields_to_read = remote_fields + default_fields
            remote_data = sock_query.execute(
                remote_database, remote_uid, remote_password,
                remote_model, 'read', object_ids, fields_to_read)
            if not remote_data or self.src_fields == self.remote_fields:
                return remote_data

            # Delete other keys in remote_data but not in fields_to_read
            if len(remote_data[0]) != len(fields_to_read):
                diff = set(remote_data[0].keys()) - set(fields_to_read)
                for item in list(diff):
                    if item == 'id':
                        continue
                    for remote in remote_data:
                        del remote[item]

            # Prevent the case when src fields and remote fields contain
            # a pair of fields but in different orders. Example
            # source fields = [name, code]
            # remote fields = [code, name]
            reverse_flag = '@new@'
            reverse_case = False
            # Correct the difference between src fields and remote fields
            for d_idx in range(0, len(remote_data)):
                for f_idx in range(0, len(src_fields)):
                    if src_fields[f_idx] != remote_fields[f_idx]:
                        if src_fields[f_idx] not in remote_data[d_idx]:
                            remote_data[d_idx][src_fields[f_idx]] =\
                                copy.deepcopy(
                                remote_data[d_idx]
                                [remote_fields[f_idx]])
                        else:
                            # Trouble
                            reverse_case = True
                            tmp_index = src_fields[f_idx] + reverse_flag
                            remote_data[d_idx][tmp_index] = copy.deepcopy(
                                remote_data[d_idx]
                                [remote_fields[f_idx]])
                        del remote_data[d_idx][remote_fields[f_idx]]
                if not reverse_case:
                    continue
                # Correct the temp keys which contain reverse_flag
                for key in remote_data[d_idx].iterkeys():
                    if reverse_flag not in key:
                        continue
                    correct_key = key.replace(reverse_flag, '')
                    remote_data[d_idx][correct_key] = copy.deepcopy(
                        remote_data[d_idx][key])
                    del remote_data[d_idx][key]

            return remote_data
        except Exception as exc:
            log_obj.add_log(setting.id, message=exc,
                            message_type=TrobzSyncLog.ERROR)
            return []

    @api.multi
    def simple_import(self, remote_data):
        """
        Import all remote data into this database based on configuration
        of the mapping.
        """
        self.ensure_one()
        model_obj = self.env['ir.model']
        record_obj = self.env['trobz.sync.record']
        log_obj = self.env['trobz.sync.log']
        src_obj = self.env[self.src_model_id.model]

        ref_fields = safe_eval(self.reference_fields or '{}')
        ignore_fields = safe_eval(self.ignore_fields or '[]')
        unique_fields = safe_eval(self.unique_fields or '[]')
        specific_mapping = self._process_specific_mapping()
        # Get fields' definitions of src_fields of src_model
        fields_dict = src_obj.fields_get(allfields=ref_fields.values())
        # For each remote_record in remote_data
        for i in range(0, len(remote_data)):
            # Check if this record is firstly synchronized or not.
            # TODO: to create a function to handle all the check whether
            # a record is new or already existing. So that it can be called
            # from other functions used for specific mappings.
            new_sync_record = False
            remote_record = remote_data[i]
            sync_record = record_obj.search(
                [('mapping_id', '=', self.id),
                 ('id_remote', '=', remote_record['id'])],
                order='id', limit=1)
            if not sync_record:
                new_sync_record = True
                sync_record = record_obj.create(
                    {'mapping_id': self.id,
                     'id_remote': remote_record['id']})
            elif not sync_record.id_src:
                new_sync_record = True

            remote_record_id = remote_record['id']
            del remote_record['id']

            # Delete values in the ignore fields
            for ignore_field in ignore_fields:
                if ignore_field in remote_record:
                    del remote_record[ignore_field]

            # For each field in the reference (relational) fields
            # Replace the remote id with the source id.
            failed_record = False
            # TODO: to replace the for loop below with this function
            # self._process_relation_fields(remote_data)
            for remote_field, src_field in ref_fields.iteritems():
                if src_field not in remote_record:
                    message = 'Cannot find the field %s in' % remote_field +\
                        ' remote model %s.' % self.remote_model
                    log_obj.add_log(self.setting_id.id, message=message,
                                    message_type=TrobzSyncLog.WARNING)
                    continue
                if not remote_record[src_field]:
                    continue
                if src_field not in fields_dict:
                    message = 'Cannot find the field %s' % src_field +\
                        ' in the model %s.' % self.src_model_id.name
                    sync_record.mark_fail_record(message=message)
                    failed_record = True
                    continue
                # Get the relation mapping of this relational field
                relation_mapping = specific_mapping.get(src_field)
                if not relation_mapping:
                    relation_model = model_obj.search(
                        [('model', '=', fields_dict[src_field]['relation'])],
                        limit=1, order='id')
                    if not relation_model:
                        message = 'Cannot find the relation' +\
                            ' model %s of the field %s.' % (
                                fields_dict[src_field]['relation'], src_field)
                        sync_record.mark_fail_record(message=message)
                        failed_record = True
                        continue
                    relation_mapping = self.search(
                        [('src_model_id', '=', relation_model.id)],
                        order='sequence', limit=1)
                    if not relation_mapping:
                        message = 'Cannot find a mapping for this' +\
                            'model %s.' % fields_dict[src_field]['relation']
                        sync_record.mark_fail_record(message=message)
                        failed_record = True
                        continue

                # Process relational field's value
                relation_record = None
                operator = '='
                if fields_dict[src_field]['type'] == 'many2many':
                    operator = 'in'
                relation_record = record_obj.search(
                    [('mapping_id', '=', relation_mapping.id),
                     ('id_remote', operator, remote_record[src_field][0]),
                     ('state', '=', 'success')],
                    order='id', limit=1)
                if not relation_record:
                    message = 'Cannot find a record of mapping' +\
                        ' %s with this remote_id %s.' % (
                            relation_mapping.name, remote_record[src_field][0])
                    sync_record.mark_fail_record(message=message)
                    failed_record = True
                    continue
                if fields_dict[src_field]['type'] == 'many2many':
                    remote_record[src_field] = [
                        (6, 0, [x.id_src for x in relation_record])]
                elif fields_dict[src_field]['type'] == 'many2one':
                    remote_record[src_field] = relation_record.id_src

            if new_sync_record:
                # Check for existing records that have same unique fields
                # even if the mapping is not created yet.
                id_src = self._find_unique_record(remote_record, unique_fields)
                if id_src:
                    new_sync_record = False
                    sync_record.id_src = id_src
            if failed_record:
                # The current remote_record is considered failed. Continue to
                # next remote_record.
                continue

            # Add default values
            remote_record = self._process_default_values(
                remote_record, self.src_model_id)
            # Create or Update data
            try:
                if not new_sync_record:
                    id_src = sync_record.id_src
                    src_record = src_obj.browse(id_src)
                    # There is a case that the source record is deleted while
                    # the remote record is still existed.
                    if not src_record.exists():
                        new_sync_record = True
                        message = 'Cannot find the ID %s of model %s.' % (
                            id_src, self.src_model_id.model)
                        log_obj.add_log(self.setting_id.id, message=message,
                                        message_type=TrobzSyncLog.WARNING)
                    else:
                        src_record.write(remote_record)
                        message = 'Updated the record ID %s of model %s' % (
                            sync_record.id_src, self.src_model_id.model)
                        log_obj.add_log(self.setting_id.id, message=message,
                                        message_type=TrobzSyncLog.INFO)

                if new_sync_record:
                    id_src = src_obj.create(remote_record)
                    # TODO: to create an XML ID for this record with
                    # this pattern __export__.{model}_{remote_id}
                    message = 'Created a new record of ' +\
                        'model %s ' % self.src_model_id['model'] +\
                        'with the ID %s' % id_src
                    # Note: When a mapping is failed to be synchronized,
                    # all its dependencies mappings are also failed
                    # to be synchronized.
                    log_obj.add_log(self.setting_id.id, message=message,
                                    message_type=TrobzSyncLog.INFO)
                sync_record.write({
                    'id_src': id_src, 'state': 'success',
                    'date': fields.datetime.now(), 'note': False
                })

                # TODO: Have options for the commit frequency:
                # > After each record is synchronized
                # > After a number of records are synchronized
                self._cr.commit()
            except Exception as exc:
                self._cr.rollback()
                sync_record = record_obj.search(
                    [('mapping_id', '=', self.id),
                     ('id_remote', '=', remote_record_id)],
                    order='id', limit=1)
                if not sync_record:
                    new_sync_record = True
                    sync_record = record_obj.create({
                        'mapping_id': self.id,
                        'id_remote': remote_record_id,
                        'state': 'fail'})
                sync_record.mark_fail_record(message=exc)
                self._cr.commit()
                continue
        return True

    @api.multi
    def _process_specific_mapping(self):
        """
        Specific Mapping allows users to indicate a specific mapping
        for a relation field. Example

        ```
        <record id="..." model="trobz.sync.mapping">
            <field name="src_model_id" ref="product.model_product_product"/>
            <field name="remote_model">trobz.component</field>
        </record>

        <record id="..." model="trobz.sync.mapping">
            <field name="src_model_id" ref="product.model_product_product"/>
            <field name="remote_model">trobz.article</field>
        </record>

        <record id="..." model="trobz.sync.mapping">
            <field name="src_model_id" ref="product.model_product_product"/>
            <field name="remote_model">product.product</field>
        </record>

        <record id="..." model="trobz.sync.mapping">
            <field name="src_fields">['article_id']</field>
            <field name="remote_fields">['article_id']</field>
            <field name="specific_mapping">
                {'article_id': 'trobz.article'}
            </field>
        </record>
        ```

        In this case, there are several mappings of `product.product` so we
        need to be able to select a specific mapping among them.
        """
        # TODO: to make specific mapping more flexible
        # Example: A mapping has a relation field of model `res.partner`.
        # However, there are two mappings for `res.partner`; one mapping to
        # synchronize companies and the other mapping to synchronize contacts.
        self.ensure_one()
        specific_mapping = safe_eval(self.specific_mapping or '{}')
        if not specific_mapping:
            return specific_mapping
        for relation_field in specific_mapping:
            remote_model = specific_mapping[relation_field]
            relation_mapping = self.search(
                [('remote_model', '=', remote_model)], limit=1, order='id')
            if relation_mapping:
                specific_mapping.update({relation_field: relation_mapping.id})
            else:
                specific_mapping.update({relation_field: False})
        return specific_mapping

    @api.multi
    def _process_relation_fields(self, remote_record, src_field, remote_field):
        """
        """
        self.ensure_one()
        # TODO: Move the part of processing relation fields from the function
        # simple_import to this function.
        return True

    @api.multi
    def _process_default_values(self, remote_record, src_model):
        """
        Process default values.
        """
        self.ensure_one()
        defaults = safe_eval(self.defaults or '{}')
        if not defaults:
            return remote_record
        # TODO: if sync.model does NOT exist, will it cause an error?
        sync_src_obj = self.env.get(['sync.' + src_model['model']], None)
        for default_key, default_val in defaults.iteritems():
            if 'name' in default_val and 'model' in default_val:
                relation_obj = self.env[default_val['model']].search(
                    [('name', '=', default_val['name'])], limit=1, order='id')
                if not relation_obj:
                    continue
                remote_record.update({default_key: relation_obj.id})
            elif 'value' in default_val:
                if isinstance(default_val, (str, unicode))\
                        and hasattr(sync_src_obj, default_val['value']):
                    method = getattr(sync_src_obj, default_val['value'])
                    remote_record.update({
                        default_key: method(self._cr, self._uid, remote_record,
                                            self._context)
                    })
            else:
                remote_record.update({default_key: default_val})
        return remote_record

    @api.multi
    def _run_post_script(self, sock_query, remote_uid):
        """
        Run the post script of a synchronization of a self.
        """
        self.ensure_one()
        if not self.post_script:
            return True
        log_obj = self.env['trobz.sync.log']
        sync_src_obj = self.env.get('sync.' + self.src_model_id.model, None)
        # Log the start of post script
        message = 'Running post_script of %s' % self.name
        log_obj.add_log(self.setting_id.id, message=message,
                        message_type=TrobzSyncLog.INFO)
        # Perform valid post script
        if not isinstance(self.post_script, (str, unicode))\
                or not hasattr(sync_src_obj, self.post_script):
            message = 'Invalid value in post_script'
            log_obj.add_log(self.setting_id.id, message=message,
                            message_type=TrobzSyncLog.ERROR)
            return False
        # Call post script
        method = getattr(sync_src_obj, self.post_script)
        method(self._cr, self._uid, self, sock_query, remote_uid,
               self._context)
        # Log the end of post script
        message = 'End post_script of %s' % self.name
        log_obj.add_log(self.setting_id.id, message=message,
                        message_type=TrobzSyncLog.INFO)
        return True

    @api.multi
    def _find_unique_record(self, remote_record, unique_fields):
        """
        Check for existing records that have same unique fields
        """
        self.ensure_one()
        if not unique_fields:
            return False
        log_obj = self.env['trobz.sync.log']
        domain = []
        for unique_field in unique_fields:
            if unique_field not in remote_record:
                message = '[%s] Cannot find the unique field' % self.name +\
                    ' %s in remote data' % unique_field
                raise ValidationError(message)
            # Relation field
            # This check is NOT correct for o2m or m2m fields but they should
            # NOT be used as unique fields.
            if isinstance(remote_record[unique_field], (list, tuple)):
                domain.append(
                    (unique_field, '=', remote_record[unique_field][0]))
            else:  # Other types
                domain.append((unique_field, '=', remote_record[unique_field]))
        if self.has_active_field:
            domain.extend(['|', ('active', '=', True), ('active', '=', False)])
        src_obj = self.env[self.src_model_id.model]
        existing_ids = src_obj.search(domain, order='id')
        if not existing_ids:
            return False
        if len(existing_ids) > 1:
            message = '[%s] Found more than one records' % \
                str(unique_fields) + 'that have same set of unique fields'
            log_obj.add_log(self.setting_id.id, message=message,
                            message_type=TrobzSyncLog.WARNING)
        return existing_ids[0].id

    @api.multi
    def copy(self, default={}):
        """
        Add a suffix " (copy)" after the name.
        """
        if 'name' not in default:
            default.update({'name': self.name + ' (copy)'})
        return super(TrobzSyncMapping, self).copy(default)
