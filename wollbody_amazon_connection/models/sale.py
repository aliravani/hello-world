# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
import pytz

import odoo.addons.decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    @api.multi
    def _get_all_messages(self):
        all_ids = []
        for sale in self:
#             for x in sale.message_ids:
#                 all_ids.append(x.id)
            
            if sale.partner_id:
                for x in sale.partner_id.all_message_ids:
                    all_ids.append(x.id)
                    
            sale.all_message_ids = list(set(all_ids))
            sale.all_message_ids = sorted(all_ids, reverse=True)
    
    
    @api.multi
    def _shipped_all_btn(self):
        all_ids = []
        for sale in self:
            ship_list = []
            if sale.transaction_id and sale.payment_method:
                if sale.payment_method == 'Kauf auf Rechnung' and 'betterpaymentcw' in sale.transaction_id:
                    ship_list.append('False')
                
            for line in sale.order_line:
                if line.product_id.type == 'product':
                    if not line.shipped_type:
                        ship_list.append('False')
                    
            if not 'False' in ship_list:
                sale.shipped_all_btn = True
            else:
                sale.shipped_all_btn = False
                
    
    @api.multi
    def _total_price_error(self):
        for sale in self:
            total = 0
            if sale.order_line:
                for line in sale.order_line:
                    if not line.shipped_type and line.product_id.type == 'product':
                        total += line.price_unit
            sale.total_price_error = total

    
    is_amazon               = fields.Boolean('Is Amazon')
    date_time               = fields.Datetime('Date Time')
    purchase_date           = fields.Datetime('Purchase Date')
    last_update_date        = fields.Datetime('Last Update Date')
    amazon_id               = fields.Char('AmazonOrder Id', size=64)
    f_channel               = fields.Char('Full Fillment Channel', size=16)
    sales_channel           = fields.Char('Sales Channel', size=16)
    ship_serv_level         = fields.Char('Ship Service Level', size=16)
    shipment_service        = fields.Char('Ship Service Category', size=16)
    
    #created in shopware module
    #payment_method          = fields.Char('Payment Method', size=64)
    #order_status            = fields.Char('Order Status')
    
    unshipped_items         = fields.Integer('No of items Unshipped')
    shipped_items           = fields.Integer('No of items Shipped')
    marketplace_id          = fields.Char('Marketplace ID', size=16)
    order_total             = fields.Float('Order Total')
    order_type              = fields.Char('Order Type')
    all_message_ids         = fields.One2many('mail.message', compute=_get_all_messages, string='Message', store=False)
    shipped_all_btn         = fields.Boolean(compute=_shipped_all_btn, string='Shipped All button', store=False)
    total_price_error       = fields.Float(compute=_total_price_error, string='Total Price error')
    
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # TDE FIXME: strange
        if self._context.get('shipped_type_not'):
            order_ids = []
            lines = self.env['sale.order.line'].search([('shipped_type','=',False),('state','in',['draft','sent'])])
            if lines:
                for line in lines:
                    if line.product_id.type == 'product':
                        if not line.order_id.id in order_ids:  
                            order_ids.append(line.order_id.id)
            args += [('id', 'in', order_ids)]
                
        return super(SaleOrder, self).search(args, offset=offset, limit=limit, order=order, count=count)
    
    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({
                             
                             'shipping_speed'       :self.shipping_speed,
                             #Shopware part
                            'transaction_id'        : self.transaction_id,
                            'transaction_id2'        : self.transaction_id2,
                            'payment_status'        : self.payment_status,
                            'paypal_email'          : self.paypal_email,
                            'sale_id'               : self.id,
                            'is_shopware'           : self.is_shopware,
                            'shopware_id'           : self.shopware_id,
                            'sw_order_total'        : self.sw_order_total,
                            'payment_description'   : self.payment_description,
                            'fulfillment_order'     : self.fulfillment_order,
                            'fulfillment_status'    : self.fulfillment_status,
                            'pakdo_tracking_code'   : self.pakdo_tracking_code,
                            
                            
        })
        #for shopware
        if self.is_shopware:
            invoice_vals['payment_method'] = self.payment_method
            invoice_vals['date_invoice'] = self.sw_date_time
            
            payment_jouranl_id = self.env['account.journal'].search([('name','=',invoice_vals.get('payment_method'))])
            if payment_jouranl_id:
                invoice_vals['payment_journal_id'] = payment_jouranl_id.id
            else:
                journal_vals = {
                                'name'              : invoice_vals.get('payment_method'),
                                'type'              : 'cash'
                }
                payment_jouranl_id = self.env['account.journal'].create(journal_vals)
                invoice_vals['payment_journal_id'] = payment_jouranl_id.id 

        #for amazon
        if self.is_amazon:
            invoice_vals.update({
                                 #amazon
                                'date_invoice':self.purchase_date,
                                'date_time': self.date_time,
                                'purchase_date': self.purchase_date,
                                'last_update_date': self.last_update_date,
                                'amazon_id': self.amazon_id,
                                'f_channel':self.f_channel,
                                'sales_channel': self.sales_channel,
                                'ship_serv_level':self.ship_serv_level,
                                'shipment_service': self.shipment_service,
                                'payment_method': 'Payment by Amazon',
                                'order_status': self.order_status,
                                'unshipped_items': self.unshipped_items,
                                'shipped_items': self.shipped_items,
                                'marketplace_id': self.marketplace_id,
                                'order_total': self.order_total,
                                'order_type': self.order_type,
                                'is_amazon': True
                                 })
            
            payment_jouranl_id = self.env['account.journal'].search([('name','=','Payment by Amazon')])
            if payment_jouranl_id:
                invoice_vals['payment_journal_id'] = payment_jouranl_id.id
                
        return invoice_vals
    
    @api.multi
    def create_fba(self):
        #create FBA
        
        raw_date = datetime.strptime(self.date_order, "%Y-%m-%d %H:%M:%S").date()
        date_order = raw_date.strftime('%Y-%m-%d')
        order_vals = {
#                        Main
                        'SellerFulfillmentOrderId' : self.name,
                        'ShippingSpeedCategory'    : self.shipping_speed,
                        'DisplayableOrderId'       : self.name,
                        'DisplayableOrderDateTime' : date_order,
                        'DisplayableOrderComment'  : 'Vielen Dank für Ihre Bestellung bei Wollbody.de',
                         
                        'NotificationEmailList.member.1':  '',
                        'NotificationEmailList.member.2':  '',
                      }
        
        if self.is_ship_differ:
