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
import os
import base64
import logging

from odoo import models, api
from odoo.tools.translate import _
from odoo.tools.safe_eval import safe_eval
from odoo.modules.module import get_module_resource
from odoo.exceptions import Warning


_logger = logging.getLogger(__name__)


class TrobzBase(models.AbstractModel):

    """
        Implement general functions at Trobz
    """
    _name = "trobz.base"
    _description = "Trobz Base"

    @api.model
    def update_config(self, config_setting_model_name, config_datas):
        """
        Update config based on the args dictionary config_datas
        @:param config_setting_model_name:
        @:param config_datas
        Example for sale.config.settings
        - config_setting_model_name: 'sale.config.settings'
        - config_datas = {'sale_pricelist_setting': 'fixed',
                            'group_uom': 1}
        """
        for config_field, config_val in config_datas.iteritems():
            self.env['ir.values'].set_default(
                config_setting_model_name, config_field, config_val)
        return True

    @api.model
    def unlink_object_by_xml_id(self, module, xml_id):
        try:
            _logger.info(
                'unlink_object_by_xml_id, module: %s, xml_id: %s'
                % (module, xml_id))
            full_xml_id = str(module) + "." + str(xml_id)
            model_obj = self.env.ref(full_xml_id)
            # Note: unlink also deletes ir_values and ir.model.data
            model_obj.unlink()
        except (ValueError, TypeError):
            _logger.warning(
                'The xml_id "%s" of module "%s" could not be found. Maybe it \
                has already been deleted or the wrong module/xml_id is used.'
                % (xml_id, module))
        return True

    @api.model
    def delete_default_products(self, products_to_remove):
        """
        Delete default products in Odoo
        Normally, there is no more default products in Odoo version 10
        """
        product_obj = self.env['product.product']
        products = product_obj.search([('name', 'in', products_to_remove)])
        # set product as inactive instead of delete it forever.
        # this will help to ignore error when upgrade "base"
        for product in products:
            product.active = False
            product.product_tmpl_id.active = False
        return True

    @api.model
    def get_ean13(self, base_number):
        """
        Generate ean13 number from base number
        @param base_number: number has 12 digits
        """
        if len(str(base_number)) > 12:
            raise Warning(_('Invalid input base number for EAN13 code!')
                          )
        # weight number
        ODD_WEIGHT = 1
        EVEN_WEIGHT = 3
        # Build a 12 digits base_number_str by adding 0 for missing first
        # characters
        base_number_str = '%s%s' % (
            '0' * (12 - len(str(base_number))), str(base_number))
        # sum_value
        sum_value = 0
        for i in range(0, 12):
            if i % 2 == 0:
                sum_value += int(base_number_str[i]) * ODD_WEIGHT
            else:
                sum_value += int(base_number_str[i]) * EVEN_WEIGHT
        # calculate the last digit
        sum_last_digit = sum_value % 10
        calculated_digit = 0
        if sum_last_digit != 0:
            calculated_digit = 10 - sum_last_digit
        barcode = base_number_str + str(calculated_digit)
        return barcode

    @api.model
    def check_ean13(self, ean13_num):
        """
        Check EAN13 number is correct or not
        @param ean13_num: ean13 number needs to check
        """
        ean13_num = str(ean13_num)
        if not ean13_num or len(ean13_num) != 13 or not ean13_num.isdigit():
            return False

        base_number = ean13_num[:12]
        ean13_number_test = ''
        if base_number:
            ean13_number_test = self.get_ean13(base_number)

        if not ean13_number_test or ean13_number_test != ean13_num:
            return False

        return True

    @api.model
    def get_selection_value(self, selection_list, selected_key):
        """
        This fucntion help to return selected value associated with selected
        key.
        Example:
            - Selection list: [('assigned', 'Assigned'),
                               ('test', 'Test'),
                               ('close', 'Close')]
            - Selected key: 'test'
        After calling the function, the return value is 'Test'
        """

        if not selection_list or not selected_key:
            raise Warning(_('Invalid input parameters!'))

        selected_value = None
        selection_dict = dict(selection_list)
        if selection_dict:
            selected_value = selection_dict.get(selected_key)
            if not selected_value:
                raise Warning(_("Can not find associated value with "
                                "selected key '" + selected_key + "'!"))

        return selected_value

    @api.model
    def get_selection_value_from_field(self, model_name,
                                       selection_field_name, selected_key):
        """
        This function help to return selected value associated with selected
        key of a selection field in a model.
        Example:
            Input:
                - model_name: model.person
                - selection_field_name: gender [('male', 'Male'),
                                                ('female', 'Female')]
                - selected_key: 'male'
            Output: 'Male'
        """

        if not model_name or not selection_field_name or not selected_key:
            raise Warning(_('Invalid input parameters!'))

        # get model
        model_obj = self.env[model_name]
        # get selection field
        selection_field = model_obj.fields_get(
            allfields=[selection_field_name])
        if not selection_field:
            raise Warning(_('Can not find selection field %s \
                                 in model %s'
                            % (selection_field_name, model_name)))
        # get selected value
        selection_list = selection_field[selection_field_name] and\
            selection_field[selection_field_name]['selection'] or False
        selection_dict = selection_list and dict(selection_list) or False
        selected_value = selection_dict and \
            selection_dict.get(selected_key) or False
        if not selected_value:
            raise Warning(_("Can not find associated value \
                                 with selected key %s !"
                            % selected_key))
        return selected_value

    @api.model
    def update_company_logo(self):
        """
        Update company logo path
        """
        _logger.info('Post Object: Updating company logo has been started.')
        company_path = self.env['ir.config_parameter'].get_param(
            'Company logo path', False)
        if not company_path:
            _logger.error(
                'Could not find configure parameter: Company logo path.')
            return True

        # When it's dict string
        if '{' in company_path and '}' in company_path:
            company_path = safe_eval(company_path)

        company_args = []
        company_names = None
        if isinstance(company_path, dict):
            company_names = company_path.keys()
            company_args = [('name', 'in', company_names)]
        company_obj = self.env['res.company']
        companies = company_obj.search(company_args)

        for company in companies:
            if company_names:
                if company.name and company_path.get(company.name):
                    img_path = company_path[company.name]
                else:
                    continue
            else:
                img_path = company_path
            module_path = img_path.split(',')
            if len(module_path) == 2:
                path = get_module_resource(
                    module_path[0].strip(), module_path[1].strip())
                if path and os.path.isfile(path):
                    try:
                        f = open(path)
                        content = base64.encodestring(f.read())
                        company.write({'logo': content})
                    except Exception, e:
                        _logger.error(
                            'Error when updating company logo: "%s".' % (e,))
                else:
                    _logger.info('File does not exist: "%s".' % (path,))
            else:
                _logger.info('Invalid value: "%s".' % (company_path,))

        _logger.info('Post Object: Updating company logo has been done.')
        return True

    @api.model
    def load_language(self):
        """
        Auto load a language on the install of a project's module,
        for example, drm_modules, qrvr_modules...
        language_to_load is parameter that predefined in database by xml file
        """
        logging.info('Start loading default Translation...')
        language_to_load = \
            self.env['ir.config_parameter'].get_param(
                'language_to_load', False)
        if not language_to_load:
            logging.info('No default Translation was defined.')
            return False
        languages = language_to_load.split(',')
        modobj = self.env['ir.module.module']
        mids = modobj.search([('state', '=', 'installed')])
        for language_to_load in languages:
            language_to_load = language_to_load.strip()
            sql = "SELECT id, active FROM res_lang WHERE code = '%s'" \
                  % language_to_load
            self._cr.execute(sql)
            if self._cr.rowcount:
                language = self._cr.fetchone()
                if not language[1]:
                    language_objs = self.env['res.lang'].browse([language[0]])
                    language_objs.write({'active': True})
                logging.info('Default Translation of %s was loaded.'
                             % language_to_load)
            mids.update_translations(language_to_load)
        logging.info('Finish loading default Translation.')
        return True

    @api.model
    def run_post_object_one_time(self, object_name, list_functions=[]):
        """
        Generic function to run post object one time
        Input:
            + Object name: where you define the functions
            + List functions: to run
        Result:
            + Only functions which are not run before will be run
        """
        _logger.info('==START running one time functions for post object: %s'
                     % object_name)
        if isinstance(list_functions, (str, unicode)):  # @UndefinedVariable
            list_functions = [list_functions]
        if not list_functions\
                or not isinstance(list_functions, (list)):
            _logger.warning('Invalid value of parameter list_functions.\
                            Exiting...')
            return False

        ir_conf_para_env = self.env['ir.config_parameter']
        post_object_env = self.env[object_name]
        ran_functions = \
            ir_conf_para_env.get_param(
                'List_post_object_one_time_functions', '[]')
        ran_functions = safe_eval(ran_functions)
        if not isinstance(ran_functions, (list)):
            ran_functions = []
        for function in list_functions:
            if (object_name + ':' + function) in ran_functions:
                continue
            getattr(post_object_env, function)()
            ran_functions.append(object_name + ':' + function)
        if ran_functions:
            ir_conf_para_env.set_param('List_post_object_one_time_functions',
                                       str(ran_functions))
        _logger.info('==END running one time functions for post object: %s'
                     % object_name)
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
