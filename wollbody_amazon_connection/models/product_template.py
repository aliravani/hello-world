# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import psycopg2

import odoo.addons.decimal_precision as dp

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, except_orm


class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    @api.depends('product_variant_ids')
    def _compute_get_small_child(self):
        for template in self:
            size_list = []
            for product in template.product_variant_ids:
                size_list.append(product.id)
            if size_list:
                obj = self.env['product.product'].browse(size_list[0]).default_code
                template.update({
                                 'get_small_child' : size_list[0],
                                 'small_child_sku' : self.env['product.product'].browse(size_list[0]).default_code, 
                                 })
    
    @api.depends('product_variant_ids.total_child_qty')
    def _total_qty(self):
        for template in self:
            total_qty = 0
            for product in template.product_variant_ids:
                total_qty += product.total_child_qty
            template.update({'total_qty' : total_qty})
    
    @api.depends('product_variant_ids.wlbdy_qty','product_variant_ids.pakdo_qty')
    def _wldy_pakdo_qty(self):
        for template in self:
            wldy_pakdo_qty = 0
            for product in template.product_variant_ids:
                total_qty = product.wlbdy_qty + product.pakdo_qty
                wldy_pakdo_qty += total_qty 
            template.update({'wldy_pakdo_qty' : wldy_pakdo_qty})
    
    @api.depends('related_supplier_id')
    def _supplier_name(self):
        for template in self:
            if template.related_supplier_id:
                template.update({'supplier_name':template.related_supplier_id.name})
        
    
    related_supplier_id       = fields.Many2one('res.partner', 'Supplier')
    supplier_name             = fields.Char('Supplier Name',compute='_supplier_name')
    art_no                    = fields.Char('Article number',size=32, help='Artikelnummer des Herstellers')
    art_no_original           = fields.Char('Article number original',size=32, help='Artikelnummer des Herstellers')
    art_name                  = fields.Char('Article name', size=50, help='Artikelname des Herstellers', translate=True)
    color_no                  = fields.Char('Color number', size=32, help='Colornumber')
    color_name                = fields.Char('Color', size=50, help='Color', translate=True)
    material_id               = fields.Many2one('article.material','Material')
    single_size               = fields.Char('Single Size')
    
    get_small_child           = fields.Many2one('product.product', 'Small Child', compute='_compute_get_small_child',store=False)
    small_child_sku           = fields.Char('Small Child SKU', compute='_compute_get_small_child',store=False)
    
    is_gift                   = fields.Boolean('Gift')
    german_name               = fields.Char('German Name')
    swedish_name              = fields.Char('Swedish Name')
    total_qty                 = fields.Integer('Total Qty', compute='_total_qty', store=False)
    type                      = fields.Selection(default='product')
    wldy_pakdo_qty            = fields.Integer('Wldby-Pakdo Qty', compute='_wldy_pakdo_qty', store=False)
    

class ArticleMaterial(models.Model):
    _name = 'article.material'
    
    name = fields.Char('Name')