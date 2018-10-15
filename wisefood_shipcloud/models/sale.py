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

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    weight                          = fields.Float('Weight',compute='_get_weight')
    length                          = fields.Float('Length',compute='_get_length')
    width                           = fields.Float('Width',compute='_get_width')
    height                          = fields.Float('Height',compute='_get_height')
    
    shipcloud_carrier_id            = fields.Many2one('shipcloud.carrier','Shipcloud Carrier',copy=False)
    carrier_services_id             = fields.Many2one('carrier.services','Shipcloud Service',copy=False)
    package_type_id                 = fields.Many2one('package.type','Shipcloud Package Type',copy=False)
    
    carrier_services_ids            = fields.Many2many('carrier.services',string='Services',related='shipcloud_carrier_id.carrier_services_ids')
    package_type_ids                = fields.Many2many('package.type',string='Package Type',related='shipcloud_carrier_id.package_type_ids')
    shipcloud_shipment_id           = fields.Char('Shipcloud ID',copy=False)
    carrier_tracking_no             = fields.Char('Carrier Tracking No.',copy=False)
    tracking_url                    = fields.Char('Tracking URL',copy=False)
    shipcloud_shipment_price        = fields.Float('Price',copy=False)
    label_url                       = fields.Char('Label URL',copy=False)
    
    name_int                        = fields.Integer('Name Int',compute='_name_int',store=True)
    
    customs_declaration             = fields.Boolean('Customs Declaration')
    contents_type_id                   = fields.Many2one('contents.type','Contents Type')
    contents_explanation_id            = fields.Many2one('contents.explanation','Contents Explanation')
    additional_fees                 = fields.Float('Additional Fees')
    drop_off_location_id            = fields.Many2one('res.country','Drop Off Location')
    invoice_number                  = fields.Char('Invoice Number')
    
    
    
    @api.depends('name')
    @api.multi
    def _name_int(self):
        for sale in self:
            if sale.name:
                try:
                    sale.name_int = int(sale.name)
                except:
                    sale.name_int = 0
    
    @api.multi
    def _get_weight(self):
        for sale in self:
            total_weight = 0
            if sale.order_line:
                for line in sale.order_line:
                    if line.product_id.weight:
                        total_weight += line.product_id.weight * line.product_uom_qty
            sale.weight = total_weight    
    
    @api.multi
    def _get_length(self):
        for sale in self:
            length_list = []
            if sale.order_line:
                for line in sale.order_line:
                    if line.product_id.length:
                        length_list.append(line.product_id.length)
            if length_list:
                sale.length = max(length_list)
    
    @api.multi
    def _get_width(self):
        for sale in self:
            width_list = []
            if sale.order_line:
                for line in sale.order_line:
                    if line.product_id.width:
                        width_list.append(line.product_id.width)
            if width_list:
                sale.width = max(width_list)
    
    @api.multi
    def _get_height(self):
        for sale in self:
            height_list = []
            qty_list = []
            if sale.order_line:
                for line in sale.order_line:
                    if line.product_id.width:
                        height_list.append(line.product_id.height * line.product_uom_qty)
            if height_list:
                sale.height = sum(height_list)
                
#    {'id': 'a72add51b506cf4ab7773257a2a0cee1bbb9a206', 'carrier_tracking_no': 'H1001060000000401031', 
#    'tracking_url': 'https://track.shipcloud.io/de/a72add51b5', 'price': 0.0, 
#    'label_url': 'https://sc-labels.s3.amazonaws.com/shipments/b3149b05/a72add51b5/label/shipping_label_a72add51b5.pdf'}
    @api.multi
    def action_create_shipment(self):
        for sale in self:
            if sale.shipcloud_shipment_id:
                raise UserError(_('Shipment Already Created'))
            
            partner = sale.partner_id
            if not sale.shipcloud_carrier_id:
                raise UserError(_('Please Insert Value in Shipcloud Carrier'))
            if not sale.carrier_services_id:
                raise UserError(_('Please Insert Value in Shipcloud Service'))
            if not sale.package_type_id:
                raise UserError(_('Please Insert Value in Shipcloud Package Type'))
            
            if not partner.first_name:
                raise UserError(_('Please Insert Value in First Name of Customer'))
            if not partner.last_name:
                raise UserError(_('Please Insert Value in Last Name of Customer'))
            if not partner.street:
                raise UserError(_('Please Insert Value in Street of Customer'))
            if not partner.street2:
                raise UserError(_('Please Insert Value in Street2 of Customer'))
            if not partner.city:
                raise UserError(_('Please Insert Value in City of Customer'))
            if not partner.zip:
                raise UserError(_('Please Insert Value in Zip of Customer'))
            if not partner.city:
                raise UserError(_('Please Insert Value in City of Customer'))
            if not partner.country_id:
                raise UserError(_('Please Insert Value in Country of Customer'))
            
            
            ship_cloud = self.env['ship.cloud'].search([], limit=1)
            if ship_cloud:
                if sale.customs_declaration:
                    ship_cloud.action_create_shipment_customs(sale)
                else:
                    ship_cloud.action_create_shipment(sale)
        return True
    
    
    @api.multi 
    def get_file(self):
        sales = self.env['sale.order'].search([])
        pdfs = []
        for sale in sales:
            
            tmp_dir = tempfile.gettempdir()
            r = requests.get(sale.label_url)
            with open(tmp_dir + "/Label"+ str(sale.name)  + ".pdf", "wb") as code:
                code.write(r.content)
            
            pdfs.append(tmp_dir + "/Label"+ str(sale.name)  + ".pdf")
                
                
        merger = PdfFileMerger()

        for pdf in pdfs:
            merger.append(open(pdf, 'rb'))

        with open(tmp_dir +'/new.pdf', 'wb') as fout:
            merger.write(fout)
        
        
        
        
        
        with open(tmp_dir +'/new.pdf', "rb") as code:
            #code.write(r.content)
            #encoded_string=base64.b64encode(image_file.read())
            page_content = code.read()
        
        base64Data = base64.encodestring(page_content)
        
        
        
        attachment = self.env['ir.attachment'].create({
                            'datas': base64Data,
                            'type': 'binary',
                            'res_model': 'sale.order',
                            'res_id': self.id,
                            'db_datas': 'ABC.pdf',
                            'datas_fname': 'ABC.pdf',
                            'name': 'ABC.pdf'
                            })   
        
        self.env.cr.commit()       
                #pdfs.append("/home/ali/Desktop/Label"+ str(inc)  + ".pdf")
                #inc += 1
                
                
        return {
                 'type' : 'ir.actions.act_url',
                 #'url': 'file:///tmp/new.pdf',
                 'url':   '/web/content/%s?download=true' % (attachment.id),
                 'target': 'new',
                 }   

class ContentsExplanation(models.Model):
    _name = 'contents.explanation'
    
    name = fields.Char('Contents Explanation')

class ContentsType(models.Model):
    _name = 'contents.type'
    
    name = fields.Char('Contents Type')
    