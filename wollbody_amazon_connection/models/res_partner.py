# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.osv import expression

import odoo.addons.decimal_precision as dp

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    @api.multi
    def _get_all_messages(self):
        
        mail_pool = self.env['mail.message']
        so_pool = self.env['sale.order']
        inv_pool = self.env['account.invoice']
        issue_pool = self.env['project.issue']
        
        all_ids = []
        for partner in self:
            for x in partner.message_ids:
                all_ids.append(x.id)

            so_ids = so_pool.search([('partner_id','=',partner.id)])
            for so in so_ids:
                for x in so.message_ids:
                    all_ids.append(x.id)

            inv_ids = inv_pool.search([('partner_id','=',partner.id)])
            for inv in inv_ids:
                for x in inv.message_ids:
                    all_ids.append(x.id)
            
            issue_ids = issue_pool.search([('partner_id','=',partner.id)])
            for issue in issue_ids:
                for x in  issue.message_ids:
                    all_ids.append(x.id)
                    
            
            partner.all_message_ids = sorted(all_ids, reverse=True)
            
        
    
    ref_num             = fields.Char('Reference Number')
    customer_created    = fields.Date('Customer Created')
    
    all_message_ids     = fields.One2many('mail.message', compute=_get_all_messages, string='Message', store=False)
    