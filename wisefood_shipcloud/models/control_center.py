# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid
import base64
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

from PyPDF2 import PdfFileMerger

import os
import tempfile

class ControlCenter(models.Model):
    _name = 'control.center'
    
    name             = fields.Char('Name')
    sale_start       = fields.Many2one('sale.order','SO Start')
    sale_end         = fields.Many2one('sale.order','SO End')
    
    @api.multi
    def action_print_all_labels(self):
        
        sales = self.env['sale.order'].search([('id','>=',self.sale_start.id),('id','<=',self.sale_end.id),('label_url','!=',False)])
        print ('sales sales sales          ',sales)
        pdfs = []
        for sale in sales:
            tmp_dir = tempfile.gettempdir()
            r = requests.get(sale.label_url)
            with open(tmp_dir + "/Label"+ str(sale.name)  + ".pdf", "wb") as code:
                code.write(r.content)
            
            pdfs.append(tmp_dir + "/Label"+ str(sale.name)  + ".pdf")
                
                
        merger = PdfFileMerger()
        if pdfs:
            for pdf in pdfs:
                merger.append(open(pdf, 'rb'))
    
            with open(tmp_dir +'/new.pdf', 'wb') as fout:
                merger.write(fout)
            
            with open(tmp_dir +'/new.pdf', "rb") as code:
                #code.write(r.content)
                #encoded_string=base64.b64encode(image_file.read())
                page_content = code.read()
            
            base64Data = base64.encodestring(page_content)
            
            unlink_attachs = self.env['ir.attachment'].search([('res_id','=',self.id)])
            if unlink_attachs:
                unlink_attachs.unlink()
            
            
            attachment = self.env['ir.attachment'].create({
                                'datas': base64Data,
                                'type': 'binary',
                                'res_model': 'control.center',
                                'res_id': self.id,
                                'db_datas': 'All_labels.pdf',
                                'datas_fname': 'All_labels.pdf',
                                'name': 'All_labels.pdf'
                                })   
            
            self.env.cr.commit()       
                    #pdfs.append("/home/ali/Desktop/Label"+ str(inc)  + ".pdf")
                    #inc += 1
                    
                    
            return {
                     'type' : 'ir.actions.act_url',
                     'url':   '/web/content/%s?download=true' % (attachment.id),
                     'target': 'new',
                     }   
        
        