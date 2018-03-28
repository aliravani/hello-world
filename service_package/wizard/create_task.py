# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
from openerp import models, api,exceptions, fields, _
from openerp.exceptions import Warning
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError, UserError, except_orm
import logging
_logger = logging.getLogger(__name__)

class CreateTask(models.TransientModel):
    _name = "create.task"
    
    sale_id             = fields.Many2one('sale.order','Sale order')
    combo_ids           = fields.Many2many('product.combo', 'product_combo_create_task_rel', 'combo_id', 'create_task_id', string='Services Include', copy=False)
    
    
    @api.model
    def default_get(self, fields):
        resp = super(CreateTask, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        sale = self.env['sale.order'].browse(context.get('active_id'))
        resp['combo_ids']= [(6,0,sale.combo_ids.ids)]
        resp['sale_id'] = sale.id
        
        return resp
    
    @api.multi
    def referesh_list(self):
        for service in self:
            service.write({'combo_ids': [(6,0, service.sale_id.combo_ids.ids)]})
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'create.task',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': service.id,
                'views': [(False, 'form')],
                'target': 'new',
            }
    
    @api.multi
    def create_task(self):
        for service in self:
            if service.combo_ids:
                project_pool = self.env['project.project']
                task_pool    = self.env['project.task']
                task_type_pool = self.env['project.task.type']
                product_exist = []
                allow_dict = {}
                for combo in service.sale_id.combo_ids:
                    if not combo.product_template_id.id in allow_dict:
                        allow_dict.update({combo.product_template_id.id: combo.product_template_id.allow_combo})
                
                for combo2 in service.combo_ids:
                    if combo2.product_template_id.allow_combo > 0:
                        product_exist.append(combo2.product_template_id.id)
                
                
                last_check = []
                last_check = 0
                for allow_d in allow_dict:
                    count = product_exist.count(allow_d)
                    product = self.env['product.template'].search([('id','=',allow_d)])
                    if count > allow_dict[allow_d]:
                        #more
                        raise UserError(_('You have select product :  %s which is allow for only %s and you have added more.' ) % (product.name, product.allow_combo))
                    elif count < allow_dict[allow_d]:
                        #less
                        raise UserError(_('You have select product :  %s which is allow for  %s  and you have added less please click on refresh button to generate all list.') % (product.name, product.allow_combo))
                    else:
                        #ok
                        pass
                
                
                for combo_task in service.combo_ids:
                    project = project_pool.search([('partner_id','=',service.sale_id.partner_id.id)])
                    
                    if not project:
                        name = service.sale_id.partner_id.name 
                        if service.sale_id.partner_id.mobile:
                            name += '-' + service.sale_id.partner_id.mobile
                            
                        project_vals = {
                                    'name'              : name,
                                    'partner_id'        : service.sale_id.partner_id.id,
                                    'user_id'           : service.sale_id.user_id.id,
                                    'privacy_visibility': 'portal',
                                    'use_tasks'         : True
                            }
                        project = project_pool.create(project_vals)
                        
                    task_type = task_type_pool.search([('name','ilike','Request')])
                    
                        
                    if not task_type:
                        task_type.create({'name': 'Request', 'sequence': 1})
                        
                    if project:
                        task = task_pool.search([('sale_id','=',service.sale_id.id),('combo_id','=',combo_task.id)])
                        
                        if task:
                            raise UserError(_('Task is already create for product :  %s ' ) % (combo_task.product_template_id2.name))
                        
                        if not task:
                            task_vals = {
                                        'name'                  : combo_task.product_template_id2.name,
                                        'project_id'            : project.id,
                                        'partner_id'            : project.partner_id.id,
                                        'sale_id'               : service.sale_id.id,
                                        'user_id'               : service.sale_id.user_id.id,
                                        'product_template_id'   : combo_task.product_template_id2.id,
                                        'combo_id'              : combo_task.id,
                                        
                                }
                            
                            if task_type:
                                task_vals.update({'stage_id' : task_type.id})
                            task = task_pool.create(task_vals)
                        
                        
                    
                    
        
        return True