# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError, except_orm
from odoo.osv import expression
from datetime import date, datetime, timedelta
import time

import urllib
import urllib2
import base64
import hmac
import hashlib

from xml.dom import minidom
import ecs

import odoo.addons.decimal_precision as dp

from boto.mws.connection import MWSConnection

import logging
_logger = logging.getLogger(__name__)

class AmazonConfig(models.Model):
    _name = 'amazon.config'
    
    domain                        = fields.Char('Domain', default='https://mws.amazonaws.de')
    user_agent                    = fields.Char('User Agent', default='App/Version (Language=Python)')
    seller_id                     = fields.Char('Seller ID', readonly=True, states={'draft': [('readonly', False)]})
    aws_access_key_id             = fields.Char('AWS Access Key', readonly=True, states={'draft': [('readonly', False)]})
    secret_key                    = fields.Char('Secret Key',readonly=True, states={'draft': [('readonly', False)]})   
    state                         = fields.Selection([('draft','Draft'),('connected','Connection Success'),('error','Connection Failed')], 'State', readonly=True, default='draft')         
    import_from                   = fields.Date('Import From Date')
    inventory_sync                = fields.Datetime('Inventory Sync')
    name                          = fields.Char('Name')
    product_ids                   = fields.Char('ProduktID')
    market_place_id               = fields.Char('MarktID')
    finance_import_from           = fields.Date('Finance Import From')
    
    date_1                        = fields.Datetime('Date-1')
    date_2                        = fields.Datetime('Date-2')
    date_3                        = fields.Datetime('Date-3')
    date_4                        = fields.Datetime('Date-4')
    
    @api.multi
    def xml_to_dict(self, xml):
        try:
            dom = minidom.parseString(xml)
        except:
            # is not an XML object, so return raw text
            return xml
        else:
            return ecs.unmarshal(dom)
    
    @api.multi
    def reset(self):
        self.write({'state':'draft'})
    
    @api.multi
    def calc_signature(self, domain, secret_key, request_description, section='/Orders/2011-01-01'):
        sig_data = 'GET\n' + domain.replace('https://', '').lower() + '\n' + section + '\n' + request_description
        sig_data = str(sig_data)
        secret_key = str(secret_key)
        return base64.b64encode(hmac.new(secret_key, sig_data, hashlib.sha256).digest())
    
    @api.multi
    def make_request(self, request, section, version):
        amazon_obj = self.search([], limit=1)[0]
        data = {
                    'AWSAccessKeyId'   : amazon_obj.aws_access_key_id,
                    'SellerId'         : amazon_obj.seller_id,
                    'SignatureMethod'  : 'HmacSHA256',
                    'SignatureVersion' : '2',
                    'Timestamp'        : datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    'Version'          : version
        }
        data.update(request)
        
        request_description = '&'.join(['%s=%s' % (k, urllib.quote(data[k], safe='-_.~')) for k in sorted(data)])
        signature = self.calc_signature(amazon_obj.domain, amazon_obj.secret_key, request_description, section)
        request = '%s%s?%s&Signature=%s' % (amazon_obj.domain, section, request_description, urllib.quote(signature))

        try:
            xml = urllib2.urlopen(urllib2.Request(request, headers={'User-Agent': amazon_obj.user_agent})).read()
        except urllib2.URLError, e:
            xml = e.read()
        
        ret_val = False
        try:
            dom = minidom.parseString(xml)
        except:
            ret_val =  xml
        else:
            ret_val = ecs.unmarshal(dom)
            
        return ret_val
    
    @api.multi
    def test_connection(self):
        for amazon in self:
            request = dict(Action='GetServiceStatus')
            bag =  self.make_request(request, section='/Orders/2011-01-01', version='2011-01-01')
            
            if (bag.GetServiceStatusResponse.GetServiceStatusResult.Status == u'GREEN'):
                amazon.write({'state':'connected'})
            else:
                amazon.write(cr, uid, ids, {'state':'failed'})
        return True
    
    @api.multi
    def list_inventory_supply(self):
        _logger.info('Amazon : Importing Stock........')
        amazon_obj = self.search([], limit=1)[0] 
        next_token = True
        mws = MWSConnection(
                            SellerId = amazon_obj.seller_id,
                            aws_access_key_id=amazon_obj.aws_access_key_id,aws_secret_access_key=amazon_obj.secret_key, 
                            host="mws.amazonaws.de"
                            )
         
        yesterday = date.today() - timedelta(2)
        #6304161746
           
        #xml = mws.list_inventory_supply(QueryStartDateTime=yesterday.strftime('%Y-%m-%d'))
        xml = mws.list_inventory_supply(QueryStartDateTime="2016-01-01")
        if hasattr(xml._result, 'NextToken'):
            next_token = xml._result.NextToken
                         
        while True:
            if hasattr(xml._result, 'InventorySupplyList'):  
                members = xml._result.InventorySupplyList
                 
            ### Construct values
            for member in members:
                #try:
                
                product_obj = self.env['product.product'].search([('default_code','=', member.SellerSKU)], limit=1)
                print 'member.SellerSKU       ',member.SellerSKU, product_obj.id
                if product_obj:
                    vals = {
                                'asin'                  : member.ASIN,
                                'fnsku'                 : member.FNSKU,
                                'fba_qty'               : member.InStockSupplyQuantity,
                            }
                    product_obj.write(vals)
             
            if hasattr(xml._result, 'NextToken'):
                next_token = xml._result.NextToken
                xml = mws.list_inventory_supply_by_next_token(NextToken=next_token)
            else:
                break
            
        _logger.info('Amazon : Importing Stock Completed............!!!!!!!!!!!!')
        return amazon_obj.write({'date_1' : datetime.now()}) 
    
    @api.model
    def list_inventory_supply_cron(self, use_new_cursor=False):
        amazon_obj = self.search([], limit=1)[0]
        #amazon_obj.list_inventory_supply()
        #amazon_obj.get_product_my_price()
        
        shopware_obj = self.env['shopware.config'].search([], limit=1)
        if shopware_obj:
            shopware_obj.export_stock_all_cron()
    
    @api.multi
    def get_product_my_price(self):
        _logger.info('Amazon : Importing My Price........')
        product_pool = self.env['product.product']
        self.env.cr.execute("SELECT default_code from product_product WHERE default_code != ''")
        all_sku = [x[0] for x in self.env.cr.fetchall()]
        # Amazon login data entries from the database
        amazon_obj = self.search([], limit=1)[0] 
        mws = MWSConnection(
                             SellerId = amazon_obj.seller_id,
                             aws_access_key_id=amazon_obj.aws_access_key_id,aws_secret_access_key=amazon_obj.secret_key, 
                             host="mws.amazonaws.de"
                             )  
         
        count = 0
        my_start_list = 0
        my_end_list   = 20
        while count <= len(all_sku):
             sku = all_sku[my_start_list:my_end_list]
             try:
                 reply = mws.get_my_price_for_sku(
                         MarketplaceId=amazon_obj.market_place_id,
                         ItemCondition='New',
                         SellerSKUList=sku)
                 
                 for unit in reply.GetMyPriceForSKUResult:
                     if hasattr(unit.Product, 'Identifiers'):
                         seller_sku = str(unit.Product.Identifiers.SKUIdentifier.SellerSKU)
                         vals = {}
                         if unit.Product.Offers.Offer:
                             vals = {
                                     'amazon_my_price'  :  float(unit.Product.Offers.Offer[0].BuyingPrice.ListingPrice.Amount) 
                             }
                         
                             product_obj = self.env['product.product'].search([('default_code','=', seller_sku)], limit=1)
                             if product_obj:
                                product_obj.write(vals)
                         
                         
             
             #if count in [500,1000,1500,2000,2500,3000,3500,4000,4500,5000]:
             #    time.sleep(10)
                 count = count + 20
                 my_start_list = my_end_list
                 my_end_list   = my_end_list + 20
             except:
                continue
        _logger.info('Amazon : Importing My Price Completed............!!!!!!!!!!!!') 
        return amazon_obj.write({'date_2' : datetime.now()})
    
    
