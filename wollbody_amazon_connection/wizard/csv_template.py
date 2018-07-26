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

class ExportCSVTemplate(models.TransientModel):
    _name = "export.csv.template"
    
    template_id   = fields.Many2one('csv.template','Template')  
    file          = fields.Binary('Exported File')
    file_name     = fields.Char('File Name')
    all           = fields.Boolean('All', default=True)
    
    
    
    @api.multi
    def open_template(self):
         context = dict(self._context or {})
         return {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'csv.template',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': context,
        }
    
    @api.multi
    def export_csv(self):
        buf=StringIO()
        context = dict(self._context or {})
        sobj = self
        delimiter = '\t'
        headers = []   
        fields  = []
        vals = []     
        for fld in sobj.template_id.column_ids:
            fields.append(fld.field_name)
            if fld.field_id:
                headers.append(fld.field_id)
            elif fld.static_value:
                headers.append(fld.static_value)
            else:
                headers.append(False)
            vals.append( '"' + (fld.field_name and fld.field_name or '') + '"' )


        if sobj.template_id.delimiter:
            delimiter = sobj.template_id.delimiter
        if sobj.template_id.amazon_template:
            buf.write(sobj.template_id.amazon_desc.encode('utf-8')   + "\n")
            vals_amazon=[]
            for fld in sobj.template_id.column_ids:
                vals_amazon.append( '"' + fld.amazon_1 + '"' )
            buf.write((delimiter.join(vals_amazon)).encode('utf-8')   + "\n")

            vals_amazon=[]
            for fld in sobj.template_id.column_ids:
                vals_amazon.append( '"' + fld.amazon_2 + '"' )
            buf.write(delimiter.join(vals_amazon)   + "\n")
        else:
            buf.write(delimiter.join(vals)   + "\n")

        prod_pool = self.env['product.product']
        if sobj.all:
            active_ids = prod_pool.search([])
            active_ids = active_ids.ids
        else:
            active_ids = context.get('active_ids')
        
        for prod in prod_pool.browse(active_ids):
            vals = []
            for line in fields:
                if not fld:
                    vals.append('')
                
                line_parts = line.split(':')
                fld = line_parts[0]
                if len(line_parts)>1:
                    lang = line_parts[1]
                    
                prod_lang = prod_pool.browse(prod.id)
                value = eval('prod_lang.'+fld)
                vals.append( '"' + (value and unicode(value) or '') + '"' )
                
            buf.write((delimiter.join(vals)  + u"\n").encode('utf-8'))    

        file = base64.encodestring(buf.getvalue())
        buf.close()
        file_name = 'List_' + sobj.template_id.name + "_" + time.strftime('%d_%b_%H_%M_%p')
        self.write ({'file_name': file_name + '.csv', 'file':file})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'export.csv.template',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': sobj.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
        

class CSVTemplate(models.Model):
    _name       = "csv.template"
    
    name                  = fields.Char("Name", size=128)
    column_ids            = fields.One2many('csv.template.column','template_id','Column')
    amazon_template       = fields.Boolean('Amazon Template')
    amazon_desc           = fields.Char('Amazon Description')
    delimiter             = fields.Char('Delimiter')
    


class CSVTemplateColumn(models.Model):
    _name    = "csv.template.column"
    _order   = 'sequence'
    
    sequence       = fields.Integer('Sequence')
    template_id    = fields.Many2one('csv.template','Template')
    field_id       = fields.Many2one('ir.model.fields','Field', domain=['|',('model_id','=','product.product'),('model_id','=','product.template'),('ttype','not in',['one2many','many2many'])])
    field_name     = fields.Char('name', size=128)
    field_desc     = fields.Char(related='field_id.field_description', string="Field Label", readonly=True)
    static_value   = fields.Char('Static Value', size=64)
                  
    @api.multi
    @api.onchange('field_id') 
    def onchange_field_id(self):
        res = {'value':{}}
        if self.field_id:
            res = {'value': {
                      'field_name'  : self.field_id.name,
                      'field_desc' : self.field_id.field_description 
                   }}
        return res