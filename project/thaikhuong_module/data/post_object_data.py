# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2016 Trobz (<http://ubiz.vn/>).
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

from openerp import models, api, SUPERUSER_ID
from openerp.tools.translate import _
import logging


class PostObjectDataThaiKhuongModule(models.TransientModel):
    _name = "post.object.data.thaikhuong.module"
    _description = "Thai Khuong Module Post Object"

    @api.model
    def start(self):
        self.update_logo_of_company()
        self.env['trobz.base'].run_post_object_one_time(
            'post.object.data.thaikhuong.module',
            ['update_logo_of_company',
             ])
        return True

    @api.model
    def update_logo_of_company(self):
        logging.info("==== START: Update company logo ====")
        trobz_base_obj = self.env['trobz.base']
        trobz_base_obj.update_company_logo()
        logging.info("==== END: Update company logo ====")

