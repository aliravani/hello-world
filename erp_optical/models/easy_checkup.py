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
from datetime import datetime, timedelta


class EasyCheckup(models.Model):
    _name = "easy.checkup"
    
    name                    = fields.Char('Name',copy=False,default=lambda self: _('New'))
    partner_id              = fields.Many2one('res.partner','Customer')
    street                  = fields.Char('street')
    street2                 = fields.Char('Street2')
    zip                     = fields.Char('Zip')
    city                    = fields.Char('City')
    state_id                = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    country_id              = fields.Many2one('res.country', string='Country', ondelete='restrict')
    email                   = fields.Char('Email')
    gstin                   = fields.Char('GSTIN')
    category_id             = fields.Many2many('res.partner.category', column1='easy_checkup_id',column2='category_id', string='Tags')
    sale_id                 = fields.Many2one('sale.order','Sale Reference',copy=False)
    doctor_id               = fields.Many2one('res.partner','Check Up by Doctor')
    check_up_date           = fields.Date('Checkup Date',default=fields.Datetime.now)
    age_year                = fields.Float('Age(In Years)')
    eye_test_type_id        = fields.Many2one('eye.test.type','Eye test type')
    birthdate               = fields.Date('Birthdate')
    mobile                  = fields.Char('Mobile')
    phone                   = fields.Char('Phone')
    power_type_id           = fields.Many2one('power.type','Power Type')
    state                   = fields.Selection([('draft','Draft'),('confirm','Confirm'),('done','Done'),('cancel','Cancel')], string='State',default='draft')
    easy_checkup_count      = fields.Integer('Easy Checkup')
    
    checkup_lines           = fields.One2many('easy.checkup.line','easy_checkup_id','Lines')
    
    #Recommendation
    
    mineral                 = fields.Boolean('Mineral')
    sv                      = fields.Boolean('S.V.')
    anti_reflection         = fields.Boolean('Anti Reflection')
    hi_index                = fields.Boolean('Hi Index')
    organic                 = fields.Boolean('Organic')
    bi_focal                = fields.Boolean('Bi Focal')
    tinting                 = fields.Boolean('Tinting')
    saftey                  = fields.Boolean('Saftey')
    photo_chromic           = fields.Boolean('Photochromic')
    progressive             = fields.Boolean('Progressive')
    mira_coat               = fields.Boolean('Mira Coat-Scratch Resistance')
    other                   = fields.Boolean('Other')
    
    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            return

        values = {
            'street'            : self.partner_id.street,
            'street2'           : self.partner_id.street2,
            'zip'               : self.partner_id.zip,
            'city'              : self.partner_id.city,
            'state_id'          : self.partner_id.state_id and self.partner_id.state_id.id,
            'country_id'        : self.partner_id.country_id and self.partner_id.country_id.id,
            'email'             : self.partner_id.email,
            'phone'             : self.partner_id.phone,
            'mobile'            : self.partner_id.mobile,
            'gstin'             : self.partner_id.gstin,
            'category_id'       : self.partner_id.category_id.ids,
            'birthdate'         : self.partner_id.birthdate,
            'age_year'          : self.partner_id.age_year,
            'easy_checkup_count': self.partner_id.easy_checkup_count
        }
        
        self.update(values)
        
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('easy.checkup') or _('New')
        result = super(EasyCheckup, self).create(vals)
        return result
    
    @api.multi
    def action_cancel(self):
        return self.write({'state':'cancel'})
    
    @api.multi
    def action_done(self):
        return self.write({'state':'done'})
    
    @api.multi
    def action_create_sale(self):
        for easy in self:
            if easy.sale_id:
                print ('Already there')
            if not easy.sale_id:
                sale_vals = {
                                'partner_id'        : easy.partner_id.id,
                                'doctor_id'         : easy.doctor_id.id,
                                'check_up_date'     : easy.check_up_date,
                                'power_type_id'     : easy.power_type_id and easy.power_type_id.id,
                                'eye_test_type_id'  : easy.eye_test_type_id and easy.eye_test_type_id.id,
                }
                line_list = []
                if easy.checkup_lines:
                    for line in easy.checkup_lines:
                        line_list.append(line.id)
                    
                    if line_list:
                        sale_vals.update({'checkup_lines_ids': [(6,0,line_list)]})
                    
                sale = self.env['sale.order'].create(sale_vals)
                if sale:
                    categ_id = self.env['product.category'].search([('name','ilike','Services')], limit=1)
                    product_id = self.env['product.product'].search([('name','ilike','Eye Checkup')], limit=1)
                    if categ_id and product_id:
                        line_vals = {               
                                        'categ_id'          : categ_id.id,
                                        'product_id'        : product_id.id,
                                        'order_id'          : sale.id,
                                        #'name'              : name,
                                        'product_uom_qty'   : 1,
                                        'price_unit'        : product_id.lst_price, 
                                        'product_uom'       : product_id.uom_id and product_id.uom_id.id
                        }
                        line = self.env['sale.order.line'].create(line_vals)
                    else:
                        raise UserError(_('Either category : Services or product: Eye Checkup is not created'))
                    
                    
                    categ_id_frame = self.env['product.category'].search([('name','ilike','Frame')], limit=1)
                    if categ_id_frame:
                        line_vals = {               
                                        'categ_id'          : categ_id_frame.id,
                                        'product_id'        : False,
                                        'order_id'          : sale.id,
                                        #'name'              : name,
                                        'product_uom_qty'   : 1,
                                        'price_unit'        : product_id.lst_price, 
                                        'product_uom'       : product_id.uom_id and product_id.uom_id.id
                        }
                        line = self.env['sale.order.line'].create(line_vals)
                    else:
                        raise UserError(_('Category : Frame is not created'))
                    
                    categ_id_glasses= self.env['product.category'].search([('name','ilike','Glasses')], limit=1)
                    if categ_id_glasses:
                        line_vals = {               
                                        'categ_id'          : categ_id_glasses.id,
                                        'product_id'        : False,
                                        'order_id'          : sale.id,
                                        #'name'              : name,
                                        'product_uom_qty'   : 1,
                                        'price_unit'        : product_id.lst_price, 
                                        'product_uom'       : product_id.uom_id and product_id.uom_id.id
                        }
                        line = self.env['sale.order.line'].create(line_vals)
                    else:
                        raise UserError(_('Category : Glasses is not created'))
                    
                    categ_id_contact_lens= self.env['product.category'].search([('name','ilike','Contact Lens')], limit=1)
                    if categ_id_contact_lens:
                        line_vals = {               
                                        'categ_id'          : categ_id_contact_lens.id,
                                        'product_id'        : False,
                                        'order_id'          : sale.id,
                                        #'name'              : name,
                                        'product_uom_qty'   : 1,
                                        'price_unit'        : product_id.lst_price, 
                                        'product_uom'       : product_id.uom_id and product_id.uom_id.id
                        }
                        line = self.env['sale.order.line'].create(line_vals)
                    else:
                        raise UserError(_('Category : Contact Lens is not created'))
                    
                    
                    
                    easy.write({'state':'confirm','sale_id': sale.id})
            
        return True
    
    @api.multi
    def action_reset_draft(self):
        self.write({'state':'draft'})
        

