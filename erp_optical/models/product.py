# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import psycopg2

from odoo.addons import decimal_precision as dp

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, RedirectWarning, except_orm
from odoo.tools import pycompat

class ProductMake(models.Model):
    _name = 'product.make'
    
    name = fields.Char('Make')

class ProductShape(models.Model):
    _name = 'product.shape'
    
    name = fields.Char('Shape')

class ProductSize(models.Model):
    _name = 'product.size'
    
    name = fields.Char('Size')
    
class Productcolor(models.Model):
    _name = 'product.color'
    
    name = fields.Char('Color')  

class FrameType(models.Model):
    _name = 'frame.type'
    
    name = fields.Char('Name')


class ProductValidity(models.Model):
    _name = 'product.validity'
    
    name = fields.Char('Name')

  

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    product_make_id             = fields.Many2one('product.make','Make')
    product_shape_id            = fields.Many2one('product.shape','Shape')
    product_size_id             = fields.Many2one('product.size','Size')
    product_color_id            = fields.Many2one('product.color','Color')
    frame_type_id               = fields.Many2one('frame.type','Frame Type')
    product_validity_id         = fields.Many2one('product.validity','Validity')    