#     @api.multi
#     def import_product_name_new(self):
#         _logger.info('Amazon : Importing Product Name........')
#         self.env.cr.execute("SELECT asin from product_product WHERE asin != ''")
#         all_sku = [x[0] for x in self.env.cr.fetchall()]
# 
#         ## Amazon login data entries from the database
#         amazon_obj = self.search([], limit=1)[0]
#         mws = MWSConnection(
#                             SellerId = amazon_obj.seller_id,
#                             aws_access_key_id=amazon_obj.aws_access_key_id,aws_secret_access_key=amazon_obj.secret_key, 
#                             host="mws.amazonaws.de"
#                             )  
#         count = 0
#         name_start = 0
#         name_end   = 10
#         while count <= len(all_sku):
#             #try:
#             sku = all_sku[name_start:name_end]
#             response = mws.get_matching_product(
#                     MarketplaceId=amazon_obj.market_place_id,
#                     #IdType='ASIN',
#                     ASINList=sku)
#             for member in response.GetMatchingProductResult:
#                 print 'member member member ',member.Product.Identifiers.MarketplaceASIN.ASIN
#                 if hasattr(member.Product, 'AttributeSets'):
#                     if member.Product.Identifiers:
#                         asin = member.Product.Identifiers.MarketplaceASIN.ASIN
#                         vals = {
#                                      'amazon_name' : member.Product.AttributeSets.ItemAttributes[0].Title
#                                      }
#                         product_obj = self.env['product.product'].search([('asin','=', asin)], limit=1)
#                         #print 'product_obj product_obj product_obj ',product_obj
#                         if product_obj:
#                             product_obj.write(vals)
#                 
#                 if count in [500,1000,1500,2000,2500,3000,3500,4000,4500,5000]:
#                     time.sleep(10)
#             
#             count = count + 10
#             name_start = name_end
#             name_end   = name_end + 10
#             #except:
#             #    continue        
#         
#         _logger.info('Amazon : Importing Product Name Completed............!!!!!!!!!!!!')
#         return True
    
    @api.multi
    def import_product_name(self):
        _logger.info('Amazon : Importing Product Name........')
        product_pool = self.env['product.product']
        
        self.env.cr.execute("SELECT asin from product_product WHERE asin != ''")
        all_sku = [x[0] for x in self.env.cr.fetchall()]

        ## Amazon login data entries from the database
        amazon_obj = self.search([], limit=1)[0]
        mws = MWSConnection(
                            SellerId = amazon_obj.seller_id,
                            aws_access_key_id=amazon_obj.aws_access_key_id,aws_secret_access_key=amazon_obj.secret_key, 
                            host="mws.amazonaws.de"
                            )  
        count = 0
        name_start = 0
        name_end   = 5
        while count <= len(all_sku):
            
            sku = all_sku[name_start:name_end]
            try:
                response = mws.get_matching_product_for_id(
                        MarketplaceId=amazon_obj.market_place_id,
                        IdType='ASIN',
                        IdList=sku)
            except:
                return True
            
            for member in response.GetMatchingProductForIdResult:
                if hasattr(member.Products, 'Product'):
                    if member.Products.Product:
                        asin = member.Products.Product[0].Identifiers.MarketplaceASIN.ASIN
                        vals = {
                                     'amazon_name' : member.Products.Product[0].AttributeSets.ItemAttributes[0].Title
                                     }
                        product_obj = self.env['product.product'].search([('asin','=', asin)], limit=1)
                        if product_obj:
                           product_obj.write(vals)
            
            count = count + 5
            name_start = name_end
            name_end   = name_end + 5
        
        _logger.info('Amazon : Importing Product Name Completed............!!!!!!!!!!!!')
        return True     
    
    @api.multi
    def create_fulfillment_order(self,order_vals):
        print "CREATE FULFILLMENT ORDER METHOD CALLED"
        amazon_obj = self.search([], limit=1)
        if amazon_obj:
            domain = amazon_obj.domain
            user_agent = amazon_obj.user_agent
            secret_key = amazon_obj.secret_key
             
            section='/FulfillmentOutboundShipment/2010-10-01'
            Version='2010-10-01'
     
            data = {
                        'AWSAccessKeyId'  : amazon_obj.aws_access_key_id,
                        'SellerId'        : amazon_obj.seller_id,
                        'SignatureMethod': 'HmacSHA256',
                        'SignatureVersion': '2',
                        'Timestamp': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        'Version': Version,
                         
                        'Action' : 'CreateFulfillmentOrder',
            }
            data.update(order_vals)
            for k, v in data.items():
                if isinstance(v, unicode):
                    data[k] = v.encode('utf-8')
                elif isinstance(v, int):
                    data[k] = str(v)
                elif isinstance(v, float):
                    data[k] = str(v)
                     
            request_description = '&'.join(['%s=%s' % (k, urllib.quote(data[k], safe='-_.~')) for k in sorted(data)])
     
            signature = self.calc_signature(domain, secret_key, request_description, section)
            request = '%s%s?%s&Signature=%s' % (domain, section, request_description, urllib.quote(signature))
            _logger.info(str(request))
            
            try:
                xml = urllib2.urlopen(urllib2.Request(request, headers={'User-Agent': user_agent})).read()
                _logger.info('successssssssssssssss         <<<<<<<<<<<')
            except urllib2.URLError, e:
                _logger.info('errorrrrrrr        '+ str(e.code))
                xml = e.read()
            if 'ErrorResponse' in xml:
                _logger.info('ErrorResponse     ' + str(xml))
                
            return  self.xml_to_dict(xml)    
    
    @api.multi
    def get_customer(self,order, lang):

        def get_country(country_code):
            country_id = self.env['res.country'].search([('code','=',country_code)], limit=1)
            if country_id:
                return country_id.id 
            return False
    
        def get_state(state_name, country_id):
            state_pool = self.env['res.country.state']
            state_id = state_pool.search(['|',('name','ilike',state_name),('code','ilike',state_name)], limit=1)
            if state_id:
                state_id = state_id.id
            elif not country_id:
                return False
            else:
                
                state_id = state_pool.create({'code': state_name, 'name': state_name, 'country_id':country_id})
                state_id = state_id.id
            return state_id

        partner_pool = self.env['res.partner']
        partner_id = False
        if hasattr(order, 'ShippingAddress'):
            country_id = ( hasattr(order.ShippingAddress, 'CountryCode') ) and get_country(order.ShippingAddress.CountryCode) or False
            state_id = ( hasattr(order.ShippingAddress, 'StateOrRegion') ) and get_state(order.ShippingAddress.StateOrRegion, country_id)
            vals = {
                                'street' : hasattr(order.ShippingAddress, 'AddressLine1') and order.ShippingAddress.AddressLine1 or False,
                                'street2': hasattr(order.ShippingAddress, 'AddressLine2') and order.ShippingAddress.AddressLine2 or False,
                                'city'   : hasattr(order.ShippingAddress, 'City')         and order.ShippingAddress.City or False,
                                'name'   : hasattr(order.ShippingAddress, 'Name')         and order.ShippingAddress.Name or False,
                                'phone'  : hasattr(order.ShippingAddress, 'Phone')        and order.ShippingAddress.Phone or False,
                                'zip'    : hasattr(order.ShippingAddress, 'PostalCode')   and order.ShippingAddress.PostalCode or False,
                                'email'  : hasattr(order, 'BuyerEmail')                   and order.BuyerEmail or False,
                                'country_id': country_id,
                                'state_id': state_id,  
                                'lang': lang,
                                'customer_created': order.PurchaseDate
               }
            
            partner_id = partner_pool.search([('email','=',vals['email'])], limit=1)
            if partner_id:
                partner_id = partner_id
            else:
                partner_id = partner_pool.create(vals)
        return partner_id
    
    @api.multi
    def import_order_lines(self, amazon_order_id, order_id):
        request = {'Action': 'ListOrderItems', 'AmazonOrderId' : amazon_order_id}
        bag =  self.make_request(request, section='/Orders/2013-09-01', version='2013-09-01')
        product_pool = self.env['product.product']
        order_pool = self.env['sale.order']
        try:
            OrderItem = bag.ListOrderItemsResponse.ListOrderItemsResult.OrderItems.OrderItem
            if not isinstance(OrderItem, list):
                OrderItem = [OrderItem]
            
            product_uom = self.env['product.uom.categ'].search([('name','=','Unit')], limit=1)
            order_lines = []    
            for orderitem in OrderItem:
                qty_ordered = int(orderitem.QuantityOrdered)
                unit_price = 1.0
                if hasattr(orderitem, 'ItemPrice'):
                    unit_price = orderitem.ItemPrice.Amount
                    if qty_ordered != 0:
                        unit_price = unit_price and (float(unit_price)/qty_ordered) or 1.0
                    currency   = orderitem.ItemPrice.CurrencyCode
                
                product_id = product_pool.search([('default_code','=',orderitem.SellerSKU)],limit=1)
                if not product_id:
                    product_id = product_pool.search([('default_code','=',orderitem.SellerSKU),('active','=',False)])
                
                if not product_id:
                    order_id.write({'is_missing' : True})
                    
                    missing = self.env['sale.line.missing'].search([('sale_id','=',order_id.id),('sku','=',str(orderitem.SellerSKU))])
                    if not missing:
                        self.env['sale.line.missing'].create({'sale_id' : order_id.id, 'name' : orderitem.Title, 'sku' : str(orderitem.SellerSKU),'qty':qty_ordered, 'price_unit' :unit_price})
                    
                    #product_id = product_pool.create(cr, uid, {'name': orderitem.Title, 'asin': orderitem.ASIN, 'default_code': orderitem.SellerSKU, 'type':'product'})
                else:
                    #product_id = product_id and product_id[0] or False
                
                    #product_obj = self.pool.get('product.product').browse(cr, uid, product_id)
                    
                    vals = {
                                            'product_id'        : product_id.id or False,
                                            'name'              : orderitem.Title,
                                            'amazon_id'         : orderitem.OrderItemId,
                                            'product_uom_qty'   : qty_ordered,
                                            'amazon_shipped_qty': orderitem.QuantityShipped,
                                            'price_unit'        : unit_price, 
                                            'product_uom'       : product_uom.id,
                                            'tax_id'            : [[6,False,self.env['account.fiscal.position'].map_tax(product_id.taxes_id).ids]]
                                        }
                    vals['name'] = vals['name'].encode('utf8')
                    order_lines.append(vals)
                            
                #Shipping Product and its Price 
                if hasattr(orderitem, 'ShippingPrice'):
                    ship_amount = float(orderitem.ShippingPrice.Amount)
                    if ship_amount:
                        prod_ship_id = product_pool.search([('name','ilike','Versand')], limit=1)
                        #if prod_ship_id:
                        #    prod_Ship_obj = product_pool.browse(cr, uid, prod_ship_id[0])
                        order_lines.append({
                                        'product_id'         : prod_ship_id and prod_ship_id.id or False,
                                        'name'               : 'Versand ',
                                        'product_uom_qty'    : 1,
                                        'product_uom'        : product_uom.id,
                                        'price_unit'         : ship_amount,
                                        'amazon_id'          : orderitem.OrderItemId + 'SHIPPING',
                                        'tax_id'             : prod_ship_id and [[6,False,self.env['account.fiscal.position'].map_tax(prod_ship_id.taxes_id).ids]] or False
                                    })
                        
                if hasattr(orderitem, 'GiftWrapPrice'):
                    gift_amount = float(orderitem.GiftWrapPrice.Amount)
                    if gift_amount:
                        prod_ship_id = product_pool.search([('default_code','=','gift')], limit=1)
                        #if prod_ship_id:
                        #    prod_Ship_obj = product_pool.browse(cr, uid, prod_ship_id[0])
                        vals = {
                                        'product_id'         : prod_ship_id.id and prod_ship_id.id or False,
                                        'name'               : orderitem.Title,
                                        'product_uom_qty'    : 1,
                                        'price_unit'         : gift_amount,
                                        'product_uom'        : product_uom.id,
                                        'amazon_id'          : orderitem.OrderItemId + 'GIFT',
                                        'tax_id'             : prod_ship_id and [[6,False,self.env['account.fiscal.position'].map_tax(prod_ship_id.taxes_id).ids]] or False
                                        
                                    }
                        vals['name'] = 'GiftWrap of ' + vals['name'].encode('utf8')
                        order_lines.append(vals)
            return order_lines
        
        except:
            return False

            
    @api.model
    def import_order_cron(self, use_new_cursor=False):
        amazon_obj = self.search([], limit=1)[0]
        shopware_obj = self.env['shopware.config'].search([], limit=1)[0]
        pakdo_obj = self.env['pakdo.config'].search([], limit=1)[0]
        presta_obj = self.env['prestashop.config'].search([], limit=1)[0]
        #paypal_obj = self.env['connect.paypal'].search([], limit=1)[0]
        
        try:
            amazon_obj.import_order()
        except:
            _logger.info('Amazon : Erorrrrrrrrrrrrrrrrr      Importing Order started........')
         
        #try:
        #    shopware_obj.import_orders()
            #order_lists = shopware_obj.import_orders()
            #if order_lists:
            #    for order in order_lists:
            #        self.create_pakdo(order)
            #        time.sleep(10)
            
            #shopware_obj.import_betterpayment()
        #except:
        #    pass
        
        try:
            presta_obj.import_order()
        except:
            pass
        
        try:
            pakdo_obj.get_tracking_code()
        except:
            pass
        
        
        
        #try:
        #    paypal_obj.get_all()
        #except:
        #    pass
        
    
    @api.multi
    def create_pakdo(self, order):
        if order:
            _logger.info("Automatic Pakdo order creation startedddddddd   ...............!!!!!!!!!!!!")
            context = dict(self._context or {})
            
            pakdo = self.env['pakdo.config'].search([])
            
            #Push order code
            conn = pakdo.test_connection()[0]
            token = conn[0]
            session = conn[-1]
            print 'token token token      ',token
            headers = {'Authorization': 'Token token='+token}
            
            unixtime_order_date = time.mktime(datetime.strptime(order.order_date, "%Y-%m-%d").timetuple())
            order_data = {"client_order_number":order.name,"date":unixtime_order_date,"payment_date":unixtime_order_date,"gender":"0","firm":False,
                          #"first_name":order.partner_id.name,"last_name":False,
                          #"mail":order.partner_id.email,"country":order.partner_id.country_id.code if order.partner_id.country_id else "DE","city":order.partner_id.city,"zip":order.partner_id.zip,
                          #"street":order.partner_id.street,"street_2": order.partner_id.street2 if order.partner_id.street2 else False,
                          "house_number":False,
                          #"region":order.partner_id.state_id.name if order.partner_id.state_id else '',
                          'separate_picking': ''}
            
            if order.is_ship_differ:
                if order.partner_shipping_id.company_name:
                    order_data['street']  = order.partner_shipping_id.company_name
                    if order.partner_shipping_id.street2:
                        order_data['street_2'] = order.partner_shipping_id.street + ' ' + order.partner_shipping_id.street2
                    else:
                        order_data['street_2'] = order.partner_shipping_id.street
                else:
                    order_data['street']  = order.partner_shipping_id.street
                    order_data['street_2'] =  order.partner_shipping_id.street2 if order.partner_shipping_id.street2 else False
                    
                if order.partner_shipping_id.shopware_company_name:
                    order_data['first_name'] = order.partner_shipping_id.shopware_company_name + ',' + order.partner_shipping_id.name
                else:
                    order_dat['first_name'] = order.partner_shipping_id.name
                    
    
                order_data['city']          = order.partner_shipping_id.city
                order_data['zip']           = order.partner_shipping_id.zip
                order_data['country_id']    = order.partner_shipping_id.country_id.code if order.partner_shipping_id.country_id else "DE"
                order_data['mail']          = order.partner_shipping_id.email and order.partner_shipping_id.email or order.partner_id.email
                order_data['region']        = order.partner_shipping_id.state_id.name if order.partner_shipping_id.state_id else ''
                
            else:
                if order.partner_id.company_name:
                    order_data['street']  = order.partner_id.company_name
                    if order.partner_id.street2:
                        order_data['street_2'] = order.partner_id.street + ' ' + order.partner_id.street2
                    else:
                        order_data['street_2'] = order.partner_id.street
                else:
                    order_data['street']  = order.partner_id.street
                    order_data['street_2'] =  order.partner_id.street2 or ''
                
                if order.partner_id.shopware_company_name:
                    order_data['first_name'] = order.partner_id.shopware_company_name + ',' + order.partner_id.name
                else:
                    order_data['first_name'] = order.partner_id.name
    
                order_data['city']          = order.partner_id.city
                order_data['zip']           = order.partner_id.zip 
                order_data['country_id']    = order.partner_id.country_id.code if order.partner_id.country_id else "DE"
                order_data['mail']          = order.partner_id.email
                order_data['region']        = order.partner_id.state_id.name if order.partner_id.state_id else ''
            
            sku_list = []
            qty_list = []
            price_list = []
            vat_list = []
            line_lists = []
            
            for line in order.order_line:
                if line.product_id.type == 'product':
                    if line.product_id.barcode:
                        resp_product = session.get('https://api.app2.de/v1/products/?gtin[0]='+str(line.product_id.barcode), headers=headers)
                        try:
                            product_dict = json.loads(resp_product.content)
                            if 'id' in product_dict:
                                product_id = product_dict.get('id')[0]
                                qty = product_dict.get('products')[str(product_id)]['quantity']['2']['total_quantity']
                                _logger.info('importing >>>>>>>>>>>>>>>>>>>>>>>>    ' +  str(line.product_id.default_code) + '-' +  str(qty))
                                line.product_id.write({'pakdo_qty': qty,'pakdo':True})
                                self.env.cr.commit()
                        except:
                            _logger.info('Error in Pakdo get product  ' + str(line.product_id.barcode))
                            continue
                        if line.product_id.pakdo_qty < line.product_uom_qty:
                            return False
                            #raise UserError(_(line.product_id.default_code + ' has Qty less.Required Qty ' + str(line.quantity) + ' but Pakdo has qty ' + line.product_id.pakdo_qty))
                        else:
                            sku_list.append(line.product_id.barcode)
                            qty_list.append(line.product_uom_qty)
                            vat_list.append('19')
                            price_list.append(line.price_unit)
                            line_lists.append(line)
                        
            
            order_data.update({"products_sku" : sku_list,"products_quantity" : qty_list, "products_price" : price_list, "products_vat": vat_list})
            try:
                json_order = json.dumps(order_data)
                resp = requests.post('https://api.app2.de/v1/orders/',json_order,headers=headers)
                
                resp_dict = json.loads(resp.content)
                if 'error' in resp_dict:
                    return False
                    #raise UserError(_(resp_dict.get('error')[0]))
                
                for l in line_lists:
                    l.line_id.write({'shipped_type':'pakdo'})
                user = self.env['res.users'].browse(self.env.uid)
                vals = {
                            'body': u'<p><br/>Pakdo Order <b>%s</b> Created <br/> By <b>%s</b> at <b>%s</b></p><br/>' %(order.name ,user.name, datetime.today()), 
                            'model': 'sale.order', 
                            'res_id': order.id, 
                            'subtype_id': False, 
                            'author_id': user.partner_id.id, 
                            'message_type': 'comment', }        
                
                self.env['mail.message'].create(vals)
                self.env.cr.commit()
            except:
                if 'error' in resp_dict:
                    raise UserError(_('Please try after some times, other process in que.....or ' + str(resp_dict.get('error')[0])))
                else:
                    raise UserError(_('Please try after some times, other process in que.....'))
            
            _logger.info('Automatic : Pakdo Push order created successfully........')
        return True
    
    
    @api.multi
    def import_order(self):
        _logger.info('Amazon : Importing Order started........')
        amazon_obj = self.search([], limit=1)[0]

        #pools
        order_pool = self.env['sale.order']
        line_pool  = self.env['sale.order.line']

        # Get Last Update date
        today = datetime.today()
        import_from = datetime.strptime(amazon_obj.import_from, '%Y-%m-%d')

        market_places = {'MarketplaceId.Id.1':amazon_obj.market_place_id}
        pricelist_id = self.env['product.pricelist'].search([('name','=','Public Pricelist')], limit=1)
         
        #m_count = 1