class EasyCheckupLine(models.Model):
    _name = "easy.checkup.line"
    
    easy_checkup_id         = fields.Many2one('easy.checkup','Easy Checkup')
    checkup_type            = fields.Selection([('Left','Left'),('Right','Right')], string='R/L')
    sph                     = fields.Char('SPH')
    cyl                     = fields.Char('CYL')
    ax                      = fields.Char('AX')
    add1                    = fields.Char('Add1')
    add2                    = fields.Char('Add2')
    ipd                     = fields.Char('IPD')
    prism                   = fields.Char('Prism')
    dim                     = fields.Char('Dim')
    base                    = fields.Char('Base')
    height                  = fields.Char('Height')
    sale_id                 = fields.Many2one('sale.order','Sale Order')
    
    
    @api.multi
    @api.onchange('sph')
    def onchange_sph(self):
        if self.sph and not '-' in self.sph:
            self.update({'sph': '+' + self.sph})
    
    @api.multi
    @api.onchange('cyl')
    def onchange_cyl(self):
        if self.cyl and not '-' in self.cyl:
            self.update({'cyl': '+' + self.cyl})
    
    @api.multi
    @api.onchange('ax')
    def onchange_ax(self):
        if self.ax and not '-' in self.ax:
            self.update({'ax': '+' + self.ax})
    
    
    @api.multi
    @api.onchange('add1')
    def onchange_add1(self):
        if self.add1 and not '-' in self.add1:
            self.update({'add1': '+' + self.add1})
    
    @api.multi
    @api.onchange('add2')
    def onchange_add2(self):
        if self.add2 and not '-' in self.add2:
            self.update({'add2': '+' + self.add2})
    
    
    @api.multi
    @api.onchange('ipd')
    def onchange_ipd(self):
        if self.ipd and not '-' in self.ipd:
            self.update({'ipd': '+' + self.ipd})
    
    @api.multi
    @api.onchange('prism')
    def onchange_prism(self):
        if self.prism and not '-' in self.prism:
            self.update({'prism': '+' + self.prism})
    
    @api.multi
    @api.onchange('dim')
    def onchange_dim(self):
        if self.dim and not '-' in self.dim:
            self.update({'dim': '+' + self.dim})
    
    
    @api.multi
    @api.onchange('base')
    def onchange_base(self):
        if self.base and not '-' in self.base:
            self.update({'base': '+' + self.base})
    
    @api.multi
    @api.onchange('height')
    def onchange_height(self):
        if self.height and not '-' in self.height:
            self.update({'height': '+' + self.height})
            
class EyeTestType(models.Model):
    _name = "eye.test.type"
    name                = fields.Char('Name')

class PowerType(models.Model):
    _name = "power.type"
    name                = fields.Char('Name')
    
    