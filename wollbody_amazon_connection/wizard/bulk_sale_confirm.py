# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
from openerp import models, api,exceptions, fields, _
from openerp.exceptions import Warning
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError, UserError, except_orm
import logging
_logger = logging.getLogger(__name__)


class BulkSaleConfirm(models.TransientModel):
    _name = "bulk.sale.confirm"
    
    @api.multi
    def action_bulk_confirm(self):
        for bulk in self:
            context = dict(self._context or {})
            if context.get('active_ids'):
                sales = self.env['sale.order'].browse(context.get('active_ids'))
                for sale in sales:
                    if sale.state == 'draft' or sale.state == 'sent':
                        sale.action_confirm()
        
            return True
            
    
        

