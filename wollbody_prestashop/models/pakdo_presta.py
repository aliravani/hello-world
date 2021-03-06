# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp

import base64
import tempfile
import csv
import itertools
import logging
_logger = logging.getLogger(__name__)

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class PakdoPrestaStock(models.Model):
    _name = 'pakdo.presta.stock'
    
    product_id              = fields.Many2one('product.product','Product')
    qty                     = fields.Integer('Quantity')
    gtin                    = fields.Char('GTIN')
    presta_child_id         = fields.Char(related='product_id.presta_child_id',string='Presta Child ID', store=True)
    presta_id               = fields.Char(related='product_id.presta_id',string='Presta ID', store=True)
    presta_stock_id         = fields.Char('Stock ID')


class CSVPakdoPresta(models.TransientModel):
    _name = "csv.pakdo.presta"
    
    file            = fields.Binary("File")
    
    
    @api.multi
    def update(self):
        for record in self:
            tmp_dir = tempfile.gettempdir()
            f=open(tmp_dir+"/pakdo_presta_stock_import.csv",'w')
            datafile=record.file
            if datafile:
                csv_data = base64.decodestring(datafile)
            
            f = StringIO(csv_data)
            reader = csv.reader(f, delimiter=';')
            cm = {}
            for row in reader:
                col_count = 0
                for col in row:
                    cm[col] = col_count
                    col_count = col_count + 1
                break;
            

            product_pool = self.env['product.product']
            pp_stock_pool      = self.env['pakdo.presta.stock']
            for row in reader:
                
                product         = row[0]
                qty             = row[1]
                name            = row[2]
                gtin            = row[3]
                identifier_1    = row[4]
                identifier_2    = row[5]
                
                
                pp_stock = pp_stock_pool.search([('gtin','=',gtin)], limit=1)
                if pp_stock:
                    pp_stock.write({'qty':qty})
                else:
                    product = product_pool.search([('barcode','=',gtin)], limit=1)
                    if product:
                        pp_stock.create({'product_id':product.id, 'gtin':gtin, 'qty':qty})
                        

class PrestaPrice(models.Model):
    _name = 'presta.price'
    
    product_id              = fields.Many2one('product.product','Product')
    price                   = fields.Float('Impact Price')
    price_percent           = fields.Float('Impact Percent (%)')
    default_code            = fields.Char('Internel Reference')
    presta_child_id         = fields.Char(related='product_id.presta_child_id',string='Presta Child ID', store=True)
    presta_id               = fields.Char(related='product_id.presta_id',string='Presta ID', store=True)
    date_from               = fields.Char('Date From')
    date_to                 = fields.Char('Date To')
    presta_specific_price_id = fields.Char('Specific Price ID')
    related_supplier_id     = fields.Many2one('res.partner', related='product_id.related_supplier_id',string='Supplier')
    qty                     = fields.Float('Qty',compute='_get_qty',store=True)
    
    @api.multi
    @api.depends('product_id')
    def _get_qty(self):
        for presta in self:
            if presta.product_id:
                stock = self.env['pakdo.presta.stock'].search([('product_id','=',presta.product_id.id)], limit=1)
                if stock:
                    presta.qty = stock.qty
                        
class CSVPrestaPrice(models.TransientModel):
    _name = "csv.presta.price"
    
    file            = fields.Binary("File")
    
    
    @api.multi
    def update(self):
        for record in self:
            tmp_dir = tempfile.gettempdir()
            f=open(tmp_dir+"/presta_price_import.csv",'w')
            datafile=record.file
            if datafile:
                csv_data = base64.decodestring(datafile)
            
            f = StringIO(csv_data)
            reader = csv.reader(f, delimiter=';')
            cm = {}
            for row in reader:
                col_count = 0
                for col in row:
                    cm[col] = col_count
                    col_count = col_count + 1
                break;
            

            product_pool = self.env['product.product']
            pp_stock_pool      = self.env['presta.price']
            for row in reader:
                
                default_code         = row[0]
                price                = row[1]
                percent              = row[2]
                date_from            = row[3]
                date_to              = row[4]
                
                
#                 date_from = datetime.strptime(date_from,'%d/%m/%y %H:%M')
#                 date_from_final = date_from.strftime("%m/%d/%Y")
#                 
#                 date_to = datetime.strptime(date_to,'%d/%m/%y %H:%M')
#                 date_to_final = date_to.strftime("%m/%d/%Y")
                

                pp_stock = pp_stock_pool.search([('default_code','=',default_code)], limit=1)
                if pp_stock:
                    pp_stock.write({'price':price, 'date_from':date_from, 'date_to':date_to, 'price_percent':percent})
                else:
                    product = product_pool.search([('default_code','=',default_code)], limit=1)
                    if product:
                        pp_stock.create({'product_id':product.id, 'default_code':default_code, 'price':price, 'date_from':date_from, 'date_to':date_to, 'price_percent':percent})
                        
                        
                        
                        
                        
                        