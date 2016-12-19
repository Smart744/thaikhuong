# -*- coding: utf-8 -*-
##############################################################################

import logging

from odoo import tools, models, api


class MailMail(models.Model):

    _inherit = "mail.mail"

    @api.multi
    def send_get_mail_to(self, partner=None):
        """
        Trobz: Config send mail when is_production_instance is False
        """
        ir_config_para_obj = self.env['ir.config_parameter']
        # Get is_production_instance
        is_production_instance = tools.config.get(
            'is_production_instance', False)

        # Get default_email
        default_email = ir_config_para_obj.get_param(
            'default_email', default='noone@trobz.com')

        email_to = super(MailMail, self).send_get_mail_to(partner=partner)

        if not is_production_instance:
            logging.warning('Changing the email_to from %s to %s',
                            email_to, default_email)
            email_to = [default_email]
        return email_to

    @api.multi
    def send_get_mail_body(self, partner=None):
        """
        Trobz: Config email body when is_production_instance is False
        """
        body = super(MailMail, self).send_get_mail_body(partner=partner)
        # Get is_production_instance
        is_production_instance = tools.config.get(
            'is_production_instance', False)
        if not is_production_instance:
            # Get the original recipients
            original_recipients = super(
                MailMail, self).send_get_mail_to(partner=partner)
            body = "<i>Original recipients: %s</i><br/>" % ','.join(
                original_recipients) + body
        return body

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
