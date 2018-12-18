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

class ExportShopifyProduct(models.TransientModel):
    _name = "export.shopify.product"
    
    file            = fields.Binary('Download CSV')
    file_name       = fields.Char('Download File')
    all_product     = fields.Boolean('Export All Products')
    
    @api.multi
    def action_export(self):
        context = self._context
        for export in self:
            delimiter = ','
            buf=cStringIO.StringIO()
            #47
            headers =  ['Handle','Title','Body (HTML)','Vendor','Type','Tags','Published','Option1 Name',
                        'Option1 Value','Option2 Name','Option2 Value','Option3 Name','Option3 Value','Variant SKU','Variant Grams','Variant Inventory Tracker',
                        'Variant Inventory Qty','Variant Inventory Policy','Variant Fulfillment Service','Variant Price','Variant Compare At Price','Variant Requires Shipping','Variant Taxable','Variant Barcode',
                        'Image Src','Image Position','Image Alt Text','Gift Card','SEO Title','SEO Description','Google Shopping / Google Product Category','Google Shopping / Gender',
                        'Google Shopping / Age Group','Google Shopping / MPN','Google Shopping / AdWords Grouping','Google Shopping / AdWords Labels',
                        'Google Shopping / Condition','Google Shopping / Custom Product','Google Shopping / Custom Label 0','Google Shopping / Custom Label 1',
                        'Google Shopping / Custom Label 2','Google Shopping / Custom Label 3','Google Shopping / Custom Label 4','Variant Image','Variant Weight Unit','Variant Tax Code','Cost per item']
            buf.write(delimiter.join(headers) + "\n")
            product_ids = context.get('active_ids')
            
            if export.all_product:
                products = self.env['product.product'].search([('active','=',True)], order='product_tmpl_id')
                
                for product in products:
                    
                    val = [
                            product.name.replace(",", "")+' '+str(product.product_tmpl_id.id),
                            product.product_tmpl_id.name.replace(",", ""),
                            #'Body (HTML)',
                            '',
                            product.related_supplier_id.name if product.related_supplier_id else '',
                            product.categ_id.name,
                            #'Tags',
                            '', 
                            'true',
                            'Size',
                            product.get_size if product.get_size else '1',
                            'Color',
                            product.color_name if product.color_name else 'NULL',
                            #'Option3 Name',
                            '',
                            #'Option3 Value',
                            '',
                            product.default_code if product.default_code else ''  ,
                            #'Variant Grams',
                            '',
                            #'Variant Inventory Tracker',
                            '',
                            #'Variant Inventory Qty',
                            '',
                            #'Variant Inventory Policy',
                            'deny',
                            #'Variant Fulfillment Service',
                            'manual',
                            str(product.compute_sale_price),
                            #'Variant Compare At Price',
                            '',
                            #'Variant Requires Shipping',
                            '',
                            #'Variant Taxable',
                            '',
                            product.barcode if product.barcode else ''  ,
                            #'Image Src',
                            '',
                            #'Image Position',
                            '',
                            #'Image Alt Text',
                            '',
                            #'Gift Card',
                            '',
                            #'SEO Title',
                            '',
                            #'SEO Description',
                            '',
                            #'Google Shopping / Google Product Category',
                            '',
                            #'Google Shopping / Gender',
                            '',
                            #'Google Shopping / Age Group',
                            '',
                            #'Google Shopping / MPN',
                            '',
                            #'Google Shopping / AdWords Grouping',
                            '',
                            #'Google Shopping / AdWords Labels',
                            '',
                            #'Google Shopping / Condition',
                            '',
                            #'Google Shopping / Custom Product',
                            '',
                            #'Google Shopping / Custom Label 0',
                            '',
                            #'Google Shopping / Custom Label 1',
                            '',
                            #'Google Shopping / Custom Label 2',
                            '',
                            #'Google Shopping / Custom Label 3',
                            '',
                            #'Google Shopping / Custom Label 4',
                            '',
                            #'Variant Image',
                            '',
                            #'Variant Weight Unit',
                            '',
                            #'Variant Tax Code',
                            '',
                            str(product.standard_price),
                        ]
                    
                    buf.write((delimiter.join(val)  + u"\n").encode('utf-8'))
            else:
                products = self.env['product.product'].browse(product_ids)
                
                for product in products:
                    val = [
                            product.name.replace(",", "")+' '+str(product.product_tmpl_id.id),
                            product.product_tmpl_id.name.replace(",", ""),
                            #'Body (HTML)',
                            '',
                            product.related_supplier_id.name if product.related_supplier_id else '',
                            product.categ_id.name,
                            #'Tags',
                            '',
                            'true',
                            'Size',
                            product.get_size if product.get_size else '1',
                            'Color',
                            product.color_name if product.color_name else 'NULL',
                            #'Option3 Name',
                            '',
                            #'Option3 Value',
                            '',
                            product.default_code if product.default_code else ''  ,
                            #'Variant Grams',
                            '',
                            #'Variant Inventory Tracker',
                            '',
                            #'Variant Inventory Qty',
                            '',
                            #'Variant Inventory Policy',
                            'deny',
                            #'Variant Fulfillment Service',
                            'manual',
                            str(product.compute_sale_price),
                            #'Variant Compare At Price',
                            '',
                            #'Variant Requires Shipping',
                            '',
                            #'Variant Taxable',
                            '',
                            product.barcode if product.barcode else ''  ,
                            #'Image Src',
                            '',
                            #'Image Position',
                            '',
                            #'Image Alt Text',
                            '',
                            #'Gift Card',
                            '',
                            #'SEO Title',
                            '',
                            #'SEO Description',
                            '',
                            #'Google Shopping / Google Product Category',
                            '',
                            #'Google Shopping / Gender',
                            '',
                            #'Google Shopping / Age Group',
                            '',
                            #'Google Shopping / MPN',
                            '',
                            #'Google Shopping / AdWords Grouping',
                            '',
                            #'Google Shopping / AdWords Labels',
                            '',
                            #'Google Shopping / Condition',
                            '',
                            #'Google Shopping / Custom Product',
                            '',
                            #'Google Shopping / Custom Label 0',
                            '',
                            #'Google Shopping / Custom Label 1',
                            '',
                            #'Google Shopping / Custom Label 2',
                            '',
                            #'Google Shopping / Custom Label 3',
                            '',
                            #'Google Shopping / Custom Label 4',
                            '',
                            #'Variant Image',
                            '',
                            #'Variant Weight Unit',
                            '',
                            #'Variant Tax Code',
                            '',
                            str(product.standard_price),
                        ]
                    
                    buf.write((delimiter.join(val)  + u"\n").encode('utf-8'))
                

              
                #buf.write((delimiter.join(val)  + u"\n").encode('utf-8'))
            file = base64.encodestring(buf.getvalue())
            buf.close()
            file_name =  'export_shopify_product_list_' + time.strftime('%d_%b')
            export.write ({'file_name':file_name + '.csv','file':file})
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'export.shopify.product',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': export.id,
                'views': [(False, 'form')],
                'target': 'new',
            }