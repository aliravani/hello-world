# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class account_payment(models.Model):
    _inherit = "account.payment"
    
    @api.model
    def default_get(self, fields):
        rec = super(account_payment, self).default_get(fields)
        invoice_defaults = self.resolve_2many_commands('invoice_ids', rec.get('invoice_ids'))
        if invoice_defaults and len(invoice_defaults) == 1:
            invoice = invoice_defaults[0]
            if invoice.get('mother_invoice_id'):
                journal_id = self.env['account.invoice'].browse(invoice['mother_invoice_id'][0]).payment_ids[0].journal_id.id
                rec['journal_id'] = journal_id 
            else:
                journal_id = self.env['account.invoice'].browse(invoice['id']).payment_journal_id.id
                rec['journal_id'] = journal_id
        return rec