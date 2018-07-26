# -*- coding: utf-8 -*-

import json
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp
import logging

class AccountInvoiceTaxR(models.Model):
    _name = "account.invoice.tax.r"
    _description = "Invoice Tax Refund"
    _order = 'sequence'

    invoice_id = fields.Many2one('account.invoice', string='Invoice', ondelete='cascade', index=True)
    name = fields.Char(string='Tax Description', required=True)
    tax_id = fields.Many2one('account.tax', string='Tax')
    account_id = fields.Many2one('account.account', string='Tax Account', required=True, domain=[('deprecated', '=', False)])
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic account')
    amount = fields.Monetary()
    manual = fields.Boolean(default=True)
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of invoice tax.")
    company_id = fields.Many2one('res.company', string='Company', related='account_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id', store=True, readonly=True)    
    

class InvoiceSaleReciept(models.Model):
    _name = 'invoice.sale.reciept'
    _order   = 'sequence'
    
    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign
    
    name                  = fields.Char('Description')
    invoice_id            = fields.Many2one('account.invoice', 'Invoice')
    partner_id            = fields.Many2one('res.partner', string='Partner', related='invoice_id.partner_id',store=True)
    product_id            = fields.Many2one('product.product','Product')
    price_unit            = fields.Float('Unit Price')
    quantity              = fields.Float('Quantity')
    discount              = fields.Float('Discount')
    invoice_line_tax_ids  = fields.Many2many('account.tax','invoice_sale_line_tax', 'sale_reciept_id', 'tax_id',string='Taxes')
    refund_invoice_id     = fields.Many2one('account.invoice', 'Refund Invoice')
    account_id            = fields.Many2one('account.account','Account')
    sequence              = fields.Integer('Sequence')
    price_subtotal        = fields.Monetary(string='Amount',store=True, readonly=True, compute='_compute_price')
    currency_id           = fields.Many2one('res.currency', related='invoice_id.currency_id', store=True)
    
