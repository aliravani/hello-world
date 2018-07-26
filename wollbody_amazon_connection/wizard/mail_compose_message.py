# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import re

from odoo import _, api, fields, models, SUPERUSER_ID, tools
from odoo.tools.safe_eval import safe_eval


class MailComposer(models.TransientModel):
    """ Generic message composition wizard. You may inherit from this wizard
        at model and view levels to provide specific features.

        The behavior of the wizard depends on the composition_mode field:
        - 'comment': post on a record. The wizard is pre-populated via ``get_record_data``
        - 'mass_mail': wizard in mass mailing mode where the mail details can
            contain template placeholders that will be merged with actual data
            before being sent to each recipient.
    """
    _inherit = 'mail.compose.message'
    
    @api.multi
    def send_mail_action(self):
        # TDE/ ???
        if self._context.get('active_model') == 'account.invoice':
            if self._context.get('active_id'):
                invoice = self.env['account.invoice'].browse(self._context.get('active_id'))
                invoice.write({'sale_reciept_send' : True})
        return self.send_mail()