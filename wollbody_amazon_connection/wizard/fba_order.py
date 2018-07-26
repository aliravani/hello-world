# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
from openerp import models, api,exceptions, fields, _
from openerp.exceptions import Warning
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError, UserError, except_orm
import logging
_logger = logging.getLogger(__name__)


class FBAOrderLine(models.TransientModel):
    _name = "fba.order.line"
    
    fba_order_id  = fields.Many2one('fba.order')
    product_id    = fields.Many2one('product.product', 'Product/SKU')
    name          = fields.Char('Comment')
    quantity      = fields.Integer('Quantity')
    price         = fields.Float('Price')
    line_id       = fields.Many2one('sale.order.line','Sale Lines')
        

class FBAOrder(models.TransientModel):
    _name = "fba.order"
    
    @api.model
    def _get_line(self):
        res = []
        context = dict(self._context or {})
        if context.get('active_id'):
            sale = self.env['sale.order'].browse(context.get('active_id'))
            line_list = []
            for line in sale.order_line:
                if line.product_id.default_code and line.product_id.type == 'product':
                    if line.shipped_type != 'fba' and line.shipped_type != 'pakdo':
                        line_vals = {'product_id':line.product_id.id, 'quantity': line.product_uom_qty, 'name': line.name, 'price' : line.price_unit, 'line_id':line.id }
                        res.append(line_vals)
        return res
        
    
    name            = fields.Char('Fulfillment Order #')
    comment         = fields.Char('Comment')
    
    order_date      = fields.Date('Order Date')
    
    customer_name   = fields.Char('Customer Name')
    street1         = fields.Char('Street 1')
    street2         = fields.Char('Street 2')
    city            = fields.Char('City')
    zip             = fields.Char('ZIP')
    country_id      = fields.Many2one('res.country', 'Country')
    state_id        = fields.Many2one('res.country.state', 'State')
    
    line_ids        = fields.One2many('fba.order.line', 'fba_order_id', 'Lines', default=_get_line)
    
    notification_email1 = fields.Char('Notify Email 1')
    notification_email2 = fields.Char('Notify Email 2')
    shipping_speed  = fields.Selection([('Standard','Standard'),('Expedited','Expedited'),('Priority','Priority')], 'Shipping Speed')
    
    @api.model
    def default_get(self, fields):
        resp = super(FBAOrder, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        sale = self.env['sale.order'].browse(context.get('active_id'))
        
        resp['name'] = sale.name
        resp['shipping_speed'] = sale.shipping_speed
        resp['comment'] = "Vielen Dank für Ihre Bestellung bei Wollbody.de"
        resp['order_date'] = sale.date_order
        
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
        
        if not sale.partner_id.state_id:
            state = self.env['res.country.state'].search([('name','=','-')], limit=1)
            if state:
                resp['state_id'] = state.id
        else:
            resp['state_id'] = sale.partner_id.state_id and sale.partner_id.state_id.id

        return resp
    
    @api.multi
    def create_fulfillment_order(self):
        context = dict(self._context or {})
        sale = self.env['sale.order'].browse(context.get('active_id'))
        order_vals = {
#                        Main
                        'SellerFulfillmentOrderId' : self.name,
                        'ShippingSpeedCategory'    : self.shipping_speed,
                        'DisplayableOrderId'       : self.name,
                        'DisplayableOrderDateTime' : self.order_date,
                        'DisplayableOrderComment'  : self.comment,
                          
#                        DestinationAddress
                        'DestinationAddress.Name'                : self.customer_name, 
                        #'DestinationAddress.Line1'               : self.street1,
                        #'DestinationAddress.Line2'               : self.street2 and self.street2 or '',
                        #'DestinationAddress.City'                : self.city or '',
                        'DestinationAddress.CountryCode'         : self.country_id.code,
                        'DestinationAddress.StateOrProvinceCode' : self.state_id and self.state_id.code or False,
                        'DestinationAddress.PostalCode'          : self.zip,
                           
                        'NotificationEmailList.member.1': self.notification_email1 and self.notification_email1 or '',
                        'NotificationEmailList.member.2': self.notification_email2 and self.notification_email2 or '',
                      }
        
        if self.street1:
            #street1  = unicode(self.street1, "utf-8")
            order_vals.update({
                               'DestinationAddress.Line1'               : self.street1.encode("utf-8")
                               })
        if self.street2:
            #street2 = unicode(self.street2, "utf-8")
            order_vals.update({
                               'DestinationAddress.Line2'               : self.street2.encode("utf-8")
                               })
        
        if self.city:
            order_vals.update({
                               'DestinationAddress.City'               : self.city.encode("utf-8")
                               })
       
        counter = 1
        for line in self.line_ids:
            cnt = str(counter)
              
#            item
            order_vals['Items.member.'+ cnt +'.DisplayableComment']                 = line.product_id.name + '-' + line.product_id.get_size + '-' + line.product_id.color_name
            order_vals['Items.member.'+ cnt +'.GiftMessage']                        = ''
            order_vals['Items.member.'+ cnt +'.PerUnitDeclaredValue.Value']         = line.product_id.lst_price or 0.0
            order_vals['Items.member.'+ cnt +'.PerUnitDeclaredValue.CurrencyCode']  = 'EUR'
#             order_vals['Items.member.'+ cnt +'.FulfillmentNetworkSKU']              = line.product_id.default_code
            order_vals['Items.member.'+ cnt +'.Quantity']                           = line.quantity
            order_vals['Items.member.'+ cnt +'.SellerFulfillmentOrderItemId']       = line.product_id.default_code + '-' + cnt
            order_vals['Items.member.'+ cnt +'.SellerSKU']                          = line.product_id.default_code
            counter += 1
            line.line_id.write({'shipped_type':'fba'})
        
        _logger.info(str(order_vals))
        amazon = self.env['amazon.config'].search([],limit=1)
        request_resp = amazon.create_fulfillment_order(order_vals)
        _logger.info("Amazon FBA>>>>>>>>>>>      " + str(request_resp))
         
        if hasattr(request_resp, 'ErrorResponse'):
              if (request_resp.ErrorResponse, 'Error'):
                  error_msg = request_resp.ErrorResponse.Error.Message
                  _logger.info(str(error_msg))
                  raise UserError(_('Error' + error_msg ))
                  
        else:
            sale.write({'fulfillment_order': self.name})
            
            user = self.env['res.users'].browse(self.env.uid)
            vals = {
                        'body': u'<p><br/>Fulfillment Order <b>%s</b> Created <br/> By <b>%s</b> at <b>%s</b></p><br/>' %(self.name ,user.name, datetime.today()), 
                        'model': 'sale.order', 
                        'res_id': context.get('active_id'), 
                        'subtype_id': False, 
                        'author_id': user.partner_id.id, 
                        'message_type': 'comment', }        
           
            self.env['mail.message'].create(vals)
             
            #delivery state changes to ready to transferred
            if sale.picking_ids:
                 for pick in sale.picking_ids:
                     pick.force_assign()
                     pick.action_done()
             
            _logger.info('Amazon FBA created successfully........')
        return True