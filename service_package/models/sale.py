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
    _inherit = "sale.order"
    
    combo_ids       = fields.Many2many('product.combo', 'product_combo_order_rel', 'combo_id', 'order_id', string='Services Include', copy=False)
    
    @api.multi
    def get_combo(self):
        for sale in self:
            combo_list = []
            for line in sale.order_line:
                if line.product_id.product_tmpl_id.combo_product_id:
                    for combo in line.product_id.product_tmpl_id.combo_product_id:
                        if combo.product_template_id2.combo_product_id:
                            for sub_combo in combo.product_template_id2.combo_product_id:
                                combo_list.append(sub_combo.id)
                        else:
                            combo_list.append(combo.id)
            print 'combo_list    ',combo_list
            sale.write({'combo_ids': [(6,0,combo_list)]})
    
    
                

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        result = {'domain': domain}

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False
                return result

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(self._get_display_price(product), product.taxes_id, self.tax_id)
        self.update(vals)
        
#         if self.product_id.combo_ids:
#             print 'self.product_id.combo_ids    ',self.product_id.product_tmpl_id.combo_ids.ids
#             combo_list = self.product_id.product_tmpl_id.combo_ids.ids
#             print 'order_idorder_idorder_id  ',self.order_id
            #self.order_id.write({'combo_ids': [(6,0,combo_list)] })
        return result
    
    
    @api.multi
    def name_get(self):
        res = []
        for line in self:
            name = line.product_id.name 
            if line.product_id.default_code:
                name = name + '[' + line.product_id.default_code + ']' + ' Allow combo:' + str(line.product_id.allow_combo)   
            res.append((line.id, name))
        return res
    