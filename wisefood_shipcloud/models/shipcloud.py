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

import logging

_logger = logging.getLogger(__name__)

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
    
    
    @api.multi
    def action_create_shipment_customs(self,sale):
        for cloud in self:
            if sale:
                partner = sale.partner_id
                
                order_date = datetime.strptime(sale.date_order, '%Y-%m-%d %H:%M:%S').date()
                
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
                      "customs_declaration": {
                            "contents_type": sale.contents_type_id.name,
                            "contents_explanation": sale.contents_explanation_id.name,
                            "currency": sale.currency_id.name if sale.currency_id else 'EUR',
                            "additional_fees": sale.additional_fees,
                            "drop_off_location": sale.drop_off_location_id.code,
                            #"posting_date": "2017-10-07",
                            "posting_date": order_date.strftime("%Y-%m-%d"),
                            
                            "invoice_number": sale.invoice_number,
                            "total_value_amount": sale.amount_total,
#                             "items": [{
#                                 "origin_country": "DE",
#                                 "description": "Linkwood 25 years",
#                                 "hs_tariff_number": "501293884",
#                                 "quantity": "1",
#                                 "value_amount": "138.50",
#                                 "net_weight": "0.8"
#                               },
#                               {
#                                 "origin_country": "DE",
#                                 "description": "Caol Ila 18 years",
#                                 "hs_tariff_number": "123384890",
#                                 "quantity": "1",
#                                 "value_amount": "108.50",
#                                 "net_weight": "0.8"
#                               }
#                             ]
                          },
                      "carrier": sale.shipcloud_carrier_id.name,
                      "service": sale.carrier_services_id.name,
                      "reference_number": sale.name,
                      "notification_email": partner.email if partner.email else '',
                      "create_shipping_label": True
                    }
                item = []
                if sale.order_line:
                    for line in sale.order_line:
                        if not line.product_id.description_pickingout:
                            raise UserError(_('Product Description for Delivery Orders is empty of product : %s') %(line.product_id.name))
                        
                        item.append({
                                    "origin_country": line.product_id.origin_country_id.code,
                                    "description": line.product_id.description_pickingout,
                                    "hs_tariff_number": line.product_id.hs_tariff_number,
                                    "quantity": line.product_uom_qty,
                                    "value_amount": line.price_unit,
                                    "net_weight": line.product_id.weight
                            })
                
                if item:
                    shipment['customs_declaration']['items'] = item
                
                _logger.warning('(%s).', shipment)
                json_shipment = json.dumps(shipment)
                resp = requests.post(cloud.api_url +'shipments/',auth=(cloud.api_key, ''), data = json_shipment, headers=headers)
                #print(resp.text)
                shipment_dict = json.loads(resp.text)
                if shipment_dict.get('errors'):
                    raise UserError(_('Shipcloud Server Response \n %s') % (shipment_dict.get('errors')[0]))
                sale.write({'shipcloud_shipment_id':shipment_dict.get('id'),'carrier_tracking_no':shipment_dict.get('carrier_tracking_no'),
                            'tracking_url': shipment_dict.get('tracking_url'),'shipcloud_shipment_price':shipment_dict.get('price'),
                            'label_url':shipment_dict.get('label_url'),
                            'carrier_declaration_document_url':shipment_dict['customs_declaration'].get('carrier_declaration_document_url')})
            
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
    

