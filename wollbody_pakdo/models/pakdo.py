# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError, except_orm
from odoo.osv import expression
from datetime import date, datetime, timedelta


import httplib2 as http
import json
import base64
import urllib
import urllib2
import requests
import time



try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


import logging
_logger = logging.getLogger(__name__)

headers = {'Accept': 'application/json', 'Content-Type': 'application/json; charset=UTF-8'}


# order status = -1  means cancelled

class PakdoConfig(models.Model):
    _name = 'pakdo.config'
    
    name              = fields.Char('Name')
    url               = fields.Char('Host API Url', size=64)
    user              = fields.Char('Email', size=64)
    pwd               = fields.Char('Password',size=64)
    state             = fields.Selection([('draft','Draft'),('connected','Connection Success'),('error','Error')], 'State', default='draft', readonly=True)
    all_update        = fields.Boolean('ALL Update')
    track_datetime    = fields.Datetime('Tracking Import From')
    
    @api.multi
    def reset(self):
        return self.write({'state':'draft'})
    
    @api.one
    def test_connection(self):
        data_dict = {
                    'email': self.user,
                    'password': self.pwd
                }
        json_data = json.dumps(data_dict)
        with requests.Session() as session:
            p = session.post(self.url+'/auth/', json_data)
            if self.state != 'connected':
                if p.status_code == 200:
                    return self.write({'state':'connected'})
                else:
                    return self.write({'state':'error'})
                
            json_decode = json.loads(p.content)
            token = json_decode.get('token')
            return token, session
    
    @api.multi
    def push_product(self, product=False):
        conn = self.test_connection()[0]
        token = conn[0]
        session = conn[-1]
        if product and token:
            headers = {'Authorization': 'Token token='+token}
            #product_data ={"name":["qwery"],"gtin":["111222333"],"quantity":["15"],"price":["12"]}
            
            product_name = ''
            if product.supplier_name:
                product_name = product.supplier_name
            if  product.art_name:
                product_name += ' ' + product.art_name
                
            if product.art_no_original:
                product_name += ' ' + product.art_no_original
            elif product.art_no:
                product_name += ' ' + product.art_no
            
            if product.color_no:
                product_name += ' ' + product.color_no
            
            if product.color_name:
                product_name += ' ' + product.color_name
            
            if product.get_size:
                product_name += ' ' + product.get_size
            
            identifier_1 = ''
            default_code_count = product.default_code.count('/')
            if default_code_count >= 2:
                identifier_1 = product.default_code
            else:
                identifier_1 = product.get_int_no
                
            product_data ={"name":[product_name],"gtin":[product.barcode],"quantity":[product.pakdo_qty or 0 ],"price":[product.lst_price], 
                           "identifier_1": [identifier_1],"identifier_2": [product.fnsku] if product.fnsku else [''],"picture": [
                           {
                             "name": product.name + '.png',
                             "data": product.image_medium
                           }]
                           }
            json_product = json.dumps(product_data)
            _logger.info(str(json_product))
            resp = requests.post('https://api.app2.de/v1/products/',json_product,headers=headers)
            _logger.info(str(resp.content))
            
            resp_dict = json.loads(resp.content)
            if 'error' in resp_dict:
                raise UserError(_(resp_dict.get('error')[0]))
            else:
                product.write({'pakdo': True,'pakdo_image': True})
            return True
        
    
    @api.multi
    def update_product(self, product=False):
        conn = self.test_connection()[0]
        token = conn[0]
        session = conn[-1]
        if product and token:
            headers = {'Authorization': 'Token token='+token}
            
            #product_data={'current_gtin':['0348649248'],'name':['Baby Blanket'],'gtin':['0348649248'],'quantity':['80'],'price':['5']}
            product_name = ''
            if product.supplier_name:
                product_name = product.supplier_name
            if  product.art_name:
                product_name += ' ' + product.art_name
                
            if product.art_no_original:
                product_name += ' ' + product.art_no_original
            elif product.art_no:
                product_name += ' ' + product.art_no
            
            if product.color_no:
                product_name += ' ' + product.color_no
            
            if product.color_name:
                product_name += ' ' + product.color_name
            
            if product.get_size:
                product_name += ' ' + product.get_size
            
            if product.image_medium:
                
                identifier_1 = ''
                default_code_count = product.default_code.count('/')
                if default_code_count >= 2:
                    identifier_1 = product.default_code
                else:
                    identifier_1 = product.get_int_no
                    
                product_data = {"current_gtin":[product.barcode], "current_identifier_1": [product.get_int_no] if product.get_int_no else '',"current_identifier_2": [product.fnsku] if product.fnsku else '',
                                "name":[product_name],"gtin":[product.barcode],"quantity":[''],"price":[product.lst_price], "identifier_1": [identifier_1],
                                "identifier_2": [product.fnsku] if product.fnsku else '', "picture": [
                               {
                                 "name": product.name + product.color_no + '.png',
                                 "data": product.image_medium
                               }]
                                }
                json_product = json.dumps(product_data)
                 
                resp = requests.put('https://api.app2.de/v1/products/',json_product, headers=headers)
                resp_dict = json.loads(resp.content)
                if 'error' in resp_dict:
                    raise UserError(_(resp_dict.get('error')[0]))
                else:
                    product.write({'pakdo': True,'pakdo_image':True})
            
        return True
    
    @api.multi
    def push_all_image(self):
        
        templates = self.env['product.template'].search([('image_pushed_method','=',False)])
        for template in templates:
            if not template.image_pushed_method:
                for tmpl in template.get_alternative:
                    for product in tmpl.product_variant_ids:
                        try:
                            self.update_product(product)
                        except:
                            _logger.info('problem in exporting main')
                
                
            
            ########################
                for product in template.product_variant_ids:
                    try:    
                        self.update_product(product)
                    except:
                        _logger.info('problem in exporting  child')
                
                template.write({'image_pushed_method':True})
                self._cr.commit()
                _logger.info('push all image in progress >>>>>>>>>>>>>>>>      ' + str(template))
                time.sleep(3)
                
            _logger.info('push all image in progress >>>>>>>>>>>>>>>>     doneeeeeeee ')
        
    @api.multi
    def update_all_product(self, product=False):
        conn = self.test_connection()[0]
        token = conn[0]
        session = conn[-1]
        if self.all_update:
            products = self.env['product.product'].search([('barcode','!=',False)])
        else:
            products = self.env['product.product'].search([('push_pakdo','=',True)])
        if products and token:
            for product in products:
                headers = {'Authorization': 'Token token='+token}
                
                #product_data={'current_gtin':['0348649248'],'name':['Baby Blanket'],'gtin':['0348649248'],'quantity':['80'],'price':['5']}
                product_data = {"current_gtin":[product.barcode],"name":[product.name],"gtin":[product.barcode],"quantity":[False],"price":[product.lst_price]}
                json_product = json.dumps(product_data)
                resp = requests.put('https://api.app2.de/v1/products/',json_product, headers=headers)
                resp_dict = json.loads(resp.content)
                if 'error' in resp_dict:
                    raise UserError(_(resp_dict.get('error')[0]))
                else:
                    product.write({'pakdo': True,'pakdo_image':True})
                
            
        return True
    
    @api.multi
    def delete_product(self, product=False):
        conn = self.test_connection()[0]
        token = conn[0]
        session = conn[-1]
        if product and token:
            headers = {'Authorization': 'Token token='+str(token)}
            product_data = {"gtin":[product.barcode]}
            #json_product = json.dumps(product_data)
            resp = requests.delete('https://api.app2.de/v1/products/',headers=headers, json=product_data)
            #product.write({'pakdo':False})
            
        return True
    
    @api.multi
    def get_product(self,product=False):
        conn = self.test_connection()[0]
        token = conn[0]
        session = conn[-1]
