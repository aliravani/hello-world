# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from email.utils import formataddr

from odoo import _, api, fields, models, SUPERUSER_ID, tools
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class Message(models.Model):
    """ Messages model: system notification (replacing res.log notifications),
        comments (OpenChatter discussion) and incoming emails. """
    _inherit = 'mail.message'
    
    @api.model
    def create(self, vals):
        res = super(Message,self).create(vals)
        
        if vals.get('model') == 'sale.order' or vals.get('model') == 'account.invoice':
            if vals.get('message_type') == 'email' and vals.get('subtype_id') == 1:
                users = self.env['res.users'].search([('partner_id','=',vals.get('author_id'))])
                if not users:
                    issue   = self.env['project.issue'].create({'name':vals.get('subject'), 'email_from':vals.get('email_from')})
                    if issue:
                        issue_vals = {
                                    'subject'           : vals.get('subject'),
                                    'date'              : vals.get('date'),
                                    'email_from'        : vals.get('email_from'),
                                    'record_name'       : vals.get('record_name'),
                                    'model'             : 'project.issue',
                                    'res_id'            : issue.id,
                                    'body'              : vals.get('body'),
                            }
                        
                        if vals.get('author_id'):
                            issue_vals['author_id'] = vals.get('author_id')
                             
                        message = self.env['mail.message'].create(issue_vals)
        
        return res 