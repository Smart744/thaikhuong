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
import pytz

from odoo import api, fields, models


@api.model
def _tz_get(self):
    # put POSIX 'Etc/*' entries at the end to avoid confusing users -
    # see bug 1086728
    return [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz
                                      if not tz.startswith('Etc/') else '_')]


class ResPartner(models.Model):

    _inherit = "res.partner"

    @api.model
    def _get_default_timezone(self):
        '''
        Get default timezone for a user
        '''
        configure_parameter_env = self.env['ir.config_parameter']
        return self._context.get('tz') or \
            configure_parameter_env.get_param('Default Timezone',
                                              False)

    tz = fields.Selection(
        _tz_get, string='Timezone',
        default=_get_default_timezone,
        help="The partner's timezone, "
             "used to output proper date and time values "
             "inside printed reports. "
             "It is important to set a value for this field. "
             "You should use the same timezone that is otherwise used to "
             "pick and render date and time values: your computer's timezone."
    )
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
