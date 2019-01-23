# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import psycopg2

import odoo.addons.decimal_precision as dp

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError, except_orm
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    @api.depends('product_variant_ids.pakdo')
    def _compute_pakdo_pushed(self):
        for template in self:
            pakdo_list = []
            for product in template.product_variant_ids:
                if product.pakdo:
                    pakdo_list.append('True')
                else:
                    pakdo_list.append('False')
            
            if not 'False' in pakdo_list:
                template.update({'pakdo_pushed':True})
            else:
                template.update({'pakdo_pushed':False})
    
    
    @api.depends('product_variant_ids.pakdo_image')
    def _compute_pakdo_image_pushed(self):
        for template in self:
            pakdo_list = []
            for product in template.product_variant_ids:
                if product.pakdo_image:
                    pakdo_list.append('True')
                else:
                    pakdo_list.append('False')
            
            if not 'False' in pakdo_list:
                template.update({'pakdo_image_pushed':True})
            else:
                template.update({'pakdo_image_pushed':False})
    
    pakdo_pushed           = fields.Boolean('Pakdo Pushed', compute='_compute_pakdo_pushed',store=True)
    pakdo_image_pushed     = fields.Boolean('Pakdo Image Pushed', compute='_compute_pakdo_image_pushed',store=True)
    image_pushed_method    = fields.Boolean('Image Pushed Method')
    
    
    @api.multi
    def push_mother_pakdo(self):
        _logger.info("Pushing product single mother to Pakdo...")
        pakdo = self.env['pakdo.config'].search([])
        for tmpl in self:
            for product in tmpl.product_variant_ids:
                if not product.barcode:
                    raise UserError(_('Please add Barcode of ' + product.name +','+product.color_name ))
                else:
                    pakdo.push_product(product)
            
        return True
    
    @api.multi
    def push_mother_all_pakdo(self):
        _logger.info("Pushing product All mother to Pakdo...")
        pakdo = self.env['pakdo.config'].search([])
        for tmpl in self.get_alternative:
            for product in tmpl.product_variant_ids:
                if not product.barcode:
                    raise UserError(_('Please add Barcode of ' + product.name +',' + product.color_name ))
                else:
                    pakdo.push_product(product)
        
        ########################
        for product in self.product_variant_ids:
            if not product.barcode:
                raise UserError(_('Please add Barcode of ' + product.name +',' + product.color_name ))
            else:
                pakdo.push_product(product)
        
        return True
    
    @api.multi
    def update_mother_pakdo(self):
        _logger.info("Updating product single mother to Pakdo...")
        pakdo = self.env['pakdo.config'].search([])
        for tmpl in self:
            for product in tmpl.product_variant_ids:
                if not product.barcode:
                    raise UserError(_('Please add Barcode of ' + product.name +','+product.color_name ))
                else:
                    pakdo.update_product(product)
            
        return True  
    
    @api.multi
    def update_mother_all_pakdo(self):
        _logger.info("Updating product All mother to Pakdo...")
        pakdo = self.env['pakdo.config'].search([])
        for tmpl in self.get_alternative:
            for product in tmpl.product_variant_ids:
                if not product.barcode:
                    raise UserError(_('Please add Barcode of ' + product.name +',' + product.color_name ))
                else:
                    pakdo.update_product(product)
        
        ########################
        for product in self.product_variant_ids:
            if not product.barcode:
                raise UserError(_('Please add Barcode of ' + product.name +',' + product.color_name ))
            else:
                pakdo.update_product(product)
        
        return True
    
    
    
    @api.multi
    def delete_mother_pakdo(self):
        _logger.info("Deleting product single mother to Pakdo...")
        pakdo = self.env['pakdo.config'].search([])
        for tmpl in self:
            for product in tmpl.product_variant_ids:
                if not product.barcode:
                    raise UserError(_('Please add Barcode of ' + product.name +','+product.color_name ))
                else:
                    pakdo.delete_product(product)
            
        return True  
    
    @api.multi
    def delete_mother_all_pakdo(self):
        _logger.info("Deleting product All mother to Pakdo...")
        pakdo = self.env['pakdo.config'].search([])
        for tmpl in self.get_alternative:
            for product in tmpl.product_variant_ids:
                if not product.barcode:
                    raise UserError(_('Please add Barcode of ' + product.name +',' + product.color_name ))
                else:
                    pakdo.delete_product(product)
        
        ########################
        for product in self.product_variant_ids:
            if not product.barcode:
                raise UserError(_('Please add Barcode of ' + product.name +',' + product.color_name ))
            else:
                pakdo.delete_product(product)
        
        return True
class ProductProduct(models.Model):
    _inherit = "product.product"
    
    
    @api.multi
    def push_single_pakdo(self):
        _logger.info("Pushing product single mother to Pakdo...")
        pakdo = self.env['pakdo.config'].search([])
        
        for product in self:
            if not product.barcode:
                raise UserError(_('Please add Barcode of ' + product.name +','+product.color_name ))
            else:
                pakdo.push_product(product)
            
        return True
    
    
    @api.multi
    def update_single_pakdo(self):
        _logger.info("Updating product single mother to Pakdo...")
        pakdo = self.env['pakdo.config'].search([])
        
        for product in self:
            if not product.barcode:
                raise UserError(_('Please add Barcode of ' + product.name +','+product.color_name ))
            else:
                pakdo.update_product(product)
            
        return True  
    
    @api.multi
    def delete_single_pakdo(self):
        _logger.info("Deleting product single mother to Pakdo...")
        pakdo = self.env['pakdo.config'].search([])
        
        for product in self:
            if not product.barcode:
                raise UserError(_('Please add Barcode of ' + product.name +','+product.color_name ))
            else:
                pakdo.delete_product(product)
            
        return True
    
    