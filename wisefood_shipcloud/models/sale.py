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
    
    shipcloud_carrier_id            = fields.Many2one('shipcloud.carrier','Shipcloud Carrier')
    carrier_services_id             = fields.Many2one('carrier.services','Shipcloud Service')
    package_type_id                 = fields.Many2one('package.type','Shipcloud Package Type')
    
    carrier_services_ids            = fields.Many2many('carrier.services',string='Services',related='shipcloud_carrier_id.carrier_services_ids')
    package_type_ids                = fields.Many2many('package.type',string='Package Type',related='shipcloud_carrier_id.package_type_ids')

    
    @api.multi
    def action_create_shipment(self):
        print ('aaaaaaaaa')
        return True