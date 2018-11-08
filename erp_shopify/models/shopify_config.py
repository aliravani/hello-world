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
                        print (variant)
                        odoo_products = self.env['product.product'].search([('default_code','=',variant.get('sku'))], limit=1)
                        if odoo_products:
                            odoo_products.write({
                                                'name'          : response_template.get('title') + ' - ' +variant.get('title'),
                                                #'type'          : 'product',
                                                'shopify_id'    : variant.get('id'),
                                    })
                        if not odoo_products:
                            odoo_products = self.env['product.product'].create({
                                                'name'          : response_template.get('title') +' - ' +variant.get('title'),
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
                orders = shopify_resp.Order().find(status='unshipped',limit=250,page=2)
                product_uom = self.env['product.uom.categ'].search([('name','=','Unit')])
                for order in orders:
                    response_template = order.to_dict()
                    sale_order = self.env['sale.order'].search([('name','=',response_template.get('order_number')),('shopify_id','=',response_template.get('id'))])
                    if not sale_order:
                        partner_shipping = False
                        partner = False
                        customer_resp = response_template.get('customer')
                        
                        country = self.env['res.country'].search([('name','=',customer_resp['default_address'].get('country_name'))])
                        partner_vals = {
                                            'first_name'    : customer_resp.get('first_name'),
                                            'last_name'     : customer_resp.get('last_name') if customer_resp.get('last_name') else '-',
                                            'name'          : customer_resp.get('first_name') + ' ' + customer_resp.get('last_name') if customer_resp.get('last_name') else '-',
                                            'email'         : customer_resp.get('email'),
                                            'custom_company_name' : customer_resp['default_address'].get('company'),
                                            'street2'       : customer_resp['default_address'].get('address1'),
                                            'street'        : customer_resp['default_address'].get('address2'),
                                            'city'          : customer_resp['default_address'].get('city'),
                                            'zip'           : customer_resp['default_address'].get('zip'),
                                            'phone'         : customer_resp['default_address'].get('phone'),
                                            'country_id'    : country.id if country else False,
                                            'customer'      : True,
                                            'shopify_id'    : customer_resp.get('id'),
                            
                            }
                        
                        
                        partner = self.env['res.partner'].search([('email','=',customer_resp.get('email')),('shopify_id','=',customer_resp.get('id'))])
                        if partner:
                            partner.write(partner_vals)
                        if not partner:
                            partner = self.env['res.partner'].create(partner_vals)
                        
                        if partner:
                            country = self.env['res.country'].search([('name','=',response_template['shipping_address'].get('country_name'))])
                            if not partner.street2 == response_template['shipping_address'].get('address1'):
                                partner_shipping = self.env['res.partner'].search([('type','=','delivery'),('street2','=',response_template['shipping_address'].get('address1'))])
                                if not partner_shipping:
                                    shipping_vals = {
                                                    'parent_id'     : partner.id,
                                                    'type'          : 'delivery',
                                                    'street2'       : response_template['shipping_address'].get('address1'),
                                                    'street'        : response_template['shipping_address'].get('address2'),
                                                    'city'          : response_template['shipping_address'].get('city'),
                                                    'zip'           : response_template['shipping_address'].get('zip'),
                                                    'phone'         : response_template['shipping_address'].get('phone'),
                                                    'first_name'    : response_template['shipping_address'].get('first_name'),
                                                    'last_name'     : response_template['shipping_address'].get('last_name') if response_template['shipping_address'].get('last_name') else '-',
                                                    'name'          : response_template['shipping_address'].get('first_name') + ' ' + response_template['shipping_address'].get('last_name') if response_template['shipping_address'].get('last_name') else '-', 
                                                    'country_id'    : country.id if country else False,
                                        }
                                    
                                    partner_shipping = self.env['res.partner'].create(shipping_vals)
                         
                        sale_order = self.env['sale.order'].create({
                                        'shopify_id'            : response_template.get('id'),
                                        'partner_id'            : partner.id,
                                        'partner_shipping_id'   : partner_shipping.id if partner_shipping else partner.id,
                                        'partner_invoice_id'    : partner.id,
                                        'name'                  : response_template.get('order_number'),
                                        'date_order'            : response_template.get('created_at') 
                            })
                        print ('sale_order sale_order     ',sale_order)
                        for line in response_template.get('line_items'):
                            if line.get('variant_id'):
                                product = self.env['product.product'].search([('shopify_id','=',line.get('variant_id'))])
                                if not product:
                                    shop.action_import_products()
                                    product = self.env['product.product'].search([('shopify_id','=',line.get('variant_id'))])
                                    
                                if product:
                                    name = product.name_get()[0][1]
                                    if product.description_sale:
                                        name += '\n' + product.description_sale
                                    sale_line = self.env['sale.order.line'].create({
                                                        'order_id'          : sale_order.id,
                                                        'product_id'        : product.id,
                                                        'name'              : name,
                                                        'product_uom_qty'   : line.get('quantity'),
                                                        'price_unit'        : line.get('price'), 
                                                        'product_uom'       : product_uom.id if product_uom else False  #unit
                                        })
                
                
                orders_paid = shopify_resp.Order().find(financial_status='paid',limit=250,page=2)
                product_uom = self.env['product.uom.categ'].search([('name','=','Unit')])
                for order_paid in orders_paid:
                    response_template = order_paid.to_dict()
                    sale_order = self.env['sale.order'].search([('name','=',response_template.get('order_number')),('shopify_id','=',response_template.get('id'))])
                    if not sale_order:
                        partner_shipping = False
                        partner = False
                        customer_resp = response_template.get('customer')
                        
                        country = self.env['res.country'].search([('name','=',customer_resp['default_address'].get('country_name'))])
                        partner_vals = {
                                            'first_name'    : customer_resp.get('first_name'),
                                            'last_name'     : customer_resp.get('last_name') if customer_resp.get('last_name') else '-',
                                            'name'          : customer_resp.get('first_name') + ' ' + customer_resp.get('last_name') if customer_resp.get('last_name') else '-',
                                            'email'         : customer_resp.get('email'),
                                            'custom_company_name' : customer_resp['default_address'].get('company'),
                                            'street2'       : customer_resp['default_address'].get('address1'),
                                            'street'        : customer_resp['default_address'].get('address2'),
                                            'city'          : customer_resp['default_address'].get('city'),
                                            'zip'           : customer_resp['default_address'].get('zip'),
                                            'phone'         : customer_resp['default_address'].get('phone'),
                                            'country_id'    : country.id if country else False,
                                            'customer'      : True,
                                            'shopify_id'    : customer_resp.get('id'),
                            
                            }
                        
                        
                        partner = self.env['res.partner'].search([('email','=',customer_resp.get('email')),('shopify_id','=',customer_resp.get('id'))])
                        if partner:
                            partner.write(partner_vals)
                        if not partner:
                            partner = self.env['res.partner'].create(partner_vals)
                        
                        if partner:
                            country = self.env['res.country'].search([('name','=',response_template['shipping_address'].get('country_name'))])
                            if not partner.street2 == response_template['shipping_address'].get('address1'):
                                partner_shipping = self.env['res.partner'].search([('type','=','delivery'),('street2','=',response_template['shipping_address'].get('address1'))])
                                if not partner_shipping:
                                    shipping_vals = {
                                                    'parent_id'     : partner.id,
                                                    'type'          : 'delivery',
                                                    'street2'       : response_template['shipping_address'].get('address1'),
                                                    'street'        : response_template['shipping_address'].get('address2'),
                                                    'city'          : response_template['shipping_address'].get('city'),
                                                    'zip'           : response_template['shipping_address'].get('zip'),
                                                    'phone'         : response_template['shipping_address'].get('phone'),
                                                    'first_name'    : response_template['shipping_address'].get('first_name'),
                                                    'last_name'     : response_template['shipping_address'].get('last_name') if response_template['shipping_address'].get('last_name') else '-',
                                                    'name'          : response_template['shipping_address'].get('first_name') + ' ' + response_template['shipping_address'].get('last_name') if response_template['shipping_address'].get('last_name') else '-', 
                                                    'country_id'    : country.id if country else False,
                                        }
                                    
                                    partner_shipping = self.env['res.partner'].create(shipping_vals)
                         
                        sale_order = self.env['sale.order'].create({
                                        'shopify_id'            : response_template.get('id'),
                                        'partner_id'            : partner.id,
                                        'partner_shipping_id'   : partner_shipping.id if partner_shipping else partner.id,
                                        'partner_invoice_id'    : partner.id,
                                        'name'                  : response_template.get('order_number'),
                                        'date_order'            : response_template.get('created_at') 
                            })
                        print ('sale_order sale_order 22222    ',sale_order)
                        for line in response_template.get('line_items'):
                            if line.get('variant_id'):
                                product = self.env['product.product'].search([('shopify_id','=',line.get('variant_id'))])
                                if not product:
                                    shop.action_import_products()
                                    product = self.env['product.product'].search([('shopify_id','=',line.get('variant_id'))])
                                    
                                if product:
                                    name = product.name_get()[0][1]
                                    if product.description_sale:
                                        name += '\n' + product.description_sale
                                    sale_line = self.env['sale.order.line'].create({
                                                        'order_id'          : sale_order.id,
                                                        'product_id'        : product.id,
                                                        'name'              : name,
                                                        'product_uom_qty'   : line.get('quantity'),
                                                        'price_unit'        : line.get('price'), 
                                                        'product_uom'       : product_uom.id if product_uom else False  #unit
                                        })
                    
                    
                    
                
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    shopify_id      = fields.Char(string='Shopify ID')

class Product(models.Model):
    _inherit = 'product.product'
    
    shopify_id      = fields.Char(string='Shopify ID')

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    shopify_id      = fields.Char(string='Shopify ID')

class Partner(models.Model):
    _inherit = 'res.partner'
    
    shopify_id      = fields.Char(string='Shopify ID')
                    
        