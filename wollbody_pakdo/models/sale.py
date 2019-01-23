# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import psycopg2

import odoo.addons.decimal_precision as dp

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError, except_orm
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    sale_order_number_2 = fields.Char('SO Number 2')