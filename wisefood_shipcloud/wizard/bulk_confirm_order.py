# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class BulkConfirmOrder(models.TransientModel):
    _name = "bulk.confirm.order"
    
    @api.multi
    def action_confirm(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        for sale in sale_orders:
            if sale.state == 'draft':
                sale.action_confirm()
        return True