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
import re

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
                orders = shopify_resp.Order().find(fulfillment_status='unshipped',financial_status='paid',limit=250)
                product_uom = self.env['product.uom.categ'].search([('name','=','Unit')])
                for order in orders:
                    response_template = order.to_dict()
                    sale_order = self.env['sale.order'].search([('name','=',response_template.get('order_number')),('shopify_id','=',response_template.get('id'))])
                    if not sale_order:
                        partner_shipping = False
                        partner = False
                        
                        
                        customer_resp = response_template.get('customer')
                        street_no = ''
                        street_no_list = re.findall(r'\d+', customer_resp['default_address'].get('address1'))
                        if street_no_list:
                            street_no = street_no_list[0]
                        
                        street_name = ''
                        street1 = re.sub(r'\d+', '', customer_resp['default_address'].get('address1'))
                        if street1:
                            if customer_resp['default_address'].get('address2'):
                                street_name = street1 + customer_resp['default_address'].get('address2')
                            else:
                                street_name = street1 

                        country = self.env['res.country'].search([('name','=',customer_resp['default_address'].get('country_name'))])
                        partner_vals = {
                                            'first_name'    : customer_resp.get('first_name'),
                                            'last_name'     : customer_resp.get('last_name') if customer_resp.get('last_name') else '-',
                                            'name'          : customer_resp.get('first_name') + ' ' + customer_resp.get('last_name') if customer_resp.get('last_name') else '-',
                                            'email'         : customer_resp.get('email'),
                                            'custom_company_name' : customer_resp['default_address'].get('company'),
                                            'street2'       : street_name,
                                            'street'        : street_no,
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
                        
                        shipcloud_carrier_id = False
                        carrier_services_id = False
                        package_type_id = False
                        
                        if response_template.get('shipping_lines'):
                            
                            shipping_lines = response_template.get('shipping_lines')
                            print ('shipping_lines shipping_lines        ',shipping_lines)
                            if len(shipping_lines) >= 1:
                                #if shipping_lines[0].get('code') == 'DHL':
                                dhl_id = self.env['shipcloud.carrier'].search([('name','=','dhl')])
                                if dhl_id:
                                    shipcloud_carrier_id = dhl_id.id
                                    dhl_carrier_services_id = self.env['carrier.services'].search([('name','=','standard')])
                                    if dhl_carrier_services_id:
                                        carrier_services_id = dhl_carrier_services_id.id
                                    dhl_package_type_id = self.env['package.type'].search([('name','=','parcel')])
                                    if dhl_package_type_id:
                                        package_type_id = dhl_package_type_id.id
#                                 else:
#                                     hsi_id = self.env['shipcloud.carrier'].search([('name','=','hsi')])
#                                     if hsi_id:
#                                         shipcloud_carrier_id = hsi_id.id
#                                         hsi_carrier_services_id = self.env['carrier.services'].search([('name','=','standard')])
#                                         if hsi_carrier_services_id:
#                                             carrier_services_id = hsi_carrier_services_id.id
#                                         hsi_package_type_id = self.env['package.type'].search([('name','=','parcel')])
#                                         if hsi_package_type_id:
#                                             package_type_id = hsi_package_type_id.id
                                            
                                        
                                    
                        if partner:
                            country = self.env['res.country'].search([('name','=',response_template['shipping_address'].get('country_name'))])
                            if not partner.street2 == response_template['shipping_address'].get('address1'):
                                partner_shipping = self.env['res.partner'].search([('type','=','delivery'),('street2','=',response_template['shipping_address'].get('address1'))])
                                if not partner_shipping:
                                    
                                    
                                    street_no = ''
                                    street_no_list = re.findall(r'\d+', response_template['shipping_address'].get('address1'))
                                    if street_no_list:
                                        street_no = street_no_list[0]
                                    
                                    street_name = ''
                                    street1 = re.sub(r'\d+', '', response_template['shipping_address'].get('address1'))
                                    if street1:
                                        if response_template['shipping_address'].get('address2'):
                                            street_name = street1 + response_template['shipping_address'].get('address2')
                                        else:
                                            street_name = street1
                                    
                                    
                                    
                                    shipping_vals = {
                                                    'parent_id'     : partner.id,
                                                    'type'          : 'delivery',
                                                    'street2'       : street_name,
                                                    'street'        : street_no,
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
                                        'date_order'            : response_template.get('created_at'),
                                        'shipcloud_carrier_id'  : shipcloud_carrier_id,
                                        'carrier_services_id'   : carrier_services_id,
                                        'package_type_id'       : package_type_id
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
                    
        