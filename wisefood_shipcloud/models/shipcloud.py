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


headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

class ShipCloud(models.Model):
    _name = 'ship.cloud'
    
    name    = fields.Char('Name')
    api_url     = fields.Char('URL',default='https://api.shipcloud.io/v1/')
    api_key     = fields.Char('API Key')
    
    @api.multi
    def action_import_carrier(self):
        for cloud in self:
            resp = requests.get(cloud.api_url +'carriers/',auth=(cloud.api_key, ''))
            print(resp.text)
            carrier_list = json.loads(resp.text)
            for carrier in carrier_list:
                
                service_list = []
                package_list = []
                if carrier.get('services'):
                    for service in carrier.get('services'):
                        carrier_services = self.env['carrier.services'].search([('name','=',service)])
                        if not carrier_services:
                            carrier_services = self.env['carrier.services'].create({'name':service})
                        if carrier_services:
                            service_list.append(carrier_services.id)
                
                if carrier.get('package_types'):
                    for package in carrier.get('package_types'):
                        package_type = self.env['package.type'].search([('name','=',package)])
                        if not package_type:
                            package_type = self.env['package.type'].create({'name':package})
                        if package_type:
                            package_list.append(package_type.id)
                         
                shipcloud_carriers = self.env['shipcloud.carrier'].search([('name','=',carrier.get('name'))])
                if not shipcloud_carriers:
                    shipcloud_carriers = self.env['shipcloud.carrier'].create({'name':carrier.get('name'), 'carrier_name':carrier.get('display_name'),
                                                                               'carrier_services_ids':[(6,0,service_list)], 'package_type_ids': [(6,0,package_list)]})
                
                if shipcloud_carriers:
                    print ('wwiteeeeeeeeeeeeeeeeee')
                    shipcloud_carriers.write({'name':carrier.get('name'), 'carrier_name':carrier.get('display_name'),
                                              'carrier_services_ids':[(6,0,service_list)], 'package_type_ids': [(6,0,package_list)]})

    @api.multi
    def action_create_shipment(self,sale):
        for cloud in self:
            if sale:
                partner = sale.partner_id
                shipment={
        
                      "to": {
                          "company": partner.custom_company_name if partner.custom_company_name else '',
                          "first_name": partner.first_name,
                          "last_name": partner.last_name,
                          "street": partner.street2,
                          "street_no": partner.street,
                          "city": partner.city,
                          "zip_code": partner.zip,
                          "country": partner.country_id.code
                      },
                      "package": {
                          "weight": sale.weight,
                          "length": sale.length,
                          "width": sale.width,
                          "height": sale.height,
                          "type": sale.package_type_id.name
                      },
                      "carrier": sale.shipcloud_carrier_id.name,
                      "service": sale.carrier_services_id.name,
                      "reference_number": sale.name,
                      "notification_email": partner.email if partner.email else '',
                      "create_shipping_label": True
                    }
                json_shipment = json.dumps(shipment)
                resp = requests.post(cloud.api_url +'shipments/',auth=(cloud.api_key, ''), data = json_shipment, headers=headers)
                print(resp.text)
                shipment_dict = json.loads(resp.text)
                if shipment_dict.get('errors'):
                    raise UserError(_('Shipcloud Server Response \n %s') % (shipment_dict.get('errors')[0]))
                sale.write({'shipcloud_shipment_id':shipment_dict.get('id'),'carrier_tracking_no':shipment_dict.get('carrier_tracking_no'),
                            'tracking_url': shipment_dict.get('tracking_url'),'shipcloud_shipment_price':shipment_dict.get('price'),
                            'label_url':shipment_dict.get('label_url')})
            
        return True
    
    
class ShipCloudCarrier(models.Model):
    _name = 'shipcloud.carrier'
    
    name            = fields.Char('Name')
    carrier_name    = fields.Char('Display Name')
    carrier_services_ids = fields.Many2many('carrier.services',string='Services')
    package_type_ids = fields.Many2many('package.type',string='Package Type')


class CarrierServices(models.Model):
    _name = 'carrier.services'
    
    name            = fields.Char('Name')

class PackageType(models.Model):
    _name = 'package.type'
    
    name            = fields.Char('Name')
    