class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    
    
    @api.one
    @api.depends('sale_reciept_ids.price_subtotal', 'r_tax_line_ids.amount')
    def _compute_amount_r(self):
        self.amount_untaxed_r = sum(line.price_subtotal for line in self.sale_reciept_ids)
        self.amount_tax_r = sum(line.amount for line in self.r_tax_line_ids)
        self.amount_total_r = self.amount_untaxed_r + self.amount_tax_r
        #amount_total_company_signed = self.amount_total
        #amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
            #amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        #sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        #self.amount_total_company_signed = amount_total_company_signed * sign
        #self.amount_total_signed = self.amount_total * sign
        #self.amount_untaxed_signed = amount_untaxed_signed * sign
    
    @api.multi
    def _get_child_invoice(self):
        for invoice in self:
            child_ids = self.env['account.invoice'].search([('origin','=',invoice.number),('state','in',('draft','open','paid'))])
            invoice['get_child_invoice_ids'] = [(6,0,child_ids.ids)]
    
    @api.multi
    def _get_refund(self):
        for invoice in self:
            refund_amount = 0
            refund_total = 0
            if invoice.get_child_invoice_ids:
                for refund in invoice.get_child_invoice_ids:
                    refund_total += refund.amount_total
                    if refund.state == 'paid':
                        refund_amount += refund.amount_total
                        
            invoice.get_refund_amount = refund_amount
            invoice.get_refund_total = refund_total
            invoice.get_refund_pending = refund_total - refund_amount
    
    @api.multi
    def _get_mother_invoice(self):
        res ={}
        for invoice in self:
            if invoice.type == 'out_refund':
                invoice_ids = self.env['account.invoice'].search([('number','=',invoice.origin)], limit=1)
                if invoice_ids:
                    invoice['mother_invoice_id'] = invoice_ids.id
                    
                
        return res
    
    @api.multi
    def _get_all_messages(self):
        all_ids = []
        for invoice in self:
            #for x in invoice.message_ids:
            #    all_ids.append(x.id)
                
            if invoice.partner_id:
                for x in invoice.partner_id.all_message_ids:
                    all_ids.append(x.id)
            
                
            invoice.all_message_ids = list(set(all_ids))
            invoice.all_message_ids = sorted(all_ids, reverse=True)
    
    
    @api.multi
    def _date_10(self):
        for invoice in self:
            if invoice.date_invoice:
                date_invoice = datetime.strptime(invoice.date_invoice, "%Y-%m-%d")
                invoice.date_10 = date_invoice + relativedelta(days=10) 
                
            
            
    sale_reciept_ids        = fields.One2many('invoice.sale.reciept','invoice_id',string='Sales Reciept')
    r_tax_line_ids          = fields.One2many('account.invoice.tax.r', 'invoice_id', string='R Tax Lines', readonly=False, states={'draft': [('readonly', False)]}, copy=True)
    get_child_invoice_ids   = fields.Many2many('account.invoice',compute='_get_child_invoice', string='Child Invoices')
    child_invoice_id        = fields.Many2one('account.invoice','Refund Invoice')
    mother_invoice_id       = fields.Many2one('account.invoice', compute='_get_mother_invoice', string='Mother Invoice')
    
    amount_untaxed_r        = fields.Monetary(string='Untaxed Amount',store=True, readonly=True, compute='_compute_amount_r', track_visibility='always')
    amount_tax_r            = fields.Monetary(string='Tax',store=True, readonly=True, compute='_compute_amount_r')
    amount_total_r          = fields.Monetary(string='Total',store=True, readonly=True, compute='_compute_amount_r')
    
    get_refund_amount       = fields.Float(compute='_get_refund',string="Refunded Amount")
    get_refund_pending      = fields.Float(compute='_get_refund',string="Refund Pending Amount")
    get_refund_total        = fields.Float(compute='_get_refund', string="Refund Total")
    
    refund_amount           = fields.Float('Refund Amount')
    all_message_ids         = fields.One2many('mail.message', compute=_get_all_messages, string='Message', store=False)
    sale_reciept_send       = fields.Boolean('Sale Reciept Send')
    
    
    
    #amazon field from sale order
    is_amazon               = fields.Boolean('Is Amazon')
    date_time               = fields.Datetime('Date Time')
    purchase_date           = fields.Datetime('Purchase Date')
    last_update_date        = fields.Datetime('Last Update Date')
    amazon_id               = fields.Char('AmazonOrder Id')
    f_channel               = fields.Char('Full Fillment Channel')
    sales_channel           = fields.Char('Sales Channel')
    ship_serv_level         = fields.Char('Ship Service Level')
    shipment_service        = fields.Char('Ship Service Category')
    order_status            = fields.Char('Order Status')
    unshipped_items         = fields.Integer('No of items Unshipped')
    shipped_items           = fields.Integer('No of items Shipped')
    marketplace_id          = fields.Char('Marketplace ID')
    order_total             = fields.Float('Order Total')
    order_type              = fields.Char('Order Type')
    #amazon_finance_ids      = fields.One2many('amazon.finance','invoice_id','Amazon Finance')
    
    date_10                 = fields.Date(compute='_date_10',string='Date -10')
    
    
    def _prepare_tax_line_vals_r(self, line, tax):
        """ Prepare values to create an account.invoice.tax line

        The line parameter is an account.invoice.line, and the
        tax parameter is the output of account.tax.compute_all().
        """
        vals = {
            'invoice_id': self.id,
            'name': tax['name'],
            'tax_id': tax['id'],
            'amount': tax['amount'],
            'base': tax['base'],
            'manual': False,
            'sequence': tax['sequence'],
            'account_analytic_id': tax['analytic'] and line.account_analytic_id.id or False,
            'account_id': self.type in ('out_invoice', 'in_invoice') and (tax['account_id'] or line.account_id.id) or (tax['refund_account_id'] or line.account_id.id),
        }

        # If the taxes generate moves on the same financial account as the invoice line,
        # propagate the analytic account from the invoice line to the tax line.
        # This is necessary in situations were (part of) the taxes cannot be reclaimed,
        # to ensure the tax move is allocated to the proper analytic account.
        

        return vals
    
    @api.multi
    def get_taxes_values_r(self):
        tax_grouped = {}
        for line in self.sale_reciept_ids:
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals_r(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
        return tax_grouped
    
    
    @api.multi
    def compute_taxes_r(self):
        """Function used in other module to compute the taxes on a fresh invoice created (onchanges did not applied)"""
        account_invoice_tax = self.env['account.invoice.tax.r']
        ctx = dict(self._context)
        for invoice in self:
            # Delete non-manual tax lines
            self._cr.execute("DELETE FROM account_invoice_tax_r WHERE invoice_id=%s AND manual is False", (invoice.id,))
            self.invalidate_cache()

            # Generate one tax line per tax, however many invoice lines it's applied to
            tax_grouped = invoice.get_taxes_values_r()

            # Create new tax lines
            for tax in tax_grouped.values():
                account_invoice_tax.create(tax)

        # dummy write on self to trigger recomputations
        return True
    
    
    @api.multi
    def get_line(self):
        for invoice in self:
            reciept_pool = self.env['invoice.sale.reciept']
            if invoice.type == 'out_invoice':
                unlink_reciept_id = reciept_pool.search([('invoice_id','=',invoice.id)])
                if unlink_reciept_id:
                    unlink_reciept_id.unlink()
                         
                
                for mother in invoice.invoice_line_ids:
                    mother_val = {
                                'product_id'            : mother.product_id.id,
                                'quantity'              : mother.quantity,
                                'price_unit'            : mother.price_unit,
                                'invoice_line_tax_ids'  : [(6, 0, [x.id for x in mother.invoice_line_tax_ids])],
                                'invoice_id'            : invoice.id,
                                'name'                  : mother.name,
                                
                        }
                    reciept_id = reciept_pool.create(mother_val) 
                
                latest_inv_id_list = []
                if invoice.get_child_invoice_ids:
                    for child in invoice.get_child_invoice_ids:
                        latest_inv_id_list.append(child.id)
                        for child_refund in child.invoice_line_ids:
                            reciept = reciept_pool.search([('invoice_id','=',invoice.id),('product_id','=',child_refund.product_id.id)])
                            if reciept:
                                if reciept.product_id.id == child_refund.product_id.id:
                                    qty = reciept.quantity - child_refund.quantity
                                else:
                                    qty = mother.quantity - child_refund.quantity
    
                                child_val = {
                                    'product_id'            : child_refund.product_id.id,
                                    'quantity'              : qty,
                                    'price_unit'            : child_refund.price_unit,
                                    'invoice_line_tax_ids'  : [(6, 0, [x.id for x in child_refund.invoice_line_tax_ids])],
                                    'invoice_id'            : invoice.id,
                                    'name'                  : child_refund.name,
                                    }
                                reciept.write(child_val)
                            else:
                                if child_refund.product_id.is_gift:
                                    gift_val = {
                                            'product_id'            : child_refund.product_id.id,
                                            'quantity'              : child_refund.quantity,
                                            'price_unit'            :  - child_refund.price_unit,
                                            'invoice_line_tax_ids'  : [(6, 0, [x.id for x in child_refund.invoice_line_tax_ids])],
                                            'invoice_id'            : invoice.id,
                                            'name'                  : child_refund.name,
                                            }
                                    reciept_id = reciept_pool.create(gift_val)
                
                self.compute_taxes_r()
                max_child_id = max(latest_inv_id_list)
                invoice.write({'child_invoice_id' : max_child_id})
        return True
    
    @api.multi
    def invoice_sent(self):
        template = self.env.ref('account.email_template_edi_invoice', False)
        local_context = dict(
            default_model='account.invoice',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            custom_layout="account.mail_template_data_notification_email_account_invoice"
        )
        #template.with_context(local_context).send_mail(self.id)
        self.message_post_with_template(template.id, composition_mode='comment')
    
    @api.multi
    def invoice_sent_wlbdy(self):
        template = self.env.ref('wollbody_amazon_connection.email_template_edi_invoice_wollbody', False)
        local_context = dict(
            default_model='account.invoice',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            custom_layout="account.mail_template_data_notification_email_account_invoice"
        )
        #template.with_context(local_context).send_mail(self.id)
        self.message_post_with_template(template.id, composition_mode='comment')
    
#     @api.multi
#     def invoice_validate(self):
#         for invoice in self:
#             #refuse to validate a vendor bill/refund if there already exists one with the same reference for the same partner,
#             #because it's probably a double encoding of the same bill/refund
#             if invoice.type in ('in_invoice', 'in_refund') and invoice.reference:
#                 if self.search([('type', '=', invoice.type), ('reference', '=', invoice.reference), ('company_id', '=', invoice.company_id.id), ('commercial_partner_id', '=', invoice.commercial_partner_id.id), ('id', '!=', invoice.id)]):
#                     raise UserError(_("Duplicated vendor reference detected. You probably encoded twice the same vendor bill/refund."))
#             vals = {}
#             if invoice.type  == 'out_invoice':
#                 search_result = self.env['ir.sequence'].search([('code', '=', 'customer.invoice.sequence')])
#                 for obj in search_result:
#                     if invoice.is_shopware:
#                         obj.write({'prefix': 'w%(y)s%(month)s'})
#                         vals['number'] = self.env['ir.sequence'].next_by_code('customer.invoice.sequence') or 'New'
#                         vals['name'] = vals.get('number') 
#                     if invoice.is_amazon:
#                         obj.write({'prefix': 'ad%(y)s%(month)s'})
#                         vals['number'] = self.env['ir.sequence'].next_by_code('customer.invoice.sequence') or 'New'
#                         vals['name'] =  vals.get('number')
#             if invoice.type  == 'out_refund':
#                  vals['number'] = invoice.origin + self.env['ir.sequence'].next_by_code('customer.refund.sequence') or 'New'
#                  vals['name'] =  vals.get('number')
#                     
#         vals['state'] ='open'
#         return self.write(vals)
    
    
    @api.multi
    def action_invoice_sent_sale_reciept(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('wollbody_amazon_connection.email_template_edi_invoice_sale_reciept', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_partner_ids = [(6,0, [self.partner_id.id])],
            default_model='account.invoice',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            custom_layout="account.mail_template_data_notification_email_account_invoice"
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
    
    @api.multi
    def refund_process_all(self):
        for invoice in self:
            if invoice.state == 'draft':
                if invoice.type == 'out_refund':
                    invoice.action_invoice_open()
                    
                    
                    #register payment
                    journal_obj = self.env['account.journal']
                    journals = journal_obj.search([('name', '=', invoice.mother_invoice_id.payment_method)])
                    if journals:
                        
                        payment_type = self.env['account.payment.method'].search([('payment_type','=','outbound'),('code','=','manual')])
                        payment_dict = {
                                        'payment_type'          : 'outbound',
                                        'partner_type'          : 'customer',
                                        'invoice_ids'           : [(6,0,[invoice.id])],
                                        'partner_id'            : invoice.partner_id.id,
                                        'journal_id'            : journals.id,
                                        'payment_date'          : invoice.date_invoice,
                                        'communication'         : invoice.number,
                                        'amount'                : invoice.residual,
                                        'payment_method_id'     : payment_type.id,
                        }
                    
                        payment_id = self.env['account.payment'].create(payment_dict)
                        payment_id.post()
                        invoice.action_invoice_paid()
                        action = self.env.ref('account.action_invoice_tree1').read()[0]
                        action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
                        action['res_id'] = invoice.mother_invoice_id.id
                        invoice.mother_invoice_id.get_line()
                        
                        return action
            else:
                action = self.env.ref('account.action_invoice_tree1').read()[0]
                action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
                action['res_id'] = invoice.mother_invoice_id.id
                return action
    
    @api.multi
    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state not in ['proforma2', 'draft']):
            raise UserError(_("Invoice must be in draft or Pro-forma state in order to validate it."))
        to_open_invoices.action_date_assign()
        for invoice in self:
            #refuse to validate a vendor bill/refund if there already exists one with the same reference for the same partner,
            #because it's probably a double encoding of the same bill/refund
            vals = {}
            if invoice.type  == 'out_invoice':
                search_result = self.env['ir.sequence'].search([('code', '=', 'customer.invoice.sequence')])
                for obj in search_result:
                    if invoice.is_shopware:
                        obj.write({'prefix': 'w%(y)s%(month)s'})
                        vals['number'] = self.env['ir.sequence'].next_by_code('customer.invoice.sequence') or 'New'
                        #vals['name'] = vals.get('number') 
                    if invoice.is_amazon:
                        obj.write({'prefix': 'ad%(y)s%(month)s'})
                        vals['number'] = self.env['ir.sequence'].next_by_code('customer.invoice.sequence') or 'New'
                        #vals['name'] =  vals.get('number')
            if invoice.type  == 'out_refund':
                 vals['number'] = invoice.origin + self.env['ir.sequence'].next_by_code('customer.refund.sequence') or 'New'
                 #vals['name'] =  vals.get('number')
            
            if vals:
                invoice.write(vals)
        to_open_invoices.action_move_create()
        return to_open_invoices.invoice_validate()  
    
    
    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids:
                raise UserError(_('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
            date_invoice = inv.date_invoice
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)

            name = inv.name or '/'
            if inv.payment_term_id:
                totlines = inv.with_context(ctx).payment_term_id.with_context(currency_id=inv.currency_id.id).compute(total, date_invoice)[0]
                res_amount_currency = total_currency
                ctx['date'] = date_invoice
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': inv.id
                })
            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            line = inv.group_lines(iml, line)

            journal = inv.journal_id.with_context(ctx)
            line = inv.finalize_invoice_move_lines(line)

            date = inv.date or date_invoice
            move_vals = {
                'ref': inv.reference,
                'line_ids': line,
                'journal_id': journal.id,
                'date': date,
                'narration': inv.comment,
                'name': inv.number
            }
            ctx['company_id'] = inv.company_id.id
            ctx['invoice'] = inv
            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)
            move = account_move.with_context(ctx_nolang).create(move_vals)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post()
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'date': date,
                'move_name': move.name,
            }
            inv.with_context(ctx).write(vals)
        return True
    
class InvoiceRefundReason(models.Model):
    _name = 'invoice.refund.reason'
    name  = fields.Char('Name',required=1)
    
    