#         for marketplace in amazon_obj.market_place_ids:
#             if marketplace.active and marketplace.shop_id:
#                 market_places['MarketplaceId.Id.'+str(m_count)] = marketplace.amazon_id
#                 mp_map[marketplace.amazon_id] = {'lang': marketplace.shop_lang, 'shop_id': marketplace.shop_id.id, 'pricelist_id': marketplace.shop_id.pricelist_id.id}
#                 m_count += 1

        next_token = False

        while (import_from <= today):
            
            if next_token:
                request = {'Action': 'ListOrdersByNextToken', 'NextToken': next_token}
                bag =  self.make_request(request, section='/Orders/2013-09-01', version='2013-09-01')

                if hasattr(bag, 'ErrorResponse'):
                    raise UserError(_('Error' '%s : %s') % (bag.ErrorResponse.Error.Type, bag.ErrorResponse.Error.Message))

                bag_orders = bag.ListOrdersByNextTokenResponse.ListOrdersByNextTokenResult.Orders

                if hasattr(bag.ListOrdersByNextTokenResponse.ListOrdersByNextTokenResult, 'NextToken'):
                    next_token = bag.ListOrdersByNextTokenResponse.ListOrdersByNextTokenResult.NextToken
                else:
                    next_token = False
                
            else:
                self.env.cr.execute('select max(last_update_date) as last_update_date from sale_order WHERE amazon_id is not null');
                resp = self.env.cr.dictfetchone()
                #resp = {'last_update_date' : '2011-01-01 00:00:00'}
                if resp['last_update_date']:
                    _logger.info('*****************************************      ' + str(resp['last_update_date']))
                    import_from = datetime.strptime(resp['last_update_date'], '%Y-%m-%d %H:%M:%S')
                request = {'Action': 'ListOrders', 'LastUpdatedAfter'   : import_from.strftime('%Y-%m-%dT%H:%M:%SZ'),}
                request.update(market_places)
                bag =  self.make_request(request, section='/Orders/2013-09-01', version='2013-09-01')

                if hasattr(bag, 'ErrorResponse'):
                    raise UserError(_('Error' '%s : %s') % (bag.ErrorResponse.Error.Type, bag.ErrorResponse.Error.Message))
                
                bag_orders = bag.ListOrdersResponse.ListOrdersResult.Orders

                if hasattr(bag.ListOrdersResponse.ListOrdersResult, 'NextToken'):
                    next_token = bag.ListOrdersResponse.ListOrdersResult.NextToken 

            if bag_orders:
                orders = bag_orders.Order
                if not isinstance(orders, list):
                    orders = [orders]

                for order in orders:
                    partner_id = self.get_customer(order, lang='de_DE')
                    if not partner_id:
                        continue

                    order_ids = order_pool.search([('amazon_id','=',order.AmazonOrderId)])
                    if order_ids:
                        order_id = order_ids[0] 
                    else:
                        order_dict = {
                                        'date_order'       : order.PurchaseDate and order.PurchaseDate or False,
                                        'purchase_date'    : order.PurchaseDate and order.PurchaseDate or False,
                                        'date_time'        : order.PurchaseDate and order.PurchaseDate or False,
    
                                        'last_update_date' : order.LastUpdateDate and order.LastUpdateDate or False,
                                        'amazon_id'        : order.AmazonOrderId and order.AmazonOrderId or False,
                                        'name'             : order.AmazonOrderId and order.AmazonOrderId or False,
                                        'f_channel'        : order.FulfillmentChannel and order.FulfillmentChannel or False ,
                                        'sales_channel'    : order.SalesChannel and order.SalesChannel or False,
                                        'ship_serv_level'  : order.ShipServiceLevel and order.ShipServiceLevel or False,
                                        'shipment_service' : order.ShipmentServiceLevelCategory and order.ShipmentServiceLevelCategory or False,
                                        'payment_method'   : hasattr(order, 'PaymentMethod') and order.PaymentMethod or False,
                                        'order_status'     : order.OrderStatus and order.OrderStatus or False,
                                        'unshipped_items'  : order.NumberOfItemsUnshipped and order.NumberOfItemsUnshipped or False,
                                        'shipped_items'    : order.NumberOfItemsShipped and order.NumberOfItemsShipped or False,
                                        'marketplace_id'   : order.MarketplaceId and order.MarketplaceId or False,
                                        'order_total'      :  hasattr(order, 'OrderTotal') and order.OrderTotal.Amount or 0.0,
                                        #'order_policy'     : 'prepaid',
                                        
                                        'partner_id'          : partner_id.id,
                                        'partner_invoice_id'  : partner_id.id,
                                        'partner_shipping_id' : partner_id.id,
                                        'pricelist_id'        : pricelist_id.id,
                                        'is_amazon'           : True
                              }
                        
                        print 'order.AmazonOrderId      ',order.AmazonOrderId
                        #_logger.info('Amazon>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> : ' + str(order.AmazonOrderId))
                        order_id = order_pool.create(order_dict)
                    try:
                        for line in self.import_order_lines(order.AmazonOrderId, order_id):
                            line_ids = line_pool.search([('amazon_id', '=', line['amazon_id'])])
                            if line_ids:
                                pass
                            else:
                                line['order_id'] = order_id.id
                                line['name'] =  unicode(line['name'], 'utf-8')
                                line_id = line_pool.create(line)
                    except:
                        time.sleep(60)
                        for line in self.import_order_lines(order.AmazonOrderId, order_id):
                            line_ids = line_pool.search([('amazon_id', '=', line['amazon_id'])])
                            if line_ids:
                                pass
                            else:
                                line['order_id'] = order_id.id
                                line['name'] =  unicode(line['name'], 'utf-8')
                                line_id = line_pool.create(line)
                        
                            
                    
                    self.env.cr.commit()
                    #order_id.action_done()
                    order_id.process_all()
        _logger.info('Amazon : Importing Order completed........!!!!!!!!!!!!!!!!!!!!!!!')           