# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import datetime
import hashlib
import pytz
import threading

from email.utils import formataddr

import requests
from lxml import etree
from werkzeug import urls

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.modules import get_module_resource
from odoo.osv.expression import get_unaccent_wrapper
from odoo.exceptions import UserError, ValidationError


class Partner(models.Model):
    _inherit = "res.partner"
    
    birthdate           = fields.Date('Birthdate')
    age_year            = fields.Float('Age(In Years)')
    doctor              = fields.Boolean('Is Doctor')
    easy_checkup_count  = fields.Integer(compute='_compute_easy_checkup_count', string='# of Easy Checkup')
    easy_checkup_ids    = fields.One2many('easy.checkup', 'partner_id', 'Easy Checkup')
    gstin               = fields.Char('GSTIN')
    
    def _compute_easy_checkup_count(self):
        easy_data = self.env['easy.checkup'].read_group(domain=[('partner_id', 'child_of', self.ids)],
                                                      fields=['partner_id'], groupby=['partner_id'])
        # read to keep the child/parent relation while aggregating the read_group result in the loop
        partner_child_ids = self.read(['child_ids'])
        mapped_data = dict([(m['partner_id'][0], m['partner_id_count']) for m in easy_data])
        for partner in self:
            # let's obtain the partner id and all its child ids from the read up there
            item = next(p for p in partner_child_ids if p['id'] == partner.id)
            partner_ids = [partner.id] + item.get('child_ids')
            # then we can sum for all the partner's child
            partner.easy_checkup_count = sum(mapped_data.get(child, 0) for child in partner_ids)