#         if self.all_update:
#             odoo_products = self.env['product.product'].search([('barcode','!=',False),('type','=','product')])
#         else:
#             odoo_products = self.env['product.product'].search([('push_pakdo','=',True),('type','=','product')])
        
        if self.all_update:
            self.env.cr.execute("SELECT id from product_product WHERE barcode != ''")
            all_ids = [x[0] for x in self.env.cr.fetchall()]
        else:
            self.env.cr.execute("SELECT id from product_product WHERE pakdo == True")
            all_ids = [x[0] for x in self.env.cr.fetchall()]
        
        print len(all_ids)
        
        #_logger.info(str(odoo_products))
        #print len(odoo_products.ids)
        if all_ids and token and session:
            for odoo_product in self.env['product.product'].browse(all_ids):
                headers = {'Authorization': 'Token token='+str(token)}
                #product = session.get('https://api.app2.de/v1/products/?gtin[0]=123>in[1]=&identifier_1[0]=456&identifier_1[1]=&identifier_2[0]=789&identifier_2[1]', headers=headers)
                if odoo_product.barcode:
                    #all_data  = odoo_product.barcode + ' / ' +  odoo_product.get_int_no if odoo_product.get_int_no else 'No-intno'  + ' / ' + odoo_product.fnsku if odoo_product.fnsku else 'No-fnsku'
                    #_logger.info(str(odoo_product.default_code))
                    #_logger.info(str(all_data))
                    #resp_product = session.get('https://api.app2.de/v1/products/?gtin[0]='+str(odoo_product.barcode)+'>in[1]=&identifier_1[0]='+str(odoo_product.get_int_no) if odoo_product.get_int_no else ''+'&identifier_1[1]=&identifier_2[0]='+ str(odoo_product.fnsku) if odoo_product.fnsku else '' +'&identifier_2[1]', headers=headers)
                    #4260445695858
                    resp_product = session.get('https://api.app2.de/v1/products/?gtin[0]='+str(odoo_product.barcode), headers=headers)
                    try:
                        product_dict = json.loads(resp_product.content)
                        print 'product_dict product_dict        ',product_dict
                        if 'id' in product_dict:
                            product_id = product_dict.get('id')[0]
                            print 'product_id product_id        ',product_id
                            qty = product_dict.get('products')[str(product_id)]['quantity']['2']['total_quantity']
                             
                            _logger.info('importing >>>>>>>>>>>>>>>>>>>>>>>>    ' +  str(odoo_product.default_code) + '-' +  str(qty))
                            odoo_product.write({'pakdo_qty': qty,'pakdo':True})
                            self.env.cr.commit()
                    except:
                        #_logger.info('Error in Pakdo get product  ' + str(odoo_product.barcode))
                        continue
                
        
    
    @api.multi
    def push_order(self, order=False):
        conn = self.test_connection()[0]
        token = conn[0]
        session = conn[-1]
        
        headers = {'Authorization': 'Token token='+token}
        
        #order_data = {"client_order_number":"1234567","date":"1493149625","payment_date":"1493149625","gender":"0","firm":"App2 GmbH","first_name":"Raphael","last_name":"R\u00fcbenacker",
        #              "mail":"ruebenacker@app2.de","country":"DE","city":"Bruchsal","zip":"76646","street":"Zaisental","house_number":"12","region":"Baden-W\u00fcrttemberg",
        #              "products_sku":["4260281474983","0348649248"],"products_quantity":["1","2"]}
        
        
        today = datetime.strptime(time.strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S')
        order_data = {"client_order_number":order.name,"date":today,"payment_date":today,"gender":"0","firm":"App2 GmbH","first_name":order.customer_name,"last_name":False,
                      "mail":order.customer_email,"country":order.partner_id.country_id.code if order.partner_id.country_id else "DE","city":order.city,
                      "zip":order.zip,"street":order.street1,"house_number":"12","region":order.state_id.name if order.state_id else '','separate_picking': ''}
        
        #              "products_sku":["4260281474983","0348649248"],"products_quantity":["1","2"]}
        sku_list = []
        qty_list = []
        for line in order.line_ids:
            sku_list.append(line.product_id.barcode)
            qty_list.append(line.quantity)
            line.write({'shipped_type':'pakdo'})
        
        order_data.update({"products_sku" : sku_list,"products_quantity" : qty_list})
        
        json_order = json.dumps(order_data)
        resp = requests.post('https://api.app2.de/v1/orders/',json_order,headers=headers)
        print 'resp resp respresp               ',resp
        print 'resp resp respresp               ',resp.content
        
        return True
    
    
    @api.multi
    def update_order(self, order=False):
        #update include delete which is change the status to cancel (-2)
        conn = self.test_connection()[0]
        token = conn[0]
        session = conn[-1]
        
        headers = {'Authorization': 'Token token='+token}
        
        order_data = {"current_client_order_number":"1234567","client_order_number":"1234567","date":"1493149625","payment_date":"1493149625","gender":"0","firm":"App2 GmbH","first_name":"Raphael","last_name":"R\u00fcbenacker",
                      "mail":"ruebenacker@app2.de","country":"DE","city":"Bruchsal","zip":"76646","street":"Zaisental","house_number":"12","region":"Baden-W\u00fcrttemberg","order_status": "-2",
                      "products_sku":["4260281474983","0348649248"],"products_quantity":["1","2"]}
        
        
        
        
        
        
        
        
        json_order = json.dumps(order_data)
        resp = requests.put('https://api.app2.de/v1/orders/',json_order,headers=headers)
        print 'resp resp respresp               ',resp
        print 'resp resp respresp               ',resp.content
        
            
        return True
    
    
    @api.multi
    def get_order(self,order=False):
        conn = self.test_connection()[0]
        token = conn[0]
        session = conn[-1]
        #odoo_orders = self.env['sale.order'].search([('pakdo','=',True)])
        
        #if odoo_orders and token and session:
        #    for odoo_order in odoo_orders:
        headers = {'Authorization': 'Token token='+str(token)}
        #order = session.get('https://api.app2.de/v1/orders/?client_order_number='+str(order.name), headers=headers)
        order = session.get('https://api.app2.de/v1/orders/?client_order_number=1234567', headers=headers)
        order_dict = json.loads(order.content)
        print 'order_dict order_dict order_dict      ',order_dict
        return True
    
    
    @api.multi
    def get_tracking_code(self):
        #1501286461
        conn = self.test_connection()[0]
        token = conn[0]
        session = conn[-1]
        headers = {'Authorization': 'Token token='+str(token)}
        
        if self.track_datetime:
            track_datetime = datetime.strptime(self.track_datetime, '%Y-%m-%d %H:%M:%S')
            ans_time = time.mktime(track_datetime.timetuple())
            _logger.info('Tracking import from  ' + str(ans_time))
            
            tracking_numbers = session.get('https://api.app2.de/v1/tracking/?time='+str(ans_time), headers=headers)
        else:
            tracking_numbers = session.get('https://api.app2.de/v1/tracking/?time=', headers=headers)
        
        content_dict = json.loads(tracking_numbers.content)
        conten_track = content_dict.get('trackingnumbers')
        for order,track in conten_track.items():
            _logger.info('Tracking import from  ' + str(order) + '-' + str(track))
            
            sales_2 = self.env['sale.order'].search([('sale_order_number_2','=',order)])
            if sales_2:
                sales = sales_2
            else:
                sales = self.env['sale.order'].search([('name','=',order)])
             
            for sale in sales:
                sale.write({'pakdo_tracking_code': track})
    
    
        
    @api.model
    def pakdo_get_stock_cron(self, use_new_cursor=False):
        pakdo_obj = self.search([], limit=1)[0]
        pakdo_obj.get_product()
            