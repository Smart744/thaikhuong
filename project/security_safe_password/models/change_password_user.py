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
from openerp import models, api


class ChangePasswordUser(models.Model):

    _inherit = "change.password.user"

    @api.multi
    def change_password_button(self):
        '''
        Override function change_password_button -> validate_new_password
        This method run on action of res.users Form
        Menu to open: On res.users Form > Action > Change Password
        '''
        res_users = self.env['res.users']
        for line in self:
            res_users.validate_new_password(line.new_passwd)
            line.user_id.write({'password': line.new_passwd})

        # don't keep temporary passwords in the database longer than necessary
        self.write({'new_passwd': False})