#           DestinationAddress
            #if self.partner_shipping_id.company_name:
            #    order_vals['DestinationAddress.Line1'] = self.partner_shipping_id.company_name
            #    if self.partner_shipping_id.street2:
            #        order_vals['DestinationAddress.Line2'] = self.partner_shipping_id.street + ' ' + self.partner_shipping_id.street2
            #    else:
            #         order_vals['DestinationAddress.Line2'] = self.partner_shipping_id.street
            #else:
            
            order_vals['DestinationAddress.Line1'] = self.partner_shipping_id.street
            order_vals['DestinationAddress.Line2'] = self.partner_shipping_id.street2 and self.partner_shipping_id.street2 or ''
            
            if self.partner_shipping_id.shopware_company_name:
                order_vals['DestinationAddress.Name']                   = self.partner_shipping_id.shopware_company_name +','+ self.partner_shipping_id.name
            else:
                order_vals['DestinationAddress.Name']                   = self.partner_shipping_id.name
            #order_vals['DestinationAddress.Line1']                  = street1
            #order_vals['DestinationAddress.Line2']                  = self.partner_shipping_id.street2 and self.partner_shipping_id.street2 or ''
            order_vals['DestinationAddress.City']                   = self.partner_shipping_id.city
            order_vals['DestinationAddress.CountryCode']            = self.partner_shipping_id.country_id.code
            order_vals['DestinationAddress.StateOrProvinceCode']    = self.partner_shipping_id.state_id and self.partner_shipping_id.state_id.code or u'-'
            order_vals['DestinationAddress.PostalCode']             = str(self.partner_shipping_id.zip)        
            
        else:
