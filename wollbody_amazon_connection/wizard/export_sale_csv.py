from openerp import models, api,exceptions, fields, _
from openerp.exceptions import Warning
from openerp.tools import frozendict
import time
from openerp.exceptions import UserError, RedirectWarning, ValidationError
from datetime import date, timedelta, datetime

from psycopg2 import OperationalError

import base64
import tempfile
import csv
import itertools
import cStringIO
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class ExportSaleCSV(models.TransientModel):
    _name = "export.sale.csv"
    
    file            = fields.Binary('Download CSV')
    file_name       = fields.Char('Download File')
    sale_csv_line   = fields.One2many('sale.csv.line','csv_id',string='Lines')
    
    @api.multi
    def action_export(self):
        for export in self:
            
            unlink_csv_line = self.env['sale.csv.line'].search([('csv_id','=',export.id)])
            if unlink_csv_line:
                unlink_csv_line.unlink()
            
            today = datetime.now()
            day_30   = datetime.now() - timedelta(30)
            day_90   = datetime.now() - timedelta(90)
            day_365  = datetime.now() - timedelta(365)
            
            start_date = today.strftime("%Y-%m-%d 00:00:00")
            day_30 = day_30.strftime("%Y-%m-%d 23:59:59")
            day_90 = day_90.strftime("%Y-%m-%d 23:59:59")
            day_365 = day_365.strftime("%Y-%m-%d 23:59:59")
            
            sale_lines_30 = self.env['sale.order.line'].search([('order_id.date_order','>=',day_30),('order_id.date_order','<=',start_date),('order_id.state','in',['sale','done'])])
            sale_lines_90 = self.env['sale.order.line'].search([('order_id.date_order','>=',day_90),('order_id.date_order','<=',start_date),('order_id.state','in',['sale','done'])])
            sale_lines_365 = self.env['sale.order.line'].search([('order_id.date_order','>=',day_365),('order_id.date_order','<=',start_date),('order_id.state','in',['sale','done'])])
            
            for line in sale_lines_30:
                
                csv_line = self.env['sale.csv.line'].search([('product_id','=',line.product_id.id),('csv_id','=',export.id)], limit=1)
                if csv_line:
                    csv_line.write({'days_30': csv_line.days_30 + line.product_uom_qty})
                else:
                    csv_line = self.env['sale.csv.line'].create({'product_id':line.product_id.id,'days_30': csv_line.days_30 + line.product_uom_qty, 
                                                                 'csv_id':export.id, 'sale_pirce': line.product_id.lst_price, 'qty': line.product_id.pakdo_qty,
                                                                 'barcode': line.product_id.barcode})
                    
            
            for line in sale_lines_90:
                
                csv_line = self.env['sale.csv.line'].search([('product_id','=',line.product_id.id),('csv_id','=',export.id)], limit=1)
                if csv_line:
                    csv_line.write({'days_90': csv_line.days_90 + line.product_uom_qty})
                else:
                    csv_line = self.env['sale.csv.line'].create({'product_id':line.product_id.id,'days_90': csv_line.days_90 + line.product_uom_qty, 
                                                                 'csv_id':export.id, 'sale_pirce': line.product_id.lst_price, 'qty': line.product_id.pakdo_qty,
                                                                 'barcode': line.product_id.barcode})
                    
            
            for line in sale_lines_365:
                
                csv_line = self.env['sale.csv.line'].search([('product_id','=',line.product_id.id),('csv_id','=',export.id)], limit=1)
                if csv_line:
                    csv_line.write({'days_365': csv_line.days_365 + line.product_uom_qty})
                else:
                    csv_line = self.env['sale.csv.line'].create({'product_id':line.product_id.id,'days_365': csv_line.days_365 + line.product_uom_qty, 
                                                                 'csv_id':export.id, 'sale_pirce': line.product_id.lst_price, 'qty': line.product_id.pakdo_qty,
                                                                 'barcode': line.product_id.barcode})
            

            delimiter = '\t'
            buf=cStringIO.StringIO()
            headers = ['EAN','sales last 30 days','sales last 90 days','sales last 365 days','sale price','stock_qty']
            buf.write(delimiter.join(headers) + "\n")
             
            for line in export.sale_csv_line:
                val = [
                        line.barcode if line.barcode else '',
                        str(int(line.days_30)) if line.days_30 else '',
                        str(int(line.days_90)) if line.days_90 else '',
                        str(int(line.days_365)) if line.days_365 else '',
                        str("%0.2f" % (line.sale_pirce)) if line.sale_pirce else '',
                        str(int(line.qty)) if line.qty else '',
                    ]
             
                buf.write((delimiter.join(val)  + u"\n").encode('utf-8'))
            file = base64.encodestring(buf.getvalue())
            buf.close()
            file_name =  'export_sale_product_list_' + time.strftime('%d_%b')
            export.write ({'file_name':file_name + '.csv','file':file})
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'export.sale.csv',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': export.id,
                'views': [(False, 'form')],
                'target': 'new',
            }

class SaleCSVLine(models.TransientModel):
    _name = 'sale.csv.line'
    
    product_id      = fields.Many2one('product.product','Product')
    barcode         = fields.Char('Barcode')
    days_30         = fields.Float('Last 30 Days')
    days_90         = fields.Float('Last 90 Days')
    days_365        = fields.Float('Last 365 Days')
    sale_pirce      = fields.Float('Sale Price')
    qty             = fields.Float('Qty')
    csv_id          = fields.Many2one('export.sale.csv','CSV')