# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
from openerp import models, api,exceptions, fields, _
from openerp.exceptions import Warning
from datetime import datetime, date, timedelta
import time
from odoo.exceptions import ValidationError, UserError, except_orm
import logging
import httplib2 as http
import json
import base64
import urllib
import urllib2
import requests
from datetime import date, datetime, timedelta
_logger = logging.getLogger(__name__)


class PakdoOrderLine(models.TransientModel):
    _name = "pakdo.order.line"
    
    pakdo_order_id  = fields.Many2one('pakdo.order')
    product_id    = fields.Many2one('product.product', 'Product/SKU')
    name          = fields.Char('Comment')
    quantity      = fields.Integer('Quantity')
    price         = fields.Float('Price')
    line_id       = fields.Many2one('sale.order.line','Sale Lines')
        

class PakdoOrder(models.TransientModel):
    _name = "pakdo.order"
    
    @api.model
    def _get_line(self):
        res = []
        context = dict(self._context or {})
        if context.get('active_id'):
            sale = self.env['sale.order'].browse(context.get('active_id'))
            line_list = []
            for line in sale.order_line:
                if line.product_id.barcode and line.product_id.type == 'product':
                    if line.product_id.pakdo_qty > 0 :
                        if line.shipped_type != 'fba' and line.shipped_type != 'pakdo': 
                            line_vals = {'product_id':line.product_id.id, 'quantity': line.product_uom_qty, 'name': line.name, 'price' : line.price_unit, 'line_id':line.id }
                            res.append(line_vals)
        return res
        
    
    name            = fields.Char('Fulfillment Order #')
    
    
    order_date      = fields.Date('Order Date',default=fields.Date.context_today)
    
    customer_name   = fields.Char('Customer Name')
    street1         = fields.Char('Street 1')
    street2         = fields.Char('Street 2')
    city            = fields.Char('City')
    zip             = fields.Char('ZIP')
    country_id      = fields.Many2one('res.country', 'Country')
    state_id        = fields.Many2one('res.country.state', 'State')
    customer_email  = fields.Char('Email')
    separate_picking = fields.Boolean('Separate Picking')
    
    line_ids        = fields.One2many('pakdo.order.line', 'pakdo_order_id', 'Lines', default=_get_line)
    
    
    
    @api.model
    def default_get(self, fields):
        resp = super(PakdoOrder, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        sale = self.env['sale.order'].browse(context.get('active_id'))
        
        resp['name'] = sale.name
        
        if sale.is_ship_differ:
            if sale.partner_shipping_id.company_name:
                resp['street1']  = sale.partner_shipping_id.company_name
                if sale.partner_shipping_id.street2:
                    resp['street2'] = sale.partner_shipping_id.street + ' ' + sale.partner_shipping_id.street2
                else:
                    resp['street2'] = sale.partner_shipping_id.street
            else:
                resp['street1']  = sale.partner_shipping_id.street
                resp['street2'] =  sale.partner_shipping_id.street2 or ''
                
            if sale.partner_shipping_id.shopware_company_name:
                resp['customer_name'] = sale.partner_shipping_id.shopware_company_name + ',' + sale.partner_shipping_id.name
            else:
                resp['customer_name'] = sale.partner_shipping_id.name
                
            #resp['street1']       = street1
            #resp['street2']       = sale.partner_shipping_id.street2 and sale.partner_shipping_id.street2 or ''
            resp['city']          = sale.partner_shipping_id.city and sale.partner_shipping_id.city or ''
            resp['zip']           = sale.partner_shipping_id.zip and sale.partner_shipping_id.zip or ''
            resp['country_id']    = sale.partner_shipping_id.country_id and sale.partner_shipping_id.country_id.id or ''
            resp['customer_email'] = sale.partner_shipping_id.email and sale.partner_shipping_id.email or sale.partner_id.email
        else:
            if sale.partner_id.company_name:
                resp['street1']  = sale.partner_id.company_name
                if sale.partner_id.street2:
                    resp['street2'] = sale.partner_id.street + ' ' + sale.partner_id.street2
                else:
                    resp['street2'] = sale.partner_id.street
            else:
                resp['street1']  = sale.partner_id.street
                resp['street2'] =  sale.partner_id.street2 or ''
            
            if sale.partner_id.shopware_company_name:
                resp['customer_name'] = sale.partner_id.shopware_company_name + ',' +sale.partner_id.name
            else:
                resp['customer_name'] = sale.partner_id.name
#             resp['street1']       = street1
#             resp['street2']       = sale.partner_id.street2 and sale.partner_id.street2 or ''
            resp['city']          = sale.partner_id.city and sale.partner_id.city or ''
            resp['zip']           = sale.partner_id.zip and sale.partner_id.zip or ''
            resp['country_id']    = sale.partner_id.country_id and sale.partner_id.country_id.id or ''
            resp['customer_email'] = sale.partner_id.email
        
        if not sale.partner_id.state_id:
            state = self.env['res.country.state'].search([('name','=','-')], limit=1)
            if state:
                resp['state_id'] = state.id
        else:
            resp['state_id'] = sale.partner_id.state_id and sale.partner_id.state_id.id

        return resp
    
    @api.multi
    def create_pakdo(self):
        print 'create_pakdo create_pakdo create_pakdo create_pakdo       '
        context = dict(self._context or {})
        sale = self.env['sale.order'].browse(context.get('active_id'))
        
        pakdo = self.env['pakdo.config'].search([])
        
        #Push order code
        conn = pakdo.test_connection()[0]
        token = conn[0]
        session = conn[-1]
        print 'token token token      ',token
        headers = {'Authorization': 'Token token='+token}
        
        #unixtime_order_date = time.mktime(self.order_date.timetuple())
        unixtime_order_date = time.mktime(datetime.strptime(self.order_date, "%Y-%m-%d").timetuple())
        
        order_data = {"client_order_number":self.name,"date":unixtime_order_date,"payment_date":unixtime_order_date,"gender":"0","firm":False,"first_name":self.customer_name,"last_name":False,
                      "mail":self.customer_email,"country":self.country_id.code if self.country_id else "DE","city":self.city,"zip":self.zip,"street":self.street1,"street_2": self.street2 if self.street2 else False,
                      "house_number":False,
                      "region":self.state_id.name if self.state_id else ''}
        
        if self.separate_picking:
            order_data.update({'separate_picking': 1})
        else:
            order_data.update({'separate_picking': ''})
        
        #              "products_sku":["4260281474983","0348649248"],"products_quantity":["1","2"]}
        sku_list = []
        qty_list = []
        price_list = []
        vat_list = []
        line_lists = []
        for line in self.line_ids:
            if line.product_id.barcode:
                resp_product = session.get('https://api.app2.de/v1/products/?gtin[0]='+str(line.product_id.barcode), headers=headers)
                try:
                    product_dict = json.loads(resp_product.content)
                    if 'id' in product_dict:
                        product_id = product_dict.get('id')[0]
                        #print 'product_id product_id        ',product_id
                        qty = product_dict.get('products')[str(product_id)]['quantity']['2']['total_quantity']
                        _logger.info('importing >>>>>>>>>>>>>>>>>>>>>>>>    ' +  str(line.product_id.default_code) + '-' +  str(qty))
                        line.product_id.write({'pakdo_qty': qty,'pakdo':True})
                        self.env.cr.commit()
                except:
                    _logger.info('Error in Pakdo get product  ' + str(line.product_id.barcode))
                    continue
                if line.product_id.pakdo_qty < line.quantity:
                    raise UserError(_(line.product_id.default_code + ' has Qty less.Required Qty ' + str(line.quantity) + ' but Pakdo has qty ' + str(line.product_id.pakdo_qty)))
                else:
                    sku_list.append(line.product_id.barcode)
                    qty_list.append(line.quantity)
                    vat_list.append('19')
                    price_list.append(line.price)
                    line_lists.append(line)
                    
                    
        
        order_data.update({"products_sku" : sku_list,"products_quantity" : qty_list, "products_price" : price_list, "products_vat": vat_list})
        
        try:
            json_order = json.dumps(order_data)
            resp = requests.post('https://api.app2.de/v1/orders/',json_order,headers=headers)
            
            resp_dict = json.loads(resp.content)
            if 'error' in resp_dict:
                raise UserError(_(resp_dict.get('error')[0]))
            
            for l in line_lists:
                l.line_id.write({'shipped_type':'pakdo'})
            user = self.env['res.users'].browse(self.env.uid)
            vals = {
                        'body': u'<p><br/>Pakdo Order <b>%s</b> Created <br/> By <b>%s</b> at <b>%s</b></p><br/>' %(self.name ,user.name, datetime.today()), 
                        'model': 'sale.order', 
                        'res_id': context.get('active_id'), 
                        'subtype_id': False, 
                        'author_id': user.partner_id.id, 
                        'message_type': 'comment', }        
            
            self.env['mail.message'].create(vals)
        except:
            if 'error' in resp_dict:
                raise UserError(_('Please try after some times, other process in que.....or ' + str(resp_dict.get('error')[0])))
            else:
                raise UserError(_('Please try after some times, other process in que.....'))
             
        _logger.info('Pakdo Push order created successfully........')
        return True