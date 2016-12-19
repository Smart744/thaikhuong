# -*- encoding: utf-8 -*-
##############################################################################
import logging
from odoo import api, models
from odoo import tools

_logger = logging.getLogger(__name__)


class post_object_trobz_report(models.TransientModel):
    _name = 'post.object.trobz.report'

    @api.model_cr
    def _register_hook(self):
        _logger.info("Trobz_report_base post_object: START")
        self.update_value_report_url()
        _logger.info("Trobz_report_base post_object: END")
        return True

    @api.model
    def update_value_report_url(self):
        interface = tools.config.get('xmlrpc_interface', False)
        port = tools.config.get('xmlrpc_port', False)
        ir_config_para = self.env['ir.config_parameter']
        if interface and port:
            values = 'http://%s:%s' % (interface, str(port))
            ir_config_para.set_param('report.url', values)
        else:
            web_local = ir_config_para.get_param(key='web.base.url')
            ir_config_para.set_param('report.url', web_local)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
