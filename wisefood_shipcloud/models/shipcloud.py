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
    

