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
import shopify

class ShopifyConfig(models.Model):
    _name = 'shopify.config'
    
    name    = fields.Char('Name')
    api_url     = fields.Char('URL',default='wisefood-shop.myshopify.com')
    api_key     = fields.Char('API Key')
    api_pwd     = fields.Char('Password')
    state       = fields.Selection([('draft','Draft'),('connected','Connected'),('failed','Failed')],string='State', default='draft')
    
    @api.model
    def create(self, vals):
        shopify = self.env['shopify.config'].search([])
        if shopify:
            raise UserError(_("Cannot Create Second"))
        
        return super(ShopifyConfig,self).create(vals)
    
    @api.multi
    def action_test_connection(self):
        shop=self.api_url.split("//")
        if len(shop) == 2:
            shop_url = shop[0]+"//"+self.api_key+":"+self.api_pwd+"@"+shop[1]+"/admin"
        else :
            shop_url = "https://"+self.api_key+":"+self.api_pwd+"@"+shop[0]+"/admin"
        shopify.ShopifyResource.set_site(shop_url)
        
        
        try:
            shop_id = shopify.Shop.current()
            shopify_resp = shopify
            self.write({'state':'connected'})
            return shopify_resp
        except Exception as e:
            raise Warning(e)
    
    
    @api.multi
    def action_import_products(self):
        for shop in self:
            if shop.state == 'connected':
                shopify_resp = shop.action_test_connection()
                products = shopify_resp.Product().find(limit=250)
                for product in products:
                    response_template=product.to_dict()
                    for variant in response_template.get('variants'):
                        odoo_products = self.env['product.template'].search([('default_code','=',variant.get('sku'))], limit=1)
                        if odoo_products:
                            odoo_products.write({
                                                'name'          : variant.get('title'),
                                                #'type'          : 'product',
                                                'shopify_id'    : variant.get('id'),
                                    })
                        if not odoo_products:
                            odoo_products = self.env['product.template'].create({
                                                'name'          : variant.get('title'),
                                                'type'          : 'product',
                                                'shopify_id'    : variant.get('id'),
                                                'default_code'  : variant.get('sku')
                                    })
    
    @api.multi
    def action_import_order(self):
        for shop in self:
            if shop.state == 'connected':
                shopify_resp = shop.action_test_connection()
                print ('>>>>>>>>>>      ',dir(shopify_resp))
                orders = shopify_resp.Order().find(limit=250)
                for order in orders:
                    response_template = order.to_dict()
                    print ('response_template      ',response_template)
                    
                
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    shopify_id      = fields.Char(string='Shopify ID')
                    
        