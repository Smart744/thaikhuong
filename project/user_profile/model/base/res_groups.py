# -*- coding: utf-8 -*-
##############################################################################
import logging

from odoo.exceptions import Warning, ValidationError
from odoo.osv import expression
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api, models, fields

_logger = logging.getLogger(__name__)


class res_groups(models.Model):

    _inherit = "res.groups"

    action_id = fields.Many2one('ir.actions.actions', 'Default Home Action',
                                help="If specified, this action will be \
        opened at log on for this user, in addition to the standard menu.")
    is_profile = fields.Boolean(string='Is Profile Group',
                                help='Check this if you want this group \
                                 become a Profile Group.')
    test_model_id = fields.Many2one('ir.model', 'Test Model')
    test_user_id = fields.Many2one('res.users', 'Test User')
    test_record_id = fields.Integer('Test Record ID')
    read_access = fields.Boolean('Read Access')
    create_access = fields.Boolean('Create Access')
    write_access = fields.Boolean('Write Access')
    delete_access = fields.Boolean('Delete Access')

    @api.multi
    def check_model(self):
        profile_data = self
        msg = []
        if len(profile_data.users) < 2:
            msg.append(_('Only user Administrator belongs to this group.'
                         ' Cannot test.'))
        elif not profile_data.test_model_id:
            msg.append(_('Please set value for "Test Model"!'))
        elif not profile_data.test_record_id and\
                (profile_data.read_access or profile_data.write_access or
                 profile_data.delete_access):
            msg.append(_('Please set value for "Test Record ID"!'))
        else:
            model_env = self.env[profile_data.test_model_id.model]
            check = True

            # check if the test record id is exist or not.
            if (profile_data.read_access or profile_data.write_access or
                    profile_data.delete_access):
                test_record_objs = model_env.search(
                    [('id', '=', profile_data.test_record_id)])
                if not test_record_objs:
                    msg.append(_('"Test Record ID" does not exist!'))
                    check = False

            if check:
                rule_env = self.env['ir.rule']
                check_uid = profile_data.users[1].id
                check_username = profile_data.users[1].name
                if profile_data.test_user_id:
                    check_uid = profile_data.test_user_id.id
                    check_username = profile_data.test_user_id.name

                access_objs = self.with_context({
                    'get_ids': True,
                    'model_id': profile_data.test_model_id.id
                }).show_related_model_access()
                access_names = access_objs.name_get()
                access_name_arr = [x[1] for x in access_names]
                access_name_str = ', '.join(access_name_arr)
                check_list = []
                # Check Read access
                if profile_data.read_access:
                    check_list.append('read')

                if profile_data.create_access:
                    check_list.append('create')

                if profile_data.write_access:
                    check_list.append('write')

                if profile_data.delete_access:
                    check_list.append('unlink')
                if not check_list:
                    msg.append(_('Please set the access right to check!'))
                else:
                    can_do = []
                    cannot_do_rule = {}
                    cannot_do_access = {}
                    for operation in check_list:
                        check_access = model_env.sudo(
                            check_uid).check_access_rights(
                            operation, raise_exception=False)
                        if check_access:
                            # Check access rule
                            rule_check = self.sudo(
                                check_uid).profile_check_access_rule(
                                [profile_data.test_record_id],
                                operation, model_env)
                            if rule_check:
                                can_do.append(operation)

                            else:
                                rule_ids = self.sudo(check_uid).get_rule_ids(
                                    [profile_data.test_record_id],
                                    profile_data.test_model_id.model,
                                    operation)
                                rule_objs = rule_env.browse(rule_ids)
                                rule_names = rule_objs.name_get()
                                rule_name_arr = [x[1] for x in rule_names]
                                rule_name_str = ', '.join(rule_name_arr)
                                if rule_name_str not in cannot_do_rule:
                                    cannot_do_rule[rule_name_str] = [operation]
                                else:
                                    cannot_do_rule[
                                        rule_name_str].append(operation)
                        else:
                            # Seek for all access right
                            # for this profile on this model
                            if not access_objs:
                                if 'there is no access right defined' not in\
                                        cannot_do_access:
                                    cannot_do_access[
                                        'there is no access right defined'
                                    ] = [operation]
                                else:
                                    cannot_do_access[
                                        'there is no access right defined'
                                    ].append(operation)
                            else:
                                if access_name_str not in cannot_do_access:
                                    cannot_do_access[
                                        access_name_str] = [operation]
                                else:
                                    cannot_do_access[
                                        access_name_str].append(operation)
                    if can_do:
                        msg.append(_(
                            'This test user (id=%s, name=%s) \
                            can %s record %s of the model %s') %
                            (check_uid, check_username, ', '.join(can_do),
                             profile_data.test_record_id,
                             profile_data.test_model_id.name))
                    for rule_str, oper in cannot_do_rule.items():
                        msg.append(_('This test user (id=%s, name=%s) can not \
                         %s record %s of the model %s \
                         because of Record Rules: %s') %
                                    (check_uid, check_username,
                                     ', '.join(oper),
                                     profile_data.test_record_id,
                                     profile_data.test_model_id.name,
                                     rule_str))

                    for access_str, oper in cannot_do_access.items():
                        msg.append(_('This test user (id=%s, name=%s) can not \
                        %s record %s of the model %s \
                        because of Model Access: %s') %
                                    (check_uid, check_username,
                                     ', '.join(oper),
                                     profile_data.test_record_id,
                                     profile_data.test_model_id.name,
                                     access_str))

        if msg:
            msg = ' - ' + '\n - '.join(msg)
            raise Warning(msg)

    @api.multi
    def show_related_model_access(self):
        access_env = self.env['ir.model.access']
        group_ids = self.get_groups()
        args = [('group_id', 'in', group_ids)]
        if self._context.get('model_id'):
            args.append(('model_id', '=', self._context['model_id']))
        access_objs = access_env.search(args)
        if self._context.get('get_ids'):
            return access_objs
        return {
            'domain': [('id', 'in', access_objs.ids)],
            'name': _('Related Model Access'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'ir.model.access',
            'type': 'ir.actions.act_window',
            'context': self._context,
        }

    @api.multi
    def get_groups(self):
        sql = '''
            SELECT gid
            FROM res_groups_users_rel
            WHERE uid IN
            (
                SELECT id
                FROM res_users
                WHERE group_profile_id = %s
                Limit 1
            )'''
        self._cr.execute(sql, (self.ids[0],))
        res = self._cr.fetchall()
        group_ids = [x[0] for x in res]
        if group_ids:
            return group_ids

        # When there is no user for this profile
        profile_data = self[0].read()
        group_ids = profile_data['groups_ids'] + [-1, -1]
        sql = '''
             SELECT hid
             FROM res_groups_implied_rel
             WHERE gid IN %s
        '''
        self._cr.execute(sql, (tuple(group_ids),))
        res = self._cr.fetchall()
        group_ids2 = [x[0] for x in res]
        return group_ids + group_ids2

    @api.multi
    def profile_check_access_rule(self, test_record_ids, operation, model_env):
        """Verifies that the operation given by ``operation`` is allowed
            for the user according to ir.rules.

           :param operation: one of ``write``, ``unlink``
           :raise except_orm: * if current ir.rules do not permit
               this operation.
           :return: rule_name
        """
        ir_rule_env = self.env['ir.rule']
        if self._uid == SUPERUSER_ID:
            return True
        if model_env.is_transient():
            # Only one single implicit access rule for transient models:
            # owner only! This is ok to hardcode because we assert that
            # TransientModels always have log_access enabled so that
            # the create_uid column is always there. And even with _inherits,
            # these fields are always present in the local table too,
            # so no need for JOINs.
            self._cr.execute("""SELECT distinct create_uid
                                  FROM %s
                                  WHERE id IN %%s""" % model_env._table,
                             (tuple(test_record_ids),))
            uids = [x[0] for x in self._cr.fetchall()]
            if len(uids) != 1 or uids[0] != self._uid:
                return False
        else:
            where_clause, where_params, tables = ir_rule_env.sudo(
                self._uid).domain_get(model_env._name, operation)
            if where_clause:
                where_clause = ' and ' + ' and '.join(where_clause)
                self._cr.execute(
                    'SELECT ' + model_env._table + '.id FROM ' +
                    ','.join(tables) + ' WHERE ' + model_env._table +
                    '.id IN %s' + where_clause,
                    ([tuple(test_record_ids)] + where_params))
                returned_ids = [x['id'] for x in self._cr.dictfetchall()]
                check_rs = self.sudo(
                    self._uid).profile_check_record_rules_result_count(
                    test_record_ids, returned_ids, operation, model_env)
                return check_rs

        return True

    @api.multi
    def get_rule_ids(self, test_record_ids, model_name, mode="read"):

        if self._uid == SUPERUSER_ID:
            return []
        res_ids = []
        model_env = self.env[model_name]
        self._cr.execute("""
                SELECT r.id
                FROM ir_rule r
                JOIN ir_model m ON (r.model_id = m.id)
                WHERE m.model = %s
                AND r.active is True
                AND r.perm_""" + mode + """
                AND (r.id IN (SELECT rule_group_id FROM rule_group_rel g_rel
                            JOIN res_groups_users_rel u_rel ON
                                (g_rel.group_id = u_rel.gid)
                            WHERE u_rel.uid = %s) OR r.global)""",
                         (model_name, self._uid))
        rule_ids = [x[0] for x in self._cr.fetchall()]
        if rule_ids:
            # browse user as super-admin root to avoid access errors!
            user_obj = self.env['res.users'].sudo().browse(self._uid)
            rule_data_objs = self.env['ir.rule'].browse(rule_ids)
            for rule in rule_data_objs:
                global_domains = []                 # list of domains
                # map: group -> list of domains
                group_domains = {}
                # read 'domain' as UID to have the correct eval context for the
                # rule.
                rule_domain = rule.domain
                # rule_domain = rule_domain['domain']
                dom = expression.normalize_domain(rule_domain)
                for group in rule.groups:
                    if group in user_obj.groups_id:
                        group_domains.setdefault(group, []).append(dom)
                if not rule.groups:
                    global_domains.append(dom)
                # combine global domains and group domains
                if group_domains:
                    group_domain = expression.OR(map(expression.OR,
                                                     group_domains.values()))
                else:
                    group_domain = []
                domain = expression.AND(global_domains + [group_domain])
                if domain:
                    # _where_calc is called as superuser.
                    # This means that rules can involve objects on
                    # which the real uid has no acces rights.
                    # This means also there is no implicit restriction
                    # (e.g. an object references another object
                    # the user can't see).
                    query = self.env[model_name].sudo()._where_calc(
                        domain, active_test=False)
                    where_clause, where_params, tables = query.where_clause,\
                        query.where_clause_params, query.tables
                    if where_clause:
                        where_clause = ' and ' + ' and '.join(where_clause)
                        self._cr.execute('SELECT ' + model_env._table +
                                         '.id FROM ' + ','.join(tables) +
                                         ' WHERE ' + model_env._table +
                                         '.id IN %s' + where_clause,
                                         ([tuple(test_record_ids)] +
                                          where_params))
                        returned_ids = [x['id']
                                        for x in self._cr.dictfetchall()]
                        check_rs = self.sudo(
                            self._uid).profile_check_record_rules_result_count(
                            test_record_ids, returned_ids, mode, model_env)
                        if not check_rs:
                            res_ids.append(rule.id)
        return res_ids

    # Because check_access_rule function always raise warning when not passing
    # checking, so we need to create another function to return result
    @api.multi
    def profile_check_record_rules_result_count(
            self, test_record_ids, result_ids, operation, model_env):
        """Verify the returned rows after applying record rules matches
           the length of `ids`, and raise an appropriate exception
           if it does not.
        """
        test_record_ids, result_ids = set(test_record_ids), set(result_ids)
        missing_ids = test_record_ids - result_ids
        if missing_ids:
            # Attempt to distinguish record rule restriction
            # vs deleted records,
            # to provide a more specific error message - check if the missinf
            self._cr.execute(
                'SELECT id FROM ' + model_env._table + ' WHERE id IN %s',
                (tuple(missing_ids),)
            )
            # the missing ids are (at least partially) hidden by access rules
            if not self._cr.rowcount and operation in ('read', 'unlink'):
                # No need to warn about deleting an already deleted record.
                # And no error when reading a record that was deleted,
                # to prevent spurious
                # errors for non-transactional search/read sequences coming
                # from clients
                return True
            return False
        return True

    @api.multi
    @api.constrains("implied_ids")
    def check_recursive(self, path=None):
        _logger.info("check recursive inheritance of group !")
        if not path:
            path = []
        for res_group in self:
            branch_path = path[:]
            branch_path.append(res_group)
            implied_objs = res_group.implied_ids

            # if found intersection, raise ValidationError
            if (set(branch_path).intersection(set(implied_objs))):
                raise ValidationError("Cannot have recursive implied groups!")
            # recursive check
            implied_objs.check_recursive(path=branch_path)

    @api.multi
    def write(self, vals):
        if 'implied_ids' in vals:
            new_implied_ids = []
            tmp_implied_ids = vals.get('implied_ids', [])
            for implied_group_id in tmp_implied_ids:
                if isinstance(implied_group_id, int):
                    new_implied_ids = tmp_implied_ids
                    break
                elif len(implied_group_id) == 3:
                    new_implied_ids.extend(implied_group_id[2])
                elif len(implied_group_id) == 2:
                    new_implied_ids.extend([implied_group_id[1]])
            self.update_user_group_link(new_implied_ids)

        return super(res_groups, self).write(vals)

    @api.multi
    def update_user_group_link(self, new_implied_ids):
        """
        Update relation of users and groups when there is
        a change in inheritance of groups
        """

        for group_rec in self:

            # Get all IDs of Old implied_ids
            old_implied_grps = group_rec.implied_ids

            # Remove inherit Group
            if len(new_implied_ids) < len(old_implied_grps):
                users = group_rec.users
                for old_implied_group in old_implied_grps:

                    # Implied group is removed
                    if old_implied_group.id not in new_implied_ids:
                        # Get all users of old implied group
                        old_grp_users1 = old_implied_group.users

                        # copy new instance of old_group_users
                        old_grp_users2 = old_grp_users1[:]
                        # Remove users of implied group is removed
                        for user in old_grp_users1:
                            if user.id != SUPERUSER_ID and user in users:
                                old_grp_users2 = old_grp_users2 - user
                        # get all implied_ids of current old_implied_id
                        child_implied_grps = \
                            old_implied_group.trans_implied_ids
                        # reset users for all the groups which
                        # were removed the group from list of inherit groups
                        implied_objs = child_implied_grps + old_implied_group
                        for implied_obj in implied_objs:
                            implied_obj.users = [
                                (6, False, old_grp_users2.ids)
                            ]
        return True

    @api.model
    def make_default_manager_groups(self, exclude_groups=[], forced_groups=[],
                                    profile_group_name='Demo Manager Profile'):
        """
        Create a profile with all groups except the groups given in
        `exclude_groups` and groups which belong to either categories
        "Administration" and "Technical Settings".
        @param exclude_groups: Groups not to add to this profile.
        @param forced_groups: If you want one of the groups which belong to
        either categories "Administration" and "Technical Settings" to be be
        added to this profile, put it here.
        @param profile_group_name: Name of this new profile. By default, name
        will be "Demo Manager Profile".
        """
        except_groups = [
            'Portal', 'Public', 'Anonymous',
            'Extra Rights / Technical Features']
        except_groups = except_groups + exclude_groups
        # plus except all technical setting groups
        tech_setting_categ = self.env.ref('base.module_category_hidden')
        admin_categ = self.env.ref('base.module_category_administration')

        profile_group_obj = None
        # Search all groups except the groups given in
        # `exclude_groups` and groups which belong to either categories
        # "Administration" and "Technical Settings".
        manager_group_recs = self.search(
            [('full_name', 'not in', except_groups),
             ('is_profile', '=', False),
             ('category_id', 'not in', (tech_setting_categ.id, admin_categ.id))
             ], order='id')
        manager_group_ids = manager_group_recs and manager_group_recs.ids or []
        # Search the groups in forced_groups
        if forced_groups:
            if not isinstance(forced_groups, (list, tuple)):
                forced_groups = [forced_groups]
            forced_group_recs = self.search(
                [('full_name', 'in', forced_groups),
                 ('is_profile', '=', False)], order='id')
            manager_group_ids += forced_group_recs and forced_group_recs.ids\
                or []
        demo_profile_recs = self.search([('name', '=', profile_group_name),
                                         ('is_profile', '=', True)])
        profile_categ = self.env.ref('user_profile.module_category_profile')
        if not demo_profile_recs:
            vals = {
                'name': profile_group_name,
                'implied_ids': [(6, 0, manager_group_ids)],
                'is_profile': True,
                'category_id': profile_categ.id,
            }
            profile_group_obj = self.create(vals)
        else:
            for demo_profile_rec in demo_profile_recs:
                if 'implied_ids' in demo_profile_rec:
                    '''
                        Becareful when you select demo_profile.implied_ids.ids
                        In this case, we select (search) groups by name (above)
                        so that we have all of groups and
                        demo_profile.implied_ids.ids will render all of
                        group_ids which we want.
                    '''
                    implied_ids = sorted(demo_profile_rec.implied_ids.ids)
                    if implied_ids != manager_group_ids:
                        vals = {
                            'implied_ids': [(6, 0, manager_group_ids)],
                            'category_id': profile_categ.id
                        }
                        demo_profile_rec.write(vals)
                        # CHECK IF WE HAVE MORE THAN 1 PROFILE
                        # WITH THE SAME FULL NAME. THIS FUNCTION WILL BE RETURN
                        # THE LAST PROFILE_ID??????????
                        profile_group_obj = demo_profile_rec

        return profile_group_obj

    @api.model
    def create_profiles(self, profile_def):
        """
        Create profiles from the profile definition.
        The profile definition is a dictionary for which
        - key is the profile name
        - value is a list of groups to add to this profile
        An example of `profile_def`

        ```
        {
            'Accountant': ['Accounting & Finance / Adviser',
                           'Other Extra Rights / Contact Creation'],
            'Logistic Operator': ['Inventory / User']
        }
        ```
        """
        profile_category = self.env.ref('user_profile.module_category_profile')
        groups_cache = {}
        for prof_name, prof_groups in profile_def.iteritems():
            if not isinstance(prof_groups, list):
                prof_groups = [prof_groups]
            # Find the list of groups to be added to this profile
            groups_to_add = []
            for group_name in prof_groups:
                # Search from cache first. If not found, search in database
                # and then, cache the result.
                if group_name not in groups_cache:
                    group = self.search([('full_name', '=', group_name)])
                    if not group:
                        raise Warning('Cannot find group %s.' % group_name)
                    groups_cache[group_name] = group.id
                groups_to_add.append(groups_cache[group_name])
            # Check the profile's existence
            profile = self.search([('name', '=', prof_name),
                                   ('is_profile', '=', True)])
            if not profile:
                self.create({
                    'name': prof_name,
                    'implied_ids': [(6, 0, groups_to_add)],
                    'is_profile': True,
                    'category_id': profile_category.id
                })
                logging.info('Successfully created a new profile %s.'
                             % prof_name)
            else:
                profile.write({
                    'implied_ids': [(6, 0, groups_to_add)]
                })
                logging.info('Successfully updated the profile %s.'
                             % prof_name)
        return True
