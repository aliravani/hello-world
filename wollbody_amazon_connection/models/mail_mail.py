# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import datetime
import logging
import psycopg2
import threading

from email.utils import formataddr

from odoo import _, api, fields, models
from odoo import tools
from odoo.addons.base.ir.ir_mail_server import MailDeliveryException
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    """ Model holding RFC2822 email messages to send. This model also provides
        facilities to queue and send new email messages.  """
    _inherit = 'mail.mail'
    
    @api.model
    def cron_notify_failed_email(self, use_new_cursor=False):
        mails = self.search([('state','=','exception')])
        if mails:
            msg = "<div style=font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; >"
            msg += "Hallo Ansgar,<br/>"
            msg += "Please check failed email <br/>"
            msg += "Setting -> General setting -> Failed email <br/>"
            msg += "Or you can directly open from below link.<br/>"
            msg += "https://odoo.wollbody.com/web?debug#min=1&limit=80&view_type=list&model=mail.mail&action=85&active_id=11"
            msg += "</div>" 
    
            msg_vals = {
                      'subject'    : "Odoo : email failed notification ",
                      'body_html'  : msg,
                      'email_from' : "mail@wollbody.de",
                      'email_to'   : "ansgar.sohn@wollbody.de",
                      'email_cc'   : False,
                      'reply_to'   : False,
                      'state'      : 'outgoing',
                      'model'       : False,
                      'res_id'      : False,
                      'auto_delete' : False,
            }
            self.env['mail.mail'].create(msg_vals)        
        