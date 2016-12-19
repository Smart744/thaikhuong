# -​*- coding: utf-8 -*​-
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
import re
import logging

from openerp import models, api
from openerp.exceptions import ValidationError
from openerp.tools.safe_eval import safe_eval
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)
try:
    import cracklib
except ImportError:
    _logger.debug('Cannot import the library cracklib.')
    import crack as cracklib


class ResUsers(models.Model):

    _inherit = "res.users"

    @api.model
    def change_password(self, old_passwd, new_passwd):
        """

        """
        if new_passwd:
            self.validate_new_password(new_passwd)
        return super(ResUsers, self).change_password(
            old_passwd, new_passwd)

    @api.model
    def validate_new_password(self, new_password):
        """
        Check constraints for password
           + Long enough
           + Contain at least 1 letter in lower case
           + Contain at least 1 letter in upper case
           + Contain at least 1 number
        Check with function from cracklib
        """
        icp = self.env['ir.config_parameter']
        length_pw = icp.get_param('length_password', 'False')
        length_pw = int(length_pw)

        if len(new_password) < length_pw:
            raise ValidationError(
                _("Password must have at least %s characters") %
                (length_pw,))
        if not (re.search(r'[A-Z]', new_password) and
                re.search(r'[a-z]', new_password) and
                re.search(r'\d', new_password)):
            raise ValidationError("Password must have: <br/> \
                - at least one letter in lower case <br/> \
                - at least one letter in upper case <br/> \
                - at least one number")

        use_cracklib = icp.get_param(
            'password_check_cracklib', 'False')
        if safe_eval(use_cracklib):
            try:
                cracklib.VeryFascistCheck(new_password)
            except ValueError, error_msg:
                raise ValidationError(_(error_msg))
        return True
