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
import requests
import json

import logging

_logger = logging.getLogger(__name__)

headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
from woocommerce import API

class WooConfig(models.Model):
    _name = 'woo.config'
    
    name                = fields.Char('Name')
    api_url             = fields.Char('URL',default='https://schneewolle.de')
    consumer_key        = fields.Char('Consumer Key')
    consumer_secret     = fields.Char('Consumer Secret')
    state               = fields.Selection([('draft','Draft'),('connected','Connected'),('failed','Failed')],string='State', default='draft')
    
    @api.model
    def create(self, vals):
        wooo = self.env['woo.config'].search([])
        if wooo:
            raise UserError(_("Cannot Create Second"))
        
        return super(WooConfig,self).create(vals)
    
    @api.multi
    def action_test_connection(self):
        for woo in self:
            wcapi = API(
            url=woo.api_url,
            consumer_key=woo.consumer_key,
            consumer_secret=woo.consumer_secret,
            wp_api=True,
            version="wc/v1"
            )
            resp = wcapi.get("products")
            if resp.status_code == 200:
                woo.write({'state':'connected'})
            else:
                resp.headers['content-type']
                resp= resp.json()
                raise UserError(_('%s') % (resp.get('message')))
            
            
    
    
    @api.multi
    def action_import_product(self):
        for woo in self:
            wcapi = API(
            url=woo.api_url,
            consumer_key=woo.consumer_key,
            consumer_secret=woo.consumer_secret,
            wp_api=True,
            version="wc/v1"
            )
            resp = wcapi.get("products")
            if resp.status_code == 200:
                woo.write({'state':'draft'})
            else:
                resp.headers['content-type']
                resp= resp.json()
                raise UserError(_('%s') % (resp.get('message')))
            resp.headers['content-type']
            products = resp.json()
            
            for product in products:
                odoo_product = self.env['product.product'].search([('default_code','=',product.get('sku'))], limit=1)
                product_vals = {
                                'name'          : product.get('name'),
                                'default_code'  : product.get('sku'),
                                'woo_id'        : product.get('id'),
                                'list_price'    : product.get('price'),
                                'sale_ok'       : True,
                                'type'          : 'consu'
                    }
                if odoo_product:
                    odoo_product.write(product_vals)
                else:
                    odoo_product = self.env['product.product'].create(product_vals)
                    
                
                
            
        
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    woo_id      = fields.Char(string='Wooo ID')

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    woo_id      = fields.Char(string='Wooo ID')

class Partner(models.Model):
    _inherit = 'res.partner'
    
    woo_id      = fields.Char(string='Wooo ID')
                    
        