# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class BulkConfirmOrder(models.TransientModel):
    _name = "bulk.confirm.order"
    
    @api.multi
    def action_confirm(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        sales = []
        for sale in sale_orders:
            if sale.state == 'draft':
                sale.action_confirm()
                sale.action_create_shipment()
                self.env.cr.commit()
                sales.append(sale)
                
                
        if sales:
            pdfs = []
            for sale in sales:
                if sale.label_url:
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
                                    'res_model': 'bulk.confirm.order',
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
        