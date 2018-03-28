# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

class Task(models.Model):
    _inherit = "project.task"
    
    sale_id                  = fields.Many2one('sale.order','Sale Order')
    product_template_id      = fields.Many2one('product.template','Service Product')
    combo_id                 = fields.Many2one('product.combo','Combo')
    
    
    