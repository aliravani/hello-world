# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import psycopg2

import odoo.addons.decimal_precision as dp

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, except_orm


class ComboProduct(models.Model):
    _name = "product.combo"
    _description = "Product packs"


    name = fields.Char('name', related='product_template_id2.name')
    product_template_id = fields.Many2one('product.template', 'Item')
    product_quantity = fields.Float('Quantity', default='1', required=True)
    product_template_id2 = fields.Many2one('product.template', 'Product', required=False)
    uom_id = fields.Many2one('product.uom', related='product_template_id2.uom_id')
    price = fields.Float('Product_price')
    allow = fields.Integer('Allow', related='product_template_id.allow_combo')

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_combo = fields.Boolean('Combo Product', default=False)
    combo_product_id = fields.One2many('product.combo', 'product_template_id', 'Combo Item')
    allow_combo     = fields.Integer('Allow Combo')
    
    @api.multi
    def name_get(self):
        res = []
        for template in self:
            name = template.name 
            if template.default_code:
                name = name + '[' + template.default_code + ']'   
            res.append((template.id, name))
        return res