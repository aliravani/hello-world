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

class Partner(models.Model):
    _inherit = 'res.partner'
    
    
    first_name          = fields.Char('First Name')
    last_name           = fields.Char('Last Name')
    custom_company_name        = fields.Char('Company Name')
    
    @api.model
    def create(self, vals):
        if vals.get('first_name') and vals.get('last_name'):
            fullname = "%s %s" % (vals.get('first_name'), vals.get('last_name'))        
            vals['name'] = fullname
        
        res = super(Partner, self).create(vals)
        return res
    
    @api.multi
    def write(self, vals):
        res = super(Partner, self).write(vals)
        if vals.get('first_name') or vals.get('last_name'):
            fullname = "%s %s" % (self.first_name, self.last_name)        
            self.write({'name':fullname})
        return res