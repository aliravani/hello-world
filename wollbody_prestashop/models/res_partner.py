# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    presta_supplier_id   = fields.Char('Prestashop Supplier ID')
    presta_customer_id   = fields.Char('Prestashop Customer ID')
    presta_address_id    = fields.Char('Prestashop Address ID')