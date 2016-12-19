# -*- coding: utf-8 -*-
##############################################################################
from lxml import etree  # @UnresolvedImport
import logging

from odoo import fields, api, models
from odoo.osv.orm import setup_modifiers

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):

    _inherit = "res.users"

    group_profile_id = fields.Many2one(
        'res.groups', string='Profile Group',
        domain=[('is_profile', '=', True)], help='The profile group of a user \
        which defines all the required groups for a user.')

    @api.model
    def create(self, vals):
        '''
        Groups of a user are defined by "group_profile_id"
        '''
        # override the default context not to allow reset
        # password to be sent after new user is created
        context = self._context.copy()
        context.update({"no_reset_password": True})
        self = self.with_context(context)
        if vals.get('group_profile_id', False):
            vals['groups_id'] = [(6, 0, [vals['group_profile_id']])]
            # Insert Home Action for the user
            res_group_objs = self.env['res.groups'].browse(
                vals['group_profile_id'])
            if res_group_objs and res_group_objs[0].action_id:
                vals['action_id'] = res_group_objs[0].action_id.id

        return super(ResUsers, self).create(vals)

    @api.multi
    def write(self, vals):
        '''
        If "group_profile_id" is updated, update the list of related groups
        '''
        res_groups_env = self.env['res.groups']
        if vals.get('group_profile_id', False):

            vals['groups_id'] = [(6, 0, [vals['group_profile_id']])]
            # Insert Home Action for the user
            res_group_objs = res_groups_env.browse(vals['group_profile_id'])
            if res_group_objs and res_group_objs[0].action_id:
                vals['action_id'] = res_group_objs[0].action_id.id
        return super(ResUsers, self).write(vals)

    @api.model
    def _get_all_users_by_logins(self, logins):
        res = self.search([('login', 'in', logins)]) or []
        return res

    @api.model
    def create_users(self, user_list):
        '''
        Generic function to create users for a project
        user_list = [
            {
                'name': 'name',
                'login': 'login',
                'password': 'password'
            },
            {
                'name': 'name',
                'login': 'login',
                'password': 'password'
            }
        ]
        '''
        _logger.info("Start creating users...")
        group_obj = self.env['res.groups']
        for user in user_list:
            existing_user_objs = self._get_all_users_by_logins(
                [user['login']])

            g_profile_name = user['group_profile_name']
            g_profile_objs = group_obj.search([('name', '=', g_profile_name),
                                               ('is_profile', '=', True)])
            if not g_profile_objs:
                _logger.warning('The group profile %s does not exist'
                                % user['group_profile_name'])
                continue
            if not existing_user_objs:
                self.create({'name': user['name'],
                             'login': user['login'],
                             'password': user['password'],
                             'group_profile_id': g_profile_objs[0].id})
            else:
                existing_user_objs.write(
                    {'group_profile_id': g_profile_objs[0].id})
        _logger.info("Finish creating users...")
        return True

    @api.model
    def has_groups(self, group_ext_ids):
        """

        OLD function: use `user_has_groups` on every model instead

        Checks whether user belongs to given groups.
        :param list group_ext_ids: list of external IDs (XML IDs) of the groups
           Must be provided in fully-qualified form (``module.ext_id``),
           as there is no implicit module to use..
        :return: True if the current user is a member of the groups else False.
        """
        if not group_ext_ids:
            return False
        if not isinstance(group_ext_ids, list):
            group_ext_ids = [group_ext_ids]
        for group_ext_id in group_ext_ids:
            if self.has_group(group_ext_id):
                return True
        return False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        """
        In user_profile, all groups of user will be defined in profile
        So, we need to set readonly for all fields in tab "access_rights"
        to make sure all users of a profile have same groups
        """

        res = super(ResUsers, self).fields_view_get(view_id=view_id,
                                                    view_type=view_type,
                                                    toolbar=toolbar,
                                                    submenu=submenu)


        attr_key = 'readonly'
        attr_value = '1'

        # only superuser can edit group of admin (uid = 1)
        if self.env.user._is_superuser():
            attr_key = 'attrs'
            attr_value = "{'readonly': [('id', '!=', 1)]}"

        doc = etree.fromstring(res['arch'])
        if view_type == 'form':
            for node in doc.xpath("//page[@name='access_rights']//field"):
                node.set(attr_key, attr_value)
                setup_modifiers(node)
        res['arch'] = etree.tostring(doc)

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
