# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid

from itertools import groupby
from datetime import datetime, timedelta
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

from odoo.tools.misc import formatLang

from odoo.addons import decimal_precision as dp

class CaseType(models.Model):
    _name = 'case.type'
    
    name = fields.Char('Name')

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    doctor_id               = fields.Many2one('res.partner','Check Up by Doctor')
    check_up_date           = fields.Date('Checkup Date')
    power_type_id           = fields.Many2one('power.type','Power Type')
    eye_test_type_id        = fields.Many2one('eye.test.type','Eye test type')
    category_id             = fields.Many2many('res.partner.category', column1='sale_order_id',column2='category_id', string='Tags')
    age_year                = fields.Float('Age(In Years)')
    mobile                  = fields.Char('Mobile')
    phone                   = fields.Char('Phone')
    email                   = fields.Char('Email')
    birthdate               = fields.Date('Birthdate')
    vat                     = fields.Char('GSTIN')
    checkup_lines           = fields.One2many('easy.checkup.line','sale_id','Lines')
    case_type_id            = fields.Many2one('case.type','Case Type')
    #Recommendation
    
    mineral                 = fields.Boolean('Mineral')
    sv                      = fields.Boolean('S.V.')
    anti_reflection         = fields.Boolean('Anti Reflection')
    hi_index                = fields.Boolean('Hi Index')
    organic                 = fields.Boolean('Organic')
    bi_focal                = fields.Boolean('Bi Focal')
    tinting                 = fields.Boolean('Tinting')
    saftey                  = fields.Boolean('Saftey')
    photo_chromic           = fields.Boolean('Photochromic')
    progressive             = fields.Boolean('Progressive')
    mira_coat               = fields.Boolean('Mira Coat-Scratch Resistance')
    other                   = fields.Boolean('Other')
                
    
    
    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'user_id': self.partner_id.user_id.id or self.env.uid,
            'mobile': self.partner_id.mobile,
            'phone': self.partner_id.phone,
            'email': self.partner_id.email,
            'birthdate': self.partner_id.birthdate,
            'category_id': self.partner_id.category_id,
            'vat': self.partner_id.vat
        }
        if self.env['ir.config_parameter'].sudo().get_param('sale.use_sale_note') and self.env.user.company_id.sale_note:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note

        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id
        self.update(values)
        

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    categ_id = fields.Many2one('product.category', 'Internal Category')
    name = fields.Text(string='Description', required=False)
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', required=False)