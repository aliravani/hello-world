# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang

import odoo.addons.decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    is_presta                   = fields.Boolean('Is Prestashop')
    presta_id                   = fields.Char('Presta Order ID')
    presta_order_total          = fields.Float('Order Total')
    presta_date_time            = fields.Datetime('Date Time')
    presta_shop                 = fields.Selection([('1','DE'),('2','EN')], string='Presta Shop')
    presta_order_state          = fields.Many2one('prestashop.order.state','Presta Order status')
    tracking_code_push          = fields.Boolean('Tracking code push')
    presta_reference            = fields.Char('Reference')
    
    @api.multi
    def presta_push_trackingcode(self):
        presta = self.env['prestashop.config'].search([], limit=1)
        if presta:
            sale = self
            print 'saleeee  ',sale
            if sale.pakdo_tracking_code:
                presta.push_trackingcode(sale)
            else:
                raise UserError(_('Pakdo tracking code is empty.'))
        return True