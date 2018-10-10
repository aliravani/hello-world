
# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
from openerp import models, api,exceptions, fields, _
from openerp.exceptions import Warning
from openerp.tools import frozendict
import time
from openerp.exceptions import UserError, RedirectWarning, ValidationError
from datetime import date, timedelta, datetime

from psycopg2 import OperationalError

import base64
import tempfile
import csv
import itertools
import logging
_logger = logging.getLogger(__name__)

from io import BytesIO
import re


class SaleCSVImport(models.TransientModel):
    _name = "sale.csv.import"
    
    file            = fields.Binary("File")
    filename        = fields.Char("Filename")
    
    
    @api.multi
    def action_import(self):
        for record in self:
            sale_pool = self.env['sale.order']
            product_pool = self.env['product.product']
            partner_pool = self.env['res.partner']
            state_pool = self.env['res.country.state']
            
            datafile=record.file
            if datafile:
                csv_data = base64.decodestring(datafile)
            csv_data = csv_data.decode("utf-8")
            csv_data = csv_data.splitlines()
            
            reader = csv.reader(csv_data, delimiter='\t')
            reader = list(reader)
            error_email = ''
            try:
                for row in reader:
                    if not row[0] == 'Name' and not row[1] == 'Email':
                        
                        name                = row[0]
                        customer_email      = row[1]
                        shipping_method     = row[14]
                        qty                 = row[16]
                        product             = row[17]
                        default_code        = row[20]
                        customer_name       = row[34]
                        customer_street2    = row[35]
                        customer_street     = row[37]
                        customer_company    = row[38]
                        customer_city       = row[39]
                        customer_zip        = row[40]
                        customer_country    = row[42]
                        customer_phone      = row[43]
                        
                        name = re.sub('[!@#$]', '', name)
                        customer_zip = customer_zip.replace("'","")
                        
                        error_email = customer_email
                        
                        partner = self.env['res.partner'].search([('email','=',customer_email),('street','=',customer_street),('street2','=',customer_street2)], limit=1)
                        if not partner:
                            partner_vals = {}
                            customer_name_list = customer_name.split(' ')
                            if len(customer_name_list) == 2:
                                partner_vals['first_name'] = customer_name_list[0]
                                partner_vals['last_name'] = customer_name_list[1]
                            
                            if len(customer_name_list) == 1:
                                partner_vals['first_name'] = customer_name_list[0]
                                partner_vals['last_name'] = '-'
                            
                            country = self.env['res.country'].search([('code','=',customer_country)])
                            if country:
                                partner_vals['country_id'] = country.id
                            
                            
                            partner_vals.update({
                                            'email'     : customer_email,
                                            'street'    : customer_street,
                                            'street2'   : customer_street2,
                                            'custom_company_name' : customer_company,
                                            'city'      : customer_city,
                                            'zip'       : customer_zip,
                                            'phone'     : customer_phone,
                                            
                                })
                            partner = self.env['res.partner'].create(partner_vals)
                        
                        if partner:
                            if shipping_method == 'Standard Versand' or shipping_method == 'Free Shipping':
                                carrier = self.env['shipcloud.carrier'].search([('name','=','hsi')])
                                service = self.env['carrier.services'].search([('name','=','standard')])
                                package_type = self.env['package.type'].search([('name','=','parcel')])
                                if carrier and service:
                                    sales = self.env['sale.order'].create({'name':name,'partner_id':partner.id, 'shipcloud_carrier_id':carrier.id,'carrier_services_id':service.id,
                                                                           'package_type_id': package_type.id
                                                                           
                                                                           })
                        
                                    if sales:
                                        product = self.env['product.product'].search([('default_code','=',default_code)],limit=1)
                                        if product:
                                            line = self.env['sale.order.line'].create({'order_id':sales.id,'product_id':product.id,
                                                                                       'product_uom_qty': qty
                                                                                       })
                        
            except:
                raise UserError(_('Please Check CSV file, i.e csv file must be seprated by TAB or check line with email : %s') % (error_email))
            