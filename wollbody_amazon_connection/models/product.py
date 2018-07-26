# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime, timedelta, date
import pytz

import odoo.addons.decimal_precision as dp

class ProductProduct(models.Model):
    _inherit = "product.product"
    
    @api.depends('attribute_value_ids')
    def _get_size(self):
        for product in self:
            for size in product.attribute_value_ids:
                product.update({'get_size' : str(size.name)})
    
    @api.depends('standard_price')
    def _compute_sale_price(self):
        for product in self:
            product.update({'compute_sale_price' : product.standard_price * 2.19 if product.standard_price else 0.0 })
    
    
    
    @api.depends('product_tmpl_id.related_supplier_id','product_tmpl_id.art_name','product_tmpl_id.art_no','product_tmpl_id.color_name','product_tmpl_id.material_id','get_size')
    def _get_auto_product_desc(self):
        for product in self:
            name = ''
            tmpl = product.product_tmpl_id
            if tmpl.related_supplier_id:
                name += tmpl.related_supplier_id.name
            if tmpl.art_name:
                name += ' ' + tmpl.art_name
            if tmpl.art_no:
                name += ' ' + tmpl.art_no
            if tmpl.color_name:
                name += ' ' + tmpl.color_name
            if product.get_size:
                name += ' ' + product.get_size
            if tmpl.material_id:
                name += ' ' + tmpl.material_id.name
            product.update({'get_auto_product_desc' : name })
    
    @api.depends('product_tmpl_id.art_no','product_tmpl_id.color_no','get_size','product_tmpl_id.art_no_original')
    def _get_int_no(self):
        for product in self:
            tmpl = product.product_tmpl_id
            if tmpl.color_no and product.get_size:
                if tmpl.art_no_original:
                    int_no = tmpl.art_no_original + tmpl.color_no + str(product.get_size)
                else:
                    int_no = tmpl.art_no + tmpl.color_no + str(product.get_size)
                product.update({'get_int_no' : int_no })
    
    
    @api.depends('fba_qty','wlbdy_qty','pakdo_qty')
    def _get_total_qty(self):
        for product in self:
            product.update({'total_child_qty' : product.fba_qty + product.wlbdy_qty + product.pakdo_qty})
    
    @api.multi
    def _sales_count_30(self):
        today = datetime.now()
        day_30  = datetime.now() - timedelta(30)
        
        tz_name = 'Europe/Berlin'
        utc             = pytz.timezone('UTC')
        context_tz      = pytz.timezone(tz_name)
        local_timestamp_today = utc.localize(today, is_dst=False)
        local_timestamp_day_30 = utc.localize(day_30, is_dst=False)
        user_datetime_today   = local_timestamp_today.astimezone(context_tz)
        user_datetime_day_30   = local_timestamp_day_30.astimezone(context_tz)
        
        start_date = user_datetime_today.strftime("%m/%d/%Y 00:00:00")
        end_date = user_datetime_day_30.strftime("%m/%d/%Y 23:59:59")
        
        r = {}
        domain = [
            ('state', 'in', ['sale', 'done']),
            ('product_id', 'in', self.ids),
            ('date','<=',start_date),
            ('date','>=',end_date)
        ]
        for group in self.env['sale.report'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id']):
            r[group['product_id'][0]] = group['product_uom_qty']
        for product in self:
            product.sales_count_30 = r.get(product.id, 0)
        return r
    
    @api.multi
    def _sales_count_365(self):
        today = datetime.now()
        day_30  = datetime.now() - timedelta(365)
        
        tz_name = 'Europe/Berlin'
        utc             = pytz.timezone('UTC')
        context_tz      = pytz.timezone(tz_name)
        local_timestamp_today = utc.localize(today, is_dst=False)
        local_timestamp_day_30 = utc.localize(day_30, is_dst=False)
        user_datetime_today   = local_timestamp_today.astimezone(context_tz)
        user_datetime_day_30   = local_timestamp_day_30.astimezone(context_tz)
        
        start_date = user_datetime_today.strftime("%m/%d/%Y 00:00:00")
        end_date = user_datetime_day_30.strftime("%m/%d/%Y 23:59:59")
        
        r = {}
        domain = [
            ('state', 'in', ['sale', 'done']),
            ('product_id', 'in', self.ids),
            ('date','<=',start_date),
            ('date','>=',end_date)
        ]
        for group in self.env['sale.report'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id']):
            r[group['product_id'][0]] = group['product_uom_qty']
        for product in self:
            product.sales_count_365 = r.get(product.id, 0)
        return r
    
    @api.multi
    def _sales_count_365_30(self):
        today = datetime.now()
        day_30  = datetime.now() - timedelta(365)
        day_30_next = day_30 + timedelta(30)
        
        tz_name = 'Europe/Berlin'
        utc             = pytz.timezone('UTC')
        context_tz      = pytz.timezone(tz_name)
        local_timestamp_day_30_next = utc.localize(day_30_next, is_dst=False)
        local_timestamp_day_30 = utc.localize(day_30, is_dst=False)
        user_datetime_day_30_next   = local_timestamp_day_30_next.astimezone(context_tz)
        user_datetime_day_30   = local_timestamp_day_30.astimezone(context_tz)
        
        start_date = user_datetime_day_30_next.strftime("%m/%d/%Y 00:00:00")
        end_date = user_datetime_day_30.strftime("%m/%d/%Y 23:59:59")
        
        r = {}
        domain = [
            ('state', 'in', ['sale', 'done']),
            ('product_id', 'in', self.ids),
            ('date','<=',start_date),
            ('date','>=',end_date)
        ]
        for group in self.env['sale.report'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id']):
            r[group['product_id'][0]] = group['product_uom_qty']
        for product in self:
            product.sales_count_365_30 = r.get(product.id, 0)
        return r
    
    sales_count_30        = fields.Integer(compute='_sales_count_30', string='# Sales 30')
    sales_count_365       = fields.Integer(compute='_sales_count_365', string='# Sales 365')
    sales_count_365_30    = fields.Integer(compute='_sales_count_365_30', string='# Sales 365-30')
    get_size              = fields.Char(string='Size', store=False, readonly=True, compute='_get_size')
    get_int_no            = fields.Char(string='Int Nr', store=True, readonly=True, compute='_get_int_no')
    compute_sale_price    = fields.Float(string='Computed Sale Price', store=False, readonly=True, compute='_compute_sale_price')
    get_auto_product_desc = fields.Char(string='Auto Product Desc', store=False, readonly=True, compute='_get_auto_product_desc')
    
    
    asin                  = fields.Char('ASIN', size=32, help='The ASIN code')
    fnsku                 = fields.Char('FNSKU', size=32, help='The FNSKU')
    
    #my price and DE price same
    amazon_de_price       = fields.Float('Amazon DE Price')
    amazon_my_price       = fields.Float('My Price')
    
    #Amazon get_competitive_pricing_for_sku
    amazon_land_price     = fields.Float('Amazon Landed Price')
    amazon_list_price     = fields.Float('Amazon Listed Price')
    amazon_ship_price     = fields.Float('Amazon Shipping Price')
    amazon_offer_count    = fields.Integer('Offer Listing Count')
    
    #get_lowest_offer_listings_for_sku
    amazon_best_price_1   = fields.Float('Amazon Best Price -1')
    amazon_best_price_2   = fields.Float('Amazon Best Price -2')
    amazon_best_price_3   = fields.Float('Amazon Best Price -3')
    amazon_best_price_4   = fields.Float('Amazon Best Price -4')
    amazon_best_price_5   = fields.Float('Amazon Best Price -5')
    
    lst_price             = fields.Float(
                            'Sale Price', compute='_compute_product_lst_price',
                            digits=dp.get_precision('Product Price'), inverse='_set_product_lst_price',
                            help="The sale price is managed from the product template. Click on the 'Variant Prices' button to set the extra attribute prices.")
    
    sale_price_our        = fields.Float('Sale Price Our') 
    total_child_qty       = fields.Integer(compute='_get_total_qty',string='Total Child Qty',store=True)
    fba_qty               = fields.Integer('FBA Qty', default=0)
    wlbdy_qty             = fields.Integer('WLBDY Qty', default=0)
    pakdo_qty             = fields.Integer('PAKDO Qty', default=0)
    pakdo                 = fields.Boolean('Pakdo')
    push_pakdo            = fields.Boolean('Push To Pakdo')
    
    pakdo_image           = fields.Boolean('Pakdo Image')
    
    amazon_name           = fields.Char('Amazon Name')
    
    def _set_product_lst_price(self):
        for product in self:
            if self._context.get('uom'):
                value = self.env['product.uom'].browse(self._context['uom'])._compute_price(product.lst_price, product.uom_id)
            else:
                value = product.lst_price
            #value -= product.price_extra
            product.write({'sale_price_our': value})
            
    @api.depends('list_price')
    def _compute_product_lst_price(self):
        to_uom = None
        if 'uom' in self._context:
            to_uom = self.env['product.uom'].browse([self._context['uom']])
        for product in self:
            product.lst_price = product.sale_price_our
    
    