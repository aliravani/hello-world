# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class Invite(models.TransientModel):
    """ Wizard to invite partners (or channels) and make them followers. """
    _inherit = 'mail.wizard.invite'
    _description = 'Invite wizard'

    
    send_mail = fields.Boolean('Send Email', default=False, help="If checked, the partners will receive an email warning they have been added in the document's followers.")
    