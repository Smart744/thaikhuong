# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.modules.db import has_unaccent
from odoo import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)


class post_object_trobz_base(models.TransientModel):
    _name = 'post.object.trobz.base'
    _description = 'trobz_base > Post Object'

    @api.model
    def create_profile_functional_admin(self):
        """
        - Create Profile 'Functional Admin'
        - Create a demo manager user
        """
        group_configure_user = 'Administration / User'

        logging.info(
            "====== START: create profile 'FUNCTIONAL ADMIN' =======")
        res_groups_env = self.env['res.groups']
        default_manager_group = res_groups_env.make_default_manager_groups(
            exclude_groups=[],
            forced_groups=[group_configure_user],
            profile_group_name='Functional Admin')
        logging.info(
            "====== END: create profile 'FUNCTIONAL ADMIN' =======")
        logging.info(
            "====== START: create user 'DEMO MANAGER' =======")
        self.env['res.users'].create(
            {'name': 'Demo Manager',
             'login': 'manager',
             'password': '',  # empty password, admin will set it
             'group_profile_id': default_manager_group.id})
        logging.info(
            "====== END: create profile 'DEMO MANAGER' =======")
        return True

    @api.model
    def update_group_for_admin(self):
        """
        Auto add extra groups for admin user
        """
        ResGroups = self.env['res.groups']
        # get all technical groups
        update_groups = ResGroups.search([('category_id.name', 'not in',
                                           ('Technical Settings',
                                            'Extra Rights',
                                            'Other Extra Rights')
                                           )])
        if update_groups:
            superuser = self.env['res.users'].browse(SUPERUSER_ID)
            superuser.write({'groups_id': [(6, 0, update_groups.ids)]})
        return True

    @api.model
    def add_postgresql_unaccent_module(self):
        """
        lazy load unaccent extension
        """
        cr = self._cr
        try:
            if not has_unaccent(cr):
                cr.execute('CREATE EXTENSION "unaccent";')
        except:
            _logger.error(
                'Ooops, postgesql unaccent module can not be loaded, check your\
                 postgresql version and if this module is installed. To \
                 install it on ubuntu, execute: sudo apt-get install \
                 postgresql-contrib-9.1')
            pass
        return True

    @api.model
    def set_default_timezone(self):
        """
        F#1048
        Check all users and set the default time zone
        to ones who do not have a timezone.
        """
        # Get the list of users
        # TODO: when moving to NEW API, add a filter
        # ('tz', '=', '') in the search function. Then we can remove the
        # the code to get list of "set_tz_users"
        res_users_obj = self.env['res.users']
        users = res_users_obj.search([('tz', '=', False)])
        if not users:
            return True
        # Get the default timezone
        conf_param_obj = self.env['ir.config_parameter']
        default_timezone = conf_param_obj.get_param(
            'Default Timezone', False
        )
        if not default_timezone:
            return True

        # Update default timezone
        users.write({'tz': default_timezone})
        return True

    @api.model
    def update_thousand_separator_grouping(self):
        """
        """
        lang_obj = self.env['res.lang']
        non_groupings = lang_obj.search([('grouping', '=', '[]')])
        if non_groupings:
            non_groupings.write({'grouping': '[3, 3, 3, 3, 3, 3]'})
        return True

    @api.model
    def update_language_date_format(self):
        """
        F#2135. Create a project property and function to update the \
        language format
        """
        date_format = self.env['ir.config_parameter'].get_param(
            'language_date_format', False
        )
        if date_format:
            res_lang_obj = self.env['res.lang']
            res_langs = res_lang_obj.search([('active', '=', True)])
            if res_langs:
                res_langs.write({'date_format': date_format})
        return True

    @api.model
    def update_base_user_rule(self):
        """
        override allow to 'demo manager' to create user without any issue
        """
        base_user_rule = self.env.ref("base.res_users_rule")
        base_rule_rule_config = self.env.ref(
            "trobz_base.config_base_user_record_rule"
        )
        if base_user_rule.exists():
            base_user_rule[0].domain_force = base_rule_rule_config.value

    @api.model_cr
    def _register_hook(self):
        """
        Register hook here to run "upgrade module tasks".
        In function "upgrade_all_trobz_module",
        we just write state "to upgrade" for all Trobz modules
        In this hook, they will be upgraded if any.
        """
        _logger.info('===================START trobz base post object')
        self.update_group_for_admin()
        self.add_postgresql_unaccent_module()
        self.set_default_timezone()
        self.update_thousand_separator_grouping()
        self.update_language_date_format()
        self.update_base_user_rule()
        _logger.info('===================END trobz base post object')