#           DestinationAddress
            #if self.partner_id.company_name:
            #    order_vals['DestinationAddress.Line1'] = self.partner_id.company_name
            #   if self.partner_shipping_id.street2:
            #        order_vals['DestinationAddress.Line2'] = self.partner_id.street + ' ' + self.partner_id.street2
            #    else:
            #         order_vals['DestinationAddress.Line2'] = self.partner_id.street
            #else:
            
            order_vals['DestinationAddress.Line1'] = self.partner_id.street
            order_vals['DestinationAddress.Line2'] = self.partner_id.street2 and self.partner_id.street2 or ''
            
            if self.partner_id.shopware_company_name:
                order_vals['DestinationAddress.Name']                   = self.partner_id.shopware_company_name +','+self.partner_id.name
            else:
                order_vals['DestinationAddress.Name']                   = self.partner_id.name
            #order_vals['DestinationAddress.Line1']                  = street1
            #order_vals['DestinationAddress.Line2']                  = self.partner_id.street2 and self.partner_id.street2 or ''
            order_vals['DestinationAddress.City']                   = self.partner_id.city
            order_vals['DestinationAddress.CountryCode']            = self.partner_id.country_id.code
            order_vals['DestinationAddress.StateOrProvinceCode']    = self.partner_id.state_id and self.partner_id.state_id.code or u'-'
            order_vals['DestinationAddress.PostalCode']             = str(self.partner_id.zip)
        
        counter = 1
        for line in self.order_line:
            cnt = str(counter)
            if line.product_id.default_code and line.product_id.type != 'service':
                if line.shipped_type != 'fba' and line.shipped_type != 'pakdo':

                    order_vals['Items.member.'+ cnt +'.DisplayableComment']                 = line.product_id.name + '-' + line.product_id.get_size  + '-' + line.product_id.color_name 
                    order_vals['Items.member.'+ cnt +'.GiftMessage']                        = ''
                    order_vals['Items.member.'+ cnt +'.PerUnitDeclaredValue.Value']         = line.product_id.lst_price or 0.0
                    order_vals['Items.member.'+ cnt +'.PerUnitDeclaredValue.CurrencyCode']  = 'EUR'
        #             order_vals['Items.member.'+ cnt +'.FulfillmentNetworkSKU']              = line.product_id.default_code
                    order_vals['Items.member.'+ cnt +'.Quantity']                           = int(line.product_uom_qty)
                    order_vals['Items.member.'+ cnt +'.SellerFulfillmentOrderItemId']       = line.product_id.default_code + '-' + cnt
                    order_vals['Items.member.'+ cnt +'.SellerSKU']                          = line.product_id.default_code
                    counter += 1
                    line.write({'shipped_type': 'fba'})
        
        
        request_resp = self.env['amazon.config'].create_fulfillment_order(order_vals)
        
        if hasattr(request_resp, 'ErrorResponse'):
              if (request_resp.ErrorResponse, 'Error'):
                  error_msg = request_resp.ErrorResponse.Error.Message
                  raise UserError(_(error_msg))
                  
        else:
            self.write({'fulfillment_order': self.name})
            
            user = self.env['res.users'].browse(self.env.uid)
            vals = {
                        'body': u'<p><br/>Fulfillment Order <b>%s</b> Created <br/> By <b>%s</b> at <b>%s</b></p><br/>' %(self.name ,user.name, datetime.today()), 
                        'model': 'sale.order', 
                        'res_id': self.id, 
                        'subtype_id': False, 
                        'author_id': user.partner_id.id, 
                        'message_type': 'comment', }        
           
            self.env['mail.message'].create(vals)
    
    @api.multi
    def _confirm_invoice_delivery_sw_peper(self):
        for order in self:
            if order.is_shopware:
                #confirma and validate and done delivery order
                for picking in order.picking_ids:
                    picking.force_assign()
                    picking.action_done()
                    
                inv_id = order.action_invoice_create(grouped=False, final=False)
                inv = self.env['account.invoice'].browse(inv_id)
                inv.action_invoice_open()
                #send invoice to customer with attach report
                inv.invoice_sent_wlbdy()
                if order.payment_status == 'Komplett bezahlt':
                    journal_obj = self.env['account.journal']
                    journals = journal_obj.search([('name', '=', order.payment_method)])
                    if not journals:
                        journal_vals = {
                                'name'          : order.payment_method,
                                'type'          : 'cash',
                            }
                        journals = journal_obj.create(journal_vals)
                    
                    payment_type = self.env['account.payment.method'].search([('payment_type','=','inbound'),('code','=','manual')])
                    payment_dict = {
                                    'payment_type'          : 'inbound',
                                    'partner_type'          : 'customer',
                                    'invoice_ids'           : [(6,0,inv_id)],
                                    'partner_id'            : order.partner_id.id,
                                    'journal_id'            : journals.id,
                                    'payment_date'          : order.date_order,
                                    'communication'         : order.name,
                                    'amount'                : order.sw_order_total,
                                    'payment_method_id'     : payment_type.id,
                    }
                    
                    #try:
                    payment_id = self.env['account.payment'].create(payment_dict)
                    payment_id.post()
                    inv.action_invoice_paid()
                
                
                    
    @api.multi
    def _confirm_invoice_delivery_sw(self):
        for order in self:
            if order.is_shopware:
                #confirma and validate and done delivery order
                for picking in order.picking_ids:
                    picking.force_assign()
                    picking.action_done()
                    
                inv_id = order.action_invoice_create(grouped=False, final=False)
                inv = self.env['account.invoice'].browse(inv_id)
                inv.action_invoice_open()
                #send invoice to customer with attach report
                inv.invoice_sent_wlbdy()
                
                if order.payment_status == 'Komplett bezahlt':
                    journal_obj = self.env['account.journal']
                    journals = journal_obj.search([('name', '=', order.payment_method)])
                    if not journals:
                        journal_vals = {
                                'name'          : order.payment_method,
                                'type'          : 'cash',
                            }
                        journals = journal_obj.create(journal_vals)
                    
                    payment_type = self.env['account.payment.method'].search([('payment_type','=','inbound'),('code','=','manual')])
                    payment_dict = {
                                    'payment_type'          : 'inbound',
                                    'partner_type'          : 'customer',
                                    'invoice_ids'           : [(6,0,inv_id)],
                                    'partner_id'            : order.partner_id.id,
                                    'journal_id'            : journals.id,
                                    'payment_date'          : order.date_order,
                                    'communication'         : order.name,
                                    'amount'                : order.sw_order_total,
                                    'payment_method_id'     : payment_type.id,
                    }
                    
                    #try:
                    payment_id = self.env['account.payment'].create(payment_dict)
                    payment_id.post()
                    inv.action_invoice_paid()
                    #except:
                    #    continue
                    
                    
                
    
    @api.multi
    def _confirm_invoice_delivery(self):
        for order in self:
            if order.amazon_id:
                #confirma and validate and done delivery order
                for picking in order.picking_ids:
                    picking.force_assign()
                    picking.action_done()
                    
                amazon_id = self.env['account.invoice'].search([('amazon_id', '=', order.amazon_id)])
                if not amazon_id:
                    inv_id = order.action_invoice_create(grouped=False, final=False)
                    inv = self.env['account.invoice'].browse(inv_id)
                    inv.action_invoice_open()
                    inv.invoice_sent()
                    journals = self.env['account.journal'].search([('name', '=', 'Payment by Amazon')])
                    if journals:
                        account_id = self.env['account.journal'].browse(journals.id).default_credit_account_id.id
                    
                    payment_type = self.env['account.payment.method'].search([('code','=','manual'),('payment_type','=','inbound')])
                    payment_dict = {
                                    'payment_type'          : 'inbound',
                                    'partner_type'          : 'customer',
                                    'invoice_ids'           : [(6,0,inv_id)],
                                    'partner_id'            : order.partner_id.id,
                                    'journal_id'            : journals.id,
                                    'payment_date'          : order.date_order,
                                    'communication'         : order.name,
                                    'amount'                : order.order_total,
                                    'payment_method_id'     : payment_type.id,
                    }
                    try:
                        payment_id = self.env['account.payment'].create(payment_dict)
                        payment_id.post()
                    except:
                        continue
                    
                                 
    @api.multi
    def process_all(self):
        for order in self:
            if order.is_shopware:
                if not order.is_missing:
                    self.action_confirm()
                    #order.create_fba()
                    order._confirm_invoice_delivery_sw()
                    return order.action_view_invoice()
            if order.is_amazon:
                if not order.is_missing:
                    self.action_confirm()
                    self._confirm_invoice_delivery()
                    return order.action_view_invoice()
                    
    @api.multi
    def transfer_to_order_line(self):
        for miss in self.missing_ids:
            if not miss.transfer:
                product_pool = self.env['product.product']
                product_id = product_pool.search([('default_code','=',miss.sku)])
                product_uom = self.env['product.uom'].search([('name', '=', 'Unit(s)')])
                if product_id:
                    name = product_id.name_get()[0][1]
                    
                    product_obj = product_pool.browse(product_id[0].id)
                    vals = {
                            'product_id'        : product_obj[0].id,
                            'product_uom_qty'   : miss.qty,
                            'order_id'          : self.id,
                            'price_unit'        : miss.price_unit,
                            'product_uom'       : product_uom[0].id,
                            'name'              : name,
                            'tax_id'            : [(6, 0, [x.id for x in product_obj[0].taxes_id])] 
                            }
                    miss.write({'transfer' : True})
                    line_id = self.env['sale.order.line'].create(vals)
                    
        
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    amazon_id             = fields.Char('OrderItemId', size=64)
    amazon_shipped_qty    = fields.Integer('Shipped Quantity')
    qty_on_hand           = fields.Integer(string='Qty On Hand',related='product_id.total_child_qty')
    
    order_date            = fields.Datetime(string='Order Date', related='order_id.date_order')
    amazon_fee            = fields.Float('FulfillmentFee')
    amazon_commission     = fields.Float('Commission')
    
    fba_qty               = fields.Integer('FBA Qty', related="product_id.fba_qty")
    wlbdy_qty             = fields.Integer('WLBDY Qty',related="product_id.wlbdy_qty")
    pakdo_qty             = fields.Integer('PAKDO Qty', related="product_id.pakdo_qty")
    shipped_type          = fields.Selection([('fba','FBA'),('pakdo','PakDo')], string='Shipped Type')
    
    
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # TDE FIXME: strange
        today = datetime.now()
        if self._context.get('day_30'):
            
            day_30  = datetime.now() - timedelta(30)
            
            tz_name = 'Europe/Berlin'
            utc             = pytz.timezone('UTC')
            context_tz      = pytz.timezone(tz_name)
            local_timestamp_today = utc.localize(today, is_dst=False)
            local_timestamp_day_30 = utc.localize(day_30, is_dst=False)
            user_datetime_today   = local_timestamp_today.astimezone(context_tz)
            user_datetime_day_30   = local_timestamp_day_30.astimezone(context_tz)
            
            start_date = user_datetime_today.strftime("%m/%d/%Y 00:00:00")
            end_date = user_datetime_day_30.strftime("%m/%d/%Y 23:59:59")
            args = []
            args.append(('product_id', '=', self._context.get('search_default_product_id')[0]))
            args.append(('order_date', '<=', start_date))
            args.append(('order_date', '>=', end_date))
            args.append(('state', 'in', ['sale', 'done']))
            
        
        if self._context.get('day_365'):
            day_30  = datetime.now() - timedelta(365)
            
            tz_name = 'Europe/Berlin'
            utc             = pytz.timezone('UTC')
            context_tz      = pytz.timezone(tz_name)
            local_timestamp_today = utc.localize(today, is_dst=False)
            local_timestamp_day_30 = utc.localize(day_30, is_dst=False)
            user_datetime_today   = local_timestamp_today.astimezone(context_tz)
            user_datetime_day_30   = local_timestamp_day_30.astimezone(context_tz)
            
            start_date = user_datetime_today.strftime("%m/%d/%Y 00:00:00")
            end_date = user_datetime_day_30.strftime("%m/%d/%Y 23:59:59")
            args = []
            args.append(('product_id', '=', self._context.get('search_default_product_id')[0]))
            args.append(('order_date', '<=', start_date))
            args.append(('order_date', '>=', end_date))
            args.append(('state', 'in', ['sale', 'done']))
            
        
        if self._context.get('day_365_30'):
            day_30  = datetime.now() - timedelta(365)
            day_30_next = day_30 + timedelta(30)
            
            tz_name = 'Europe/Berlin'
            utc             = pytz.timezone('UTC')
            context_tz      = pytz.timezone(tz_name)
            local_timestamp_day_30_next = utc.localize(day_30_next, is_dst=False)
            local_timestamp_day_30 = utc.localize(day_30, is_dst=False)
            user_datetime_day_30_next   = local_timestamp_day_30_next.astimezone(context_tz)
            user_datetime_day_30   = local_timestamp_day_30.astimezone(context_tz)
            
            start_date = user_datetime_day_30_next.strftime("%m/%d/%Y 00:00:00")
            end_date = user_datetime_day_30.strftime("%m/%d/%Y 23:59:59")
            args = []
            args.append(('product_id', '=', self._context.get('search_default_product_id')[0]))
            args.append(('order_date', '<=', start_date))
            args.append(('order_date', '>=', end_date))
            args.append(('state', 'in', ['sale', 'done']))
            
        
        return super(SaleOrderLine, self).search(args, offset=offset, limit=limit, order=order, count=count)
    
    
    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )
        name = ''
        if product.related_supplier_id:
            name = product.related_supplier_id.name + ' '

        name += product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(self._get_display_price(product), product.taxes_id, self.tax_id)
        self.update(vals)

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            if product.sale_line_warn == 'block':
                self.product_id = False
            return {'warning': warning}
        return {'domain': domain}