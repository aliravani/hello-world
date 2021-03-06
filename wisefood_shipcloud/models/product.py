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


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    length      = fields.Float('Length')
    width       = fields.Float('Width')
    height      = fields.Float('Height')
    origin_country_id = fields.Many2one('res.country','Origin Country')
    hs_tariff_number  = fields.Char('HS Tariff Number')
    