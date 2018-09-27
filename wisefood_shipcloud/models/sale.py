# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid

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

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    weight                          = fields.Float('Weight',copy=False)
    length                          = fields.Float('Length',copy=False)
    width                           = fields.Float('Width',copy=False)
    height                          = fields.Float('Height',copy=False)
    
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
                ship_cloud.action_create_shipment(sale)
                
        return True