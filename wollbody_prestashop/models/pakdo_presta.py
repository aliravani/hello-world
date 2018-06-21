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
                        
                    
                    
                    
                