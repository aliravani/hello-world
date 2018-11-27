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
            resp = wcapi.get("products/3668")
            if resp.status_code == 200:
                pass
            else:
                resp.headers['content-type']
                resp= resp.json()
                raise UserError(_('%s') % (resp.get('message')))
            resp.headers['content-type']
            products = resp.json()
            print ('>>>>>>>>>   ',products)
            print (aaa)
            
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
    
    @api.multi
    def action_import_product_custom(self, product_id=False):
        for woo in self:
            wcapi = API(
            url=woo.api_url,
            consumer_key=woo.consumer_key,
            consumer_secret=woo.consumer_secret,
            wp_api=True,
            version="wc/v1"
            )
            resp = wcapi.get("products/" + str(product_id))
            if resp.status_code == 200:
                pass
            else:
                resp.headers['content-type']
                resp= resp.json()
                raise UserError(_('%s') % (resp.get('message')))
            resp.headers['content-type']
            product = resp.json()
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
                    
                
                
    @api.multi
    def action_import_orders(self):
        for woo in self:
            wcapi = API(
            url=woo.api_url,
            consumer_key=woo.consumer_key,
            consumer_secret=woo.consumer_secret,
            wp_api=True,
            version="wc/v1"
            )
            resp = wcapi.get("orders")
            
            if resp.status_code == 200:
                pass
            else:
                resp.headers['content-type']
                resp= resp.json()
                raise UserError(_('%s') % (resp.get('message')))
            resp.headers['content-type']
            orders = resp.json()
            product_uom = self.env['product.uom.categ'].search([('name','=','Unit')])
            for order in orders:
                shipcloud_carrier_id = False
                carrier_services_id = False
                package_type_id = False
                dhl_id = self.env['shipcloud.carrier'].search([('name','=','dhl')])
                if dhl_id:
                    shipcloud_carrier_id = dhl_id.id
                    dhl_carrier_services_id = self.env['carrier.services'].search([('name','=','standard')])
                    if dhl_carrier_services_id:
                        carrier_services_id = dhl_carrier_services_id.id
                    dhl_package_type_id = self.env['package.type'].search([('name','=','parcel')])
                    if dhl_package_type_id:
                        package_type_id = dhl_package_type_id.id
                        
                        
                sale_order = self.env['sale.order'].search([('name','=',order.get('number')),('woo_id','=',order.get('id'))])
                print ('nnnnnnnnnnn      ',order.get('number'))
                print ('iiiiiidddddddddddddddd     ',order.get('id'))
                print ('sale_order sale_order         ',sale_order)
                if not sale_order:
                    print ('nottttttttttttttttttttttttt')
                    partner_shipping = False
                    partner = False
                    
                    customer_resp = order.get('billing')
                        
                    country = self.env['res.country'].search([('code','=',customer_resp.get('country'))])
                    partner_vals = {
                                        'first_name'    : customer_resp.get('first_name'),
                                        'last_name'     : customer_resp.get('last_name') if customer_resp.get('last_name') else '-',
                                        'name'          : customer_resp.get('first_name') + ' ' + customer_resp.get('last_name') if customer_resp.get('last_name') else False,
                                        'email'         : customer_resp.get('email'),
                                        'custom_company_name' : customer_resp.get('company'),
                                        'street2'       : customer_resp.get('address_1'),
                                        'street'        : customer_resp.get('address_2'),
                                        'city'          : customer_resp.get('city'),
                                        'zip'           : customer_resp.get('postcode'),
                                        'phone'         : customer_resp.get('phone'),
                                        'country_id'    : country.id if country else False,
                                        'customer'      : True,
                                        'woo_id'        : order.get('customer_id'),
                        
                        }
                    
                    
                    partner = self.env['res.partner'].search([('email','=',customer_resp.get('email'))])
                    if partner:
                        partner.write(partner_vals)
                    if not partner:
                        partner = self.env['res.partner'].create(partner_vals)
                        
                        
                        
                    if partner:
                        customer_ship_resp = order.get('shipping')
                        country = self.env['res.country'].search([('code','=',customer_ship_resp.get('country'))])
                        
                        if not partner.street == customer_ship_resp.get('address_1'):
                            partner_shipping = self.env['res.partner'].search([('type','=','delivery'),('street','=',customer_ship_resp.get('address1'))])
                            if not partner_shipping:
                                shipping_vals = {
                                                'parent_id'     : partner.id,
                                                'type'          : 'delivery',
                                                'street'        : customer_ship_resp.get('address_1'),
                                                'city'          : customer_ship_resp.get('city'),
                                                'zip'           : customer_ship_resp.get('postcode'),
                                                'phone'         : customer_ship_resp.get('phone'),
                                                'first_name'    : customer_ship_resp.get('first_name'),
                                                'last_name'     : customer_ship_resp.get('last_name') if customer_resp.get('last_name') else '-',
                                                'name'          : customer_ship_resp.get('first_name') + ' ' + customer_ship_resp.get('last_name') if customer_ship_resp.get('last_name') else False, 
                                                'country_id'    : country.id if country else False,
                                                'custom_company_name' : customer_ship_resp.get('company'),
                                    }
                                partner_shipping = self.env['res.partner'].create(shipping_vals)
                    
                    
                    sale_order = self.env['sale.order'].create({
                                        'woo_id'                : order.get('id'),
                                        'partner_id'            : partner.id,
                                        'partner_shipping_id'   : partner_shipping.id if partner_shipping else partner.id,
                                        'partner_invoice_id'    : partner.id,
                                        'name'                  : order.get('number'),
                                        'date_order'            : order.get('date_created'),
                                        'woo_total'             : order.get('total'),
                                        
                                        'shipcloud_carrier_id'  : shipcloud_carrier_id,
                                        'carrier_services_id'   : carrier_services_id,
                                        'package_type_id'       : package_type_id
                            })
                    print ('sale_order sale_order     ',sale_order)
                    if sale_order:
                        for line in order.get('line_items'):
                            if line.get('product_id'):
                                product = self.env['product.product'].search([('woo_id','=',line.get('product_id'))])
                                if not product:
                                    self.action_import_product_custom(line.get('product_id'))
                                    product = self.env['product.product'].search([('woo_id','=',line.get('product_id'))])
                                    
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
    
    woo_id      = fields.Char(string='Woo ID')

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    woo_id      = fields.Char(string='Woo ID')
    woo_total   = fields.Float('WOO Total Amount')

class Partner(models.Model):
    _inherit = 'res.partner'
    
    woo_id      = fields.Char(string='Woo ID')
                    
        