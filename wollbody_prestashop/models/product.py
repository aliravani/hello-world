# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime, timedelta, date
import pytz

import odoo.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
#     @api.one
#     def _get_color(self):
#         for tmpl in self:
#             colors = self.env['product.color'].search([('name','=',tmpl.color_name)], limit=1)
#             if colors:
#                 self.get_color_id = colors.id
#             else:
#                 if tmpl.color_name:
#                     colors = self.env['product.color'].create({'name': tmpl.color_name})
#                     self.get_color_id = colors.id
    
    @api.one
    def _get_all_child(self):
        self.ensure_one()
        template_ids = self.search([('art_no','=',self.art_no),('art_no','!=',False)])
        if template_ids:
            ids_list = []
            for tmpl in template_ids:
                if tmpl.product_variant_ids:
                    for child in tmpl.product_variant_ids:
                        ids_list.append(child.id)
            self.get_all_child = ids_list
    
    
    @api.one
    def _impact_on_price(self):
        self.ensure_one()
        template_ids = self.search([('art_no','=',self.art_no),('art_no','!=',False)])
        print 'template_ids    ',template_ids
        if template_ids:
            price_list = []
            for tmpl in template_ids:
                if tmpl.product_variant_ids:
                    for child in tmpl.product_variant_ids:
                        if child.presta_price_push > 0:
                            price_list.append(child.presta_price_push)
            if price_list:
                self.impact_on_price = min(price_list)
            else:
                self.impact_on_price = 0
        
        
    
#     presta_additional_shipping_cost     = fields.Float('Additional shipping cost')
#     presta_categories                   = fields.Many2many('prestashop.category','rel_prestashop_category_product','product_id','prestashop_category_id','Prestashop Category')
#     presta_feature                      = fields.Many2many('prestashop.feature','rel_prestashop_feature_product','product_id','prestashop_feature_id','Prestashop Features')
#     
#     presta_is_english                   = fields.Boolean('Is english')
#     presta_is_german                    = fields.Boolean('Is German')
#     presta_images                       = fields.Binary('Images')
#     
#     presta_condition                    = fields.Char('Condition')
#     
#     presta_id                           = fields.Integer('Prestashop ID')
#     presta_id_shop_1                    = fields.Boolean('English Shop')
#     presta_id_shop_2                    = fields.Boolean('German Shop')
#     #presta_id_supplier                  
#     presta_manufacturer_name            = fields.Char('Manufacturer name')
#     
#     get_color_id                        = fields.Many2one('product.color', compute='_get_color',string='Prestashop Color')
#     get_all_child                       = fields.Many2many('product.product',compute='_get_all_child', string='All Childs')
    
    
    
    presta_link                         = fields.Char('Link')
    presta_additional_shipping_cost     = fields.Float('Additional shipping cost')
    presta_categories                   = fields.Many2many('prestashop.category','rel_prestashop_category_product','product_id','prestashop_category_id','Prestashop Category')
    presta_feature                      = fields.Many2many('prestashop.feature','rel_prestashop_feature_product','product_id','prestashop_feature_id','Prestashop Features')
    presta_is_english                   = fields.Boolean('Is english')
    presta_is_german                    = fields.Boolean('Is German')
    presta_images                       = fields.Binary('Images')
    #presta_product_features (m2m)
    presta_condition                    = fields.Char('Condition')
    presta_description_english          = fields.Text('English Description')
    presta_description_german           = fields.Text('German Description')
    presta_description_short_english    = fields.Text('English Short Description')
    presta_description_short_german     = fields.Text('German Short Description')
    presta_id                           = fields.Char('Prestashop ID')
    presta_id_shop_1                    = fields.Boolean('English Shop')
    presta_id_shop_2                    = fields.Boolean('German Shop')
    #presta_id_supplier                  
    presta_manufacturer_name            = fields.Char('Manufacturer name')
    
    
    presta_meta_description_english     = fields.Text('English Meta Description',size=160)
    presta_meta_description_german      = fields.Text('German Meta Description',size=160)
    
    
    
    presta_meta_keywords_english        = fields.Char('English Keywords')
    presta_meta_keywords_german         = fields.Char('German Keywords')
    
    presta_meta_title_english           = fields.Char('English Meta Title',size=70)
    presta_meta_title_german            = fields.Char('German Meta Title',size=70)
    
    presta_name_english                 = fields.Char('English Name')
    presta_name_german                  = fields.Char('German Name')
    
    
    
    get_color_id                        = fields.Many2one('product.color',string='Prestashop Color')
    
    
    
    get_all_child                       = fields.Many2many('product.product',compute='_get_all_child', string='All Childs')
    presta_default_category_id          = fields.Many2one('prestashop.category','Default Category')
    presta_image_id                     = fields.Char('Presta Image ID')
    
    impact_on_price                     = fields.Float(compute='_impact_on_price', string="Basic Price",digits=dp.get_precision('Payment Terms'))
    
    @api.multi
    def push_product(self):
        presta = self.env['prestashop.config'].search([], limit=1)
        if presta:
            product_tmpl = self
            presta.push_product(product_tmpl)
    
    @api.multi
    def update_product_details(self):
        presta = self.env['prestashop.config'].search([], limit=1)
        if presta:
            product_tmpl = self
            presta.update_product_details(product_tmpl)
            
    @api.multi
    def push_single_product(self):
        presta = self.env['prestashop.config'].search([], limit=1)
        if presta:
            product_tmpl = self
            presta.push_single_product(product_tmpl)
    
    @api.multi
    def presta_apply_all(self):
        for tmpl in self:
            for alter in tmpl.get_alternative:
                vals = {
                        'name'                                  : tmpl.name,
                        'german_name'                           : tmpl.german_name,
                        'swedish_name'                          : tmpl.swedish_name,
                        'presta_meta_description_english'             : tmpl.presta_meta_description_english,
                        'presta_meta_description_german'       : tmpl.presta_meta_description_german,
                        'presta_meta_keywords_english'           : tmpl.presta_meta_keywords_english,
                        'presta_meta_keywords_german'             : tmpl.presta_meta_keywords_german,
                        'presta_meta_title_english'       : tmpl.presta_meta_title_english,
                        'presta_meta_title_german'           : tmpl.presta_meta_title_german,
                        'presta_description_english'             : tmpl.presta_description_english,
                        'presta_description_german'       : tmpl.presta_description_german,
                        'presta_description_short_english'           : tmpl.presta_description_short_english,
                        'presta_description_short_german'      : tmpl.presta_description_short_german,
                        'presta_default_category_id'        : tmpl.presta_default_category_id.id,
                        'related_supplier_id'               : tmpl.related_supplier_id.id
                        
                }
                if tmpl.presta_categories:
                    vals['presta_categories'] = [(6, 0, tmpl.presta_categories.ids)]
                
                alter.write(vals)

        return True

    @api.multi
    def get_presta_color(self):
        templates = self.search([])
        if templates:
            for tmpl in templates:
                colors = self.env['product.color'].search([('name','=',tmpl.color_name)], limit=1)
                if colors:
                    tmpl.write({'get_color_id': colors.id})
    
    @api.multi
    def clear_presta(self):
        if self.get_all_child:
            _logger.info("clear presta start.......................      " )
            for child in self.get_all_child:
                child.write({'presta_child_id' : 0, 'presta_specific_price_id':False})
                if child.product_tmpl_id:
                    child.product_tmpl_id.write({'presta_id': 0,'presta_link': False,'presta_image_id': 0})
                    _logger.info("clear presta done .......................      " )
        
        return True
    
    @api.multi
    def export_product_specific_prices(self):
        presta = self.env['prestashop.config'].search([], limit=1)
        if presta:
            template = self
            for variant in template.get_all_child:
                print 'variant    ',variant 
            #presta.export_product_specific_prices(variant)
        return True
    
