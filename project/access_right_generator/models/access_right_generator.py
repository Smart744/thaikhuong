# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2016 Trobz (<http://trobz.com>).
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
import logging
from odoo import models, api, _
from odoo.exceptions import Warning
_logger = logging.getLogger(__name__)


class AccessRightGenerator(models.AbstractModel):
    _name = "access.right.generator"
    _description = "Access Right Generator"

    @api.model
    def get_all_group_full_name(self):
        result = {}
        res_groups = self.env['res.groups']
        groups = res_groups.search([])
        for group in groups:
            result[group.full_name] = group.id
        return result

    @api.model
    def create_model_access_rights(self, model_access_rights):
        """
        Create a access right of a group for each models in ir_model_access
        model
        @param model_access_rights: list dictionaries of the access rights of
        groups in models
        @return: a object of ir_model_access
        """
        _logger.info('********** START CREATE MODEL ACCESS RIGHT **********')
        res = False
        context = self._context or {}
        ir_model = self.env['ir.model']
        ir_model_access = self.env['ir.model.access']
        module_name = context.get('module_name', False)
        if not module_name:
            raise Warning(_('Cannot find module name '))
        models_access = ir_model_access.search([('name', 'like', module_name)])
        models_access.unlink()
        dict_groups_name_ids = self.get_all_group_full_name()
        # Model_acess {(A,B,C):{(a,b):[1,1,1,0],(b,c):[0,0,1,1]}}
        for key, val in model_access_rights.iteritems():
            # key_model_access_right = (A,B,C)
            # val_model_access_right = {(a,b):[1,1,1,0],(b,c):[0,0,1,1]}
            if not isinstance(key, (tuple)):
                key = (key,)
            for model_name in key:
                model = ir_model.search([('model', '=', model_name)], limit=1)
                if not model:
                    raise Warning(_('Cannot find model "%s" in systems!!!'
                                    % model_name))
                model_id = model.id
                for groups, permissions in val.iteritems():
                    # groups= (a,b)
                    # permissions = [1,1,1,0]
                    if not isinstance(groups, (tuple)):
                        groups = (groups,)

                    for group in groups:
                        group_id = None
                        name = "%s_%s_ALL_%s" % (module_name, model_name,
                                                 permissions)
                        if group:
                            # group = none => set for all groups
                            # group != none => set for specific group
                            group_id = dict_groups_name_ids.get(group, False)
                            if not group_id:
                                raise Warning(
                                    _('Cannot find group %s in systems!!!'
                                      % group))
                            name = "%s_%s_%s_%s" % (module_name, model_name, group,
                                                    permissions)
                        ir_models_access = \
                            ir_model_access.search(
                                [('model_id', '=', model_id),
                                 ('group_id', '=', group_id)], limit=1)
                        vals = {
                            'model_id': model_id,
                            'name': name,
                            'perm_read': permissions[0],
                            'perm_write': permissions[1],
                            'perm_create': permissions[2],
                            'perm_unlink': permissions[3],
                            'active': True,
                            'group_id': group_id,
                        }
                        if ir_models_access:
                            ir_models_access.write(vals)
                        else:
                            res = ir_model_access.create(vals)
        _logger.info('********** END CREATE MODEL ACCESS RIGHT **********')
        return res
