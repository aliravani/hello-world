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

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class CSVNote(models.TransientModel):
    _name = "csv.note"
    
    @api.model
    def _get_model_id(self):
        model = self.env['ir.model'].search([('model', '=', 'mail.message')])
        return model.id
    
    model_id        = fields.Many2one('ir.model','Model',default=_get_model_id)
    path            = fields.Char("Path")
    
    
    
    @api.multi
    def update(self):
        for record in self:
            tmp_dir = tempfile.gettempdir()
            
            
            #path = "/tmp/server_mail_message_tab.csv"
            #path = "/home/ali/Desktop/server_mail_message_tab.csv"
            with open(record.path, 'rb') as f:
            
                reader = csv.reader(f, delimiter='\t')
                cm = {}
                for row in reader:
                    col_count = 0
                    for col in row:
                        cm[col] = col_count
                        col_count = col_count + 1
                    break;
                
                message = self.env['mail.message']
                sales   = self.env['sale.order'] 
                for row in reader:
                    record_name = row[cm['record_name']]
                    sale_exist = sales.search( [('name','=',record_name)], limit=1)
                    if sale_exist:
                        print 'sale_exist sale_exist         ',sale_exist
                        sorted_x = sorted(cm, key=cm.get)
                        vals = dict(itertools.izip(sorted_x, row))
                        vals.update({'author_id' : self.env.uid, 'res_id': sale_exist.id, 'date': sale_exist.date_order})
                        if vals.get('body'):
                            message.create(vals)
                            self.env.cr.commit()
                                
                
        
        return True