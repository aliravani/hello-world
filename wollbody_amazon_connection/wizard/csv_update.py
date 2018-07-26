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
import logging
_logger = logging.getLogger(__name__)

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class CSVUpdate(models.TransientModel):
    _name = "csv.update"
    
    @api.model
    def _get_model_id(self):
        model = self.env['ir.model'].search([('model', '=', 'product.product')])
        return model.id
    
    model_id        = fields.Many2one('ir.model','Model',default=_get_model_id)
    file            = fields.Binary("File")
    type            = fields.Selection([('int','Int No'),('default','Default Code')], string='Type of Import', default='default')
    
    
    @api.multi
    def update(self):
        for record in self:
            tmp_dir = tempfile.gettempdir()
            f=open(tmp_dir+"/csv_orders.csv",'w')
            datafile=record.file
            if datafile:
                csv_data = base64.decodestring(datafile)
            
            f = StringIO(csv_data)
            reader = csv.reader(f, delimiter='\t')
            cm = {}
            for row in reader:
                col_count = 0
                for col in row:
                    cm[col] = col_count
                    col_count = col_count + 1
                break;
            
            prod_pool = self.env['product.product']
            for row in reader:
                #try:
                if record.type == 'int':
                    int_no = row[cm['get_int_no']]
                    prod_exist = prod_pool.search( [('get_int_no','=',int_no)], limit=1)
                    if prod_exist:
                        sorted_x = sorted(cm, key=cm.get)
                        vals = dict(itertools.izip(sorted_x, row))
                        
                        if vals.get('barcode') == '':
                            vals.pop('barcode')
                        try:
                            prod_exist.write(vals)
                            #self.env.cr.commit()
                        except:
                            self.env.cr.rollback()
                            continue
                                
                if record.type == 'default':
                    sku = row[cm['default_code']]
                    prod_exist = prod_pool.search([('default_code','=',sku)])
                    _logger.info(str(prod_exist))
                    #print 'prod_exist prod_exist      ',prod_exist
                    if prod_exist:
                        sorted_x = sorted(cm, key=cm.get)
                        vals = dict(itertools.izip(sorted_x, row))
                        prod_exist.write(vals)
                        continue
        
        return True