class ProductProduct(models.Model):
    _inherit = "product.product"
    
    @api.multi
    def _get_presta_price_push(self):
        for product in self:
            price = product.lst_price / 1.19
            product.update({'presta_price_push': price})
            
    @api.one
    def _child_impact_on_price(self):
        self.ensure_one()
        for product in self:
            product.child_impact_on_price = product.presta_price_push - product.product_tmpl_id.impact_on_price       
     
      
    
    presta_price        = fields.Float('Price')
    presta_child_id     = fields.Char('Prestashop Child ID')
    presta_qty          = fields.Integer('Prestashop QTY')
    presta_specific_price_id            = fields.Char('Specific Price ID')
    presta_specific_price = fields.Float('Specific price')
    presta_stock_id     = fields.Char('Presta Stock ID')
    presta_price_push                        = fields.Float(string='Sale Price (Tax Excl)',digits=dp.get_precision('Payment Terms'),store=False, compute='_get_presta_price_push')
    child_impact_on_price                     = fields.Float(compute='_child_impact_on_price', string="Impact on price",digits=dp.get_precision('Payment Terms'))
    
    @api.multi
    def export_product_specific_prices(self):
        presta = self.env['prestashop.config'].search([], limit=1)
        if presta:
            variant = self
            presta.export_product_specific_prices(variant)
        return True

class ProductAttributevalue(models.Model):
    _inherit = "product.attribute.value"
    
    prestashop_id = fields.Char('Prestashop ID')
    
class ProductColor(models.Model):
    _name = 'product.color'
    
    name            = fields.Char('German Name', required=True)
    english_name    = fields.Char('English Name')
    prestashop_id   = fields.Char('Prestashop ID')

class ArticleMaterial(models.Model):
    _inherit = 'article.material'
    
    english_name = fields.Char('English Name')
    presta_id = fields.Char('Prestashop ID')
    presta_material_id = fields.Char('Prestashop Material ID')    