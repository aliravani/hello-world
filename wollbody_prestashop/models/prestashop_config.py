# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError, except_orm
from datetime import datetime, date, timedelta
import time
import io
from prestapyt import PrestaShopWebServiceDict
import tempfile
#from prestapyt.dict2xml import prestashop

import logging
_logger = logging.getLogger(__name__)

class PrestashopConfig(models.Model):
    _name = 'prestashop.config'
    
    name              = fields.Char('Name', default='Wollbody-Prestashop')
    url               = fields.Char('Host API Url', default='http://prestashop.wollbody.de')
    shop_url          = fields.Char('Shop URL')
    api_key           = fields.Char('API Key',)
    state             = fields.Selection([('draft','Draft'),('connected','Connection Success'),('error','Error')], 'State', default='draft', readonly=True)
    export_stock_error = fields.Text('Export stock Error')
    
    @api.multi
    def refresh_tmpl(self):
        tmpls = self.env['product.template'].search([])
        if tmpls:
            for tmpl in tmpls:
                tmpl._get_color()
                
    @api.multi
    def sw_to_presta(self):
        tmpls = self.env['product.template'].search([])
        if tmpls:
            for tmpl in tmpls:
                tmpl_vals = {
                    'presta_meta_title_english'         : tmpl.meta_title_en,
                    'presta_meta_title_german'          : tmpl.meta_title_de,             
                    'presta_meta_description_english'   : tmpl.meta_description_en,
                    'presta_meta_description_german'    : tmpl.meta_description_de,       
                    'presta_meta_keywords_english'      : tmpl.meta_keyword_en,           
                    'presta_meta_keywords_german'       : tmpl.meta_keyword_de,
                    'presta_description_german'         : tmpl.shopware_description,
                    'presta_description_english'        : tmpl.shopware_description_en,
                    'presta_description_short_english'  : tmpl.meta_description_en,
                    'presta_description_short_german'   : tmpl.meta_description_de,           
                }
                tmpl.write(tmpl_vals)
    
    @api.multi
    def clear_presta(self):
        tmpls = self.env['product.template'].search([])
        if tmpls:
            for tmpl in tmpls:
                tmpl_vals = {
                    'presta_id'         : 0,
                    'presta_link'       : False,
                    'presta_image_id'   : 0             
                }
                tmpl.write(tmpl_vals)
        
        products = self.env['product.product'].search([])
        if products:
            for product in products:
                product_vals = {
                    'presta_child_id'         : 0,
                }
                product.write(product_vals)
                
    @api.one
    def test_connection(self):
        for presta in self:
            prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
            #try:
            resp = prestashop.head('')
            return self.write({'state':'connected'})
            #except:
            #    return self.write({'state':'error'})
    
    @api.multi
    def reset(self):
        return self.write({'state':'draft'})
    
    @api.multi
    def import_category(self):
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                categories_1 = prestashop.get('categories')
                print 'categories_1 categories_1     ',categories_1
 
                prestashop_category_list = []
                for cat in categories_1['categories']['category']:
                    prestashop_category_list.append(cat['attrs'].get('id'))
                 
                 
                # 1 = german 0
                # 2 = english 1
                for category in prestashop_category_list:
                    category_resp = prestashop.get('categories',category)
                    #print 'category_resp category_resp      ',category_resp
                     
                    prestashop_id = category_resp['category']['id']
                    print 'prestashop_id prestashop_id prestashop_id        ',prestashop_id
                    
                    prestashop_parent_id = category_resp['category']['id_parent']
                     
                    name_german = category_resp['category']['name']['language'][0]['value']
                    name = category_resp['category']['name']['language'][1]['value']
                     
                    meta_description_german = category_resp['category']['meta_description']['language'][0]['value']
                    meta_description = category_resp['category']['meta_description']['language'][1]['value']
                     
                     
                    meta_keywords_german = category_resp['category']['meta_keywords']['language'][0]['value']
                    meta_keywords = category_resp['category']['meta_keywords']['language'][1]['value']
                     
                    meta_title_german = category_resp['category']['meta_title']['language'][0]['value']
                    meta_title = category_resp['category']['meta_title']['language'][1]['value']
                    
                     
                    odoo_categorys = self.env['prestashop.category'].search([('prestashop_id','=',prestashop_id)])
                     
                    values = {
                            'prestashop_id'             : prestashop_id,
                            'prestashop_parent_id'      : prestashop_parent_id,
                            'name'                      : name,
                            'name_german'               : name_german,
                            'meta_description_german'   : meta_description_german,
                            'meta_description'          : meta_description,
                            'meta_keywords_german'      : meta_keywords_german,
                            'meta_keywords'             : meta_keywords,
                            'meta_title_german'         : meta_title_german,
                            'meta_title'                : meta_title,
                            'is_german'                 : True
                    }
                     
                    parent_id = self.env['prestashop.category'].search([('prestashop_id','=',prestashop_parent_id)])
                    if parent_id:
                        values.update({'parent_id' : parent_id.id})
                     
                    if not odoo_categorys:
                        odoo_category = self.env['prestashop.category'].create(values)
                    else:
                        odoo_categorys.write(values)
                
                
#                 prestashop_category_list_2 = []
#                 categories_2 = prestashop.get('categories',options={'id_shop': 2})
#                 for cat in categories_2['categories']['category']:
#                     prestashop_category_list_2.append(cat['attrs'].get('id'))
#                  
#                  
#                 for category in prestashop_category_list_2:
#                     category_resp_2 = prestashop.get('categories',category, options={'id_shop': 2})
#                      
#                     prestashop_id = category_resp_2['category']['id']
#                      
#                     prestashop_parent_id = category_resp_2['category']['id_parent']
#                      
#                     name_german = category_resp_2['category']['name']['language'][0]['value']
#                     name = category_resp_2['category']['name']['language'][1]['value']
#                      
#                     meta_description_german = category_resp_2['category']['meta_description']['language'][0]['value']
#                     meta_description = category_resp_2['category']['meta_description']['language'][1]['value']
#                      
#                      
#                     meta_keywords_german = category_resp_2['category']['meta_keywords']['language'][0]['value']
#                     meta_keywords = category_resp_2['category']['meta_keywords']['language'][1]['value']
#                      
#                     meta_title_german = category_resp_2['category']['meta_title']['language'][0]['value']
#                     meta_title = category_resp_2['category']['meta_title']['language'][1]['value']
#                      
#                     odoo_categorys_2 = self.env['prestashop.category'].search([('prestashop_id','=',prestashop_id)])
#                      
#                     values = {
#                             'prestashop_id'             : prestashop_id,
#                             'prestashop_parent_id'      : prestashop_parent_id,
#                             'name'                      : name,
#                             'name_german'               : name_german,
#                             'meta_description_german'   : meta_description_german,
#                             'meta_description'          : meta_description,
#                             'meta_keywords_german'      : meta_keywords_german,
#                             'meta_keywords'             : meta_keywords,
#                             'meta_title_german'         : meta_title_german,
#                             'meta_title'                : meta_title,
#                             'is_english'                : True
#                     }
#                     parent_id = self.env['prestashop.category'].search([('prestashop_id','=',prestashop_parent_id)])
#                     if parent_id:
#                         values.update({'parent_id' : parent_id.id})
#                      
#                     if not odoo_categorys_2:
#                         odoo_category_2 = self.env['prestashop.category'].create(values)
#                     else:
#                         odoo_categorys_2.write(values)
                        
    @api.multi
    def import_product(self):
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                product_1 = prestashop.get('products')
                
                prestashop_product_list = []
                for prod in product_1['products']['product']:
                    prestashop_product_list.append(prod['attrs'].get('id'))
                
                prestashop_product_list = [29]
                for product in prestashop_product_list:
                    product_resp = prestashop.get('products',product)
                    print 'product_resp product_resp     ',product_resp
                    print '*********************************************************************'
                    product_dict = product_resp.get('product')
                    # 0 german 1 english
                    tmpl_vals = {
                                    'presta_additional_shipping_cost'   : product_dict.get('additional_shipping_cost'),
                                    'presta_categories'                 : product_dict.get('condition'),
                                    'presta_description_german'         : product_dict['description']['language'][0]['value'],
                                    'presta_description_english'        : product_dict['description']['language'][1]['value'],
                                    
                                    'presta_description_short_english'  : product_dict['description_short']['language'][1]['value'],
                                    'presta_description_short_german'   : product_dict['description_short']['language'][0]['value'],
                                    'presta_id'                         : product_dict.get('id'),
                                    'presta_manufacturer_name'          : product_dict['manufacturer_name'].get('value') or '',
                                    'presta_meta_description_english'   : product_dict['meta_description']['language'][1]['value'],
                                    'presta_meta_description_german'    : product_dict['meta_description']['language'][0]['value'],
                                    'presta_meta_keywords_english'      : product_dict['meta_keywords']['language'][1]['value'],
                                    'presta_meta_keywords_german'       : product_dict['meta_keywords']['language'][0]['value'],
                                    
                                    'presta_meta_title_english'         : product_dict['meta_title']['language'][1]['value'],
                                    'presta_meta_title_german'          : product_dict['meta_title']['language'][0]['value'],
                                    
                                    'presta_name_english'               : product_dict['name']['language'][1]['value'],
                                    'presta_name_german'                : product_dict['name']['language'][0]['value'],
                    }
                    
                    #categorys
                    category_list = []
                    if product_dict['associations']['categories']['category']:
                        if isinstance(product_dict['associations']['categories']['category'], list):
                            api_category_list = product_dict['associations']['categories']['category']
                        else:
                            api_category_list = [product_dict['associations']['categories']['category']]
                        
                        for category in api_category_list:
                            odoo_category = self.env['prestashop.category'].search([('prestashop_id','=',category.get('id'))])
                            if odoo_category:
                                category_list.append(odoo_category.id)
                    
                    if category_list:
                        tmpl_vals.update({'presta_categories': [(6,0,category_list)]})
                    
                    feature_list = []
                    if product_dict['associations']['product_features'].get('product_feature'):
                        if isinstance(product_dict['associations']['product_features']['product_feature'], list):
                            api_feature_list = product_dict['associations']['product_features']['product_feature']
                        else:
                            api_feature_list = [product_dict['associations']['product_features']['product_feature']]
                        
                        for feature in api_feature_list:
                            if feature.get('id_feature_value'):
                                odoo_feature = self.env['prestashop.feature'].search([('prestashop_value_id','=',feature.get('id_feature_value'))])
                            if not feature.get('id_feature_value'):
                                odoo_feature = self.env['prestashop.feature'].search([('prestashop_id','=',feature.get('id'))])
                            if odoo_feature:
                                feature_list.append(odoo_feature.id)
                    
                    if feature_list:
                        tmpl_vals.update({'presta_feature': [(6,0,feature_list)]})
                    
                    product_obj = False
                    if product_resp['product']['associations']['combinations'].get('combination'):
                        for combination in product_resp['product']['associations']['combinations']['combination']:
                            if combination.get('id'):
                                combination_resp = prestashop.get('combinations',combination.get('id'))
                                child_dict = combination_resp['combination']
                                print 'child_dict child_dict     ',child_dict
                                
                                products = self.env['product.product'].search([('default_code','=', child_dict.get('reference'))], limit=1)
                                if products:
                                    child_vals = {
                                                'presta_child_id'   : child_dict.get('id'),
                                                'presta_price'      : child_dict.get('price'),
                                    }
                                    products.write(child_vals)
                                    product_obj = products
                    
                    if product_obj:
                        product_obj.product_tmpl_id.write(tmpl_vals)
                
        
        return True
    
    @api.multi
    def import_product_child_id(self):
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                product_1 = prestashop.get('products')
                
                prestashop_product_list = []
                for prod in product_1['products']['product']:
                    prestashop_product_list.append(prod['attrs'].get('id'))
                
                for product in prestashop_product_list:
                    product_resp = prestashop.get('products',product)
                    product_dict = product_resp.get('product')
                    
                    product_obj = False
                    if product_resp['product']['associations']['combinations'].get('combination'):
                        for combination in product_resp['product']['associations']['combinations']['combination']:
                            if combination.get('id'):
                                combination_resp = prestashop.get('combinations',combination.get('id'))
                                child_dict = combination_resp['combination']
                                
                                products = self.env['product.product'].search([('default_code','=', child_dict.get('reference'))], limit=1)
                                if products:
                                    child_vals = {'presta_child_id'   : child_dict.get('id')}
                                    products.write(child_vals)
                                    product_obj = products
        return True
    
    @api.multi
    def export_material(self):
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                
                materials = self.env['article.material'].search([('presta_id','=',False)])
                for material in materials:
                    
                    
                    material_dict = {'product_feature_value': 
                                     {'id_feature': '1', 
                                      'value': {'language': [{'attrs': {'id': '1'}, 'value': material.name}, {'attrs': {'id': '2'}, 'value': material.english_name or material.name}]},
                                       'custom': '0'}}
                    
                    product_feature_resp = prestashop.add('product_feature_values',material_dict)
                    
                    material.write({'presta_id': product_feature_resp['prestashop']['product_feature_value'].get('id'), 'presta_material_id': product_feature_resp['prestashop']['product_feature_value'].get('id_feature')})
    
    @api.multi
    def import_product_features(self):
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                product_features_1 = prestashop.get('product_features')
                
                
                product_feature_values = prestashop.get('product_feature_values')
                
                
                prestashop_feature_list = []
                for feature in product_features_1['product_features']['product_feature']:
                    prestashop_feature_list.append(feature['attrs'].get('id'))
                 
                 
                for product in prestashop_feature_list:
                    product_resp = prestashop.get('product_features',product)
                    
                    val = {
                            'name_german'      : product_resp['product_feature']['name']['language'][0]['value'],
                            'name'             : product_resp['product_feature']['name']['language'][1]['value'],
                            'prestashop_id'    : product_resp['product_feature']['id'],
                    }
                    features = self.env['prestashop.feature'].search([('prestashop_id','=',product_resp['product_feature']['id']),('name','=',product_resp['product_feature']['name']['language'][1]['value'])], limit=1)
                    if not features:
                        features = self.env['prestashop.feature'].create(val)
                    else:
                        features.write(val)
                        
                    
                    
                    #feature_id = product_resp['product_feature']['id']
                
                
                
                
                #features values importing.................
                
                product_feature_values_list = []
                for values in product_feature_values['product_feature_values']['product_feature_value']:
                     
                    product_feature_values_list.append(values['attrs'].get('id'))
                 
                for feature_value in product_feature_values_list:
                    feature_value_resp = prestashop.get('product_feature_values',feature_value)
                    parent_id = feature_value_resp['product_feature_value']['id_feature']
                    
                    values = {
                            'name_german'       : feature_value_resp['product_feature_value']['value']['language'][0]['value'],
                            'name'              : feature_value_resp['product_feature_value']['value']['language'][1]['value'],
                            'prestashop_value_id'     : feature_value_resp['product_feature_value']['id'],
                    }
                    
                    features_parent = self.env['prestashop.feature'].search([('prestashop_id','=',parent_id)])
                    print 'features_parent features_parent   ',features_parent
                    if features_parent:
                        values.update({'parent_id':features_parent.id})
                    
                    features = self.env['prestashop.feature'].search([('prestashop_value_id','=',feature_value_resp['product_feature_value']['id']),('name','=',feature_value_resp['product_feature_value']['value']['language'][1]['value'])], limit=1)
                    if not features:
                        self.env['prestashop.feature'].create(values)
                    else:
                        features.write(values)
                    
                    
                 
                     

                    
                        
                
        
        return True
    
    @api.multi
    def import_brand_supplier(self):
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                suppliers = prestashop.get('manufacturers')
                supplier_list = []
                for sup in suppliers['manufacturers']['manufacturer']:
                    supplier_list.append(sup['attrs'].get('id'))
                
                for supplier in supplier_list:
                    supplier_resp = prestashop.get('manufacturers',supplier)
                    if supplier_resp['manufacturer'].get('id'):
                        partner = self.env['res.partner'].search([('name','ilike',supplier_resp['manufacturer']['name']),('supplier','=',True)])
                        if partner:
                            partner.write({'presta_supplier_id': supplier_resp['manufacturer']['id']})
    
    @api.multi
    def import_product_stock(self):
        _logger.info("Prestashop Importing stock    ..............." )
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                stock_available = prestashop.get('stock_availables')
                
                stock_lists = []
                for stock_id in stock_available['stock_availables']['stock_available']:
                    stock_lists.append(stock_id['attrs'].get('id'))
                for stock in stock_lists:
                    stock = prestashop.get('stock_availables',stock)
                    print 'stock stock     ',stock
                    product_presta_id = stock['stock_available']['id_product_attribute']
                    qty               = stock['stock_available']['quantity']
                    products = self.env['pakdo.presta.stock'].search([('presta_child_id','=',product_presta_id)])
                    if products:
                        products.write({'presta_stock_id': stock['stock_available']['id']})
        
        return True
    
    @api.multi
    def export_product_stock(self):
        _logger.info("Prestashop Exporting stock function called   ..............." )
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                products = self.env['product.product'].search([('presta_child_id','!=',0)])
                #products = self.env['product.product'].search([('id','=',12575)])
                
                #self.import_product_child_id()
                self.import_product_stock()
                
                _logger.info("Prestashop Exporting stock    ..............." )
                
                print 'products  ',products
                error_data = ''
                for product in products:
                    if product.presta_child_id and product.product_tmpl_id.presta_id:
                        stock_vals = {'stock_available': {'depends_on_stock': '0',
                                          'id': product.presta_stock_id,
                                          'id_product': product.product_tmpl_id.presta_id,
                                          'id_product_attribute': product.presta_child_id,
                                          'id_shop': '0',
                                          'id_shop_group': '1',
                                          'out_of_stock': '2',
                                          'quantity': product.pakdo_qty}}
                        _logger.info("Prestashop Exporting stock    ..............." + str(product.default_code) )
                        _logger.info(str(stock_vals))
                        try:
                            stock_resp = prestashop.edit('stock_availables',stock_vals)
                        except:
                            error_data += str(product.default_code) + ','
                            _logger.info("Prestashop Exporting stock errorrrrrrrrrrrrrrrr    ..............." + str(product.default_code) )
                
                presta.write({'export_stock_error': error_data})
        
        return True
    
    
    @api.multi
    def export_product_stock_new(self):
        _logger.info("Prestashop Exporting stock function called   ..............." )
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                
                stocks = self.env['pakdo.presta.stock'].search([('presta_id','!=',False),('presta_child_id','!=',False)])
                print 'stocks stocks stocks       ',stocks
                self.import_product_stock()
                for stock in stocks:
                    if stock.presta_stock_id:
                        stock_vals = {'stock_available': {'depends_on_stock': '0',
                                  'id': stock.presta_stock_id,
                                  'id_product': stock.presta_id,
                                  'id_product_attribute': stock.presta_child_id,
                                  'id_shop': '1',
                                  'id_shop_group': '0',
                                  'out_of_stock': '1',
                                  'quantity': stock.qty}}
                        print 'stock_vals stock_vals        ',stock_vals
                        stock_resp = prestashop.edit('stock_availables',stock_vals)
                        
                
        
        return True
    
    @api.model
    def export_product_stock_cron(self,use_new_cursor=False):
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                products = self.env['product.product'].search([('presta_child_id','!=',0)])
                #products = self.env['product.product'].search([('id','=',12575)])
                
                #self.import_product_child_id()
                #self.import_product_stock()
                
                print 'products  ',products
                error_data = ''
                for product in products:
                    if product.presta_child_id and product.product_tmpl_id.presta_id:
                        stock_vals = {'stock_available': {'depends_on_stock': '0',
                                          'id': product.presta_stock_id,
                                          'id_product': product.product_tmpl_id.presta_id,
                                          'id_product_attribute': product.presta_child_id,
                                          'id_shop': '0',
                                          'id_shop_group': '1',
                                          'out_of_stock': '2',
                                          'quantity': product.pakdo_qty}}
                        _logger.info("Prestashop Exporting stock    ..............." + str(product.default_code) )
                        _logger.info(str(stock_vals))
                        try:
                            stock_resp = prestashop.edit('stock_availables',stock_vals)
                        except:
                            error_data += str(product.default_code) + ','
                            _logger.info("Prestashop Exporting stock errorrrrrrrrrrrrrrrr    ..............." + str(product.default_code) )
                
                presta.write({'export_stock_error': error_data})
        
        return True
    
    @api.multi
    def import_product_image(self):
        for presta in self:
            if presta.state == 'connected':
                
                #http://prestashop.wollbody.de/30-medium_default/strumpfhose.jpg
                #large_default, medium_default, small_default, home_default, cart_default
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                #image_type = prestashop.get('image_types')
                #print 'images images       ',image_type
                
                
                #https://www.wollbody.de/media/image/b1/03/ec/Logo_Wollbody.png
                img = { 'images' : {'image' :'https://www.wollbody.de/media/image/b1/03/ec/Logo_Wollbody.png', 
                                    'id_product': '8',
                                    } }
                
                ig = {'prestashop': {'image_types': {'products': {'image' :'https://www.wollbody.de/media/image/b1/03/ec/Logo_Wollbody.png', 
                                    'id_product': '8',
                                    }}}}
                
                xml_val = ''' <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
                                <id_product>50</id_product>
                                <image>https://www.wollbody.de/media/image/b1/03/ec/Logo_Wollbody.png"</image>
                                </prestashop> '''
                
                images = prestashop.add('images',ig)
                print 'v  >>>>>>>>>>..        ',images
#                 for image in images['images']['image']:
#                     print "image['attrs'].get('id')      ",image['attrs'].get('id')
#                     img = prestashop.get('images','products',options={'display':image['attrs'].get('id')})
#                     print 'imggggggg     ',img
                
                
                #i = prestashop.get_with_url('http://prestashop.wollbody.de/api/images/products/7/26')
                #print 'i i i    ',i
        
        return True
    
    @api.multi
    def export_image(self, product_template):
        #add product image file_name = ‘sample.jpg’ fd = io.open(file_name, “rb”) content = fd.read() fd.close()
        #prestashop.add(‘/images/products/123’, files=[(‘image’, file_name, content)])
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                #add product image file_name = ‘sample.jpg’ fd = io.open(file_name, “rb”) content = fd.read() fd.close()
                #product_template = self.env['product.template'].search([('art_no','=','91053')], limit=1)
                if product_template:
                    path_list = []
                    for template in product_template:
                    
                        #file_name = '/home/ali/Desktop/image.jpeg'
                        #file_name ='https://www.wollbody.de/media/image/b1/03/ec/Logo_Wollbody.png'
                        
                        if template.image and template.presta_image_id == 0:
                            tmp_dir = tempfile.gettempdir()
                            
                            path = tmp_dir +"/" + template.art_no +'_' + template.color_no +".jpeg"
                            with open(path, "wb") as fh:
                                fh.write(template.image.decode('base64'))
                                path_list.append(path)
                                fh.close()
                                self._cr.commit()
                            
                            file_name = str(path)
                            fd = io.open(file_name, 'rb') 
                            content = fd.read() 
                            fd.close()
                            image = prestashop.add('/images/products/'+str(template.presta_id), files=[('image', file_name, content)])
                            
                            if image['prestashop']['image']['id']:
                                template.write({'presta_image_id': image['prestashop']['image']['id']})
        
        return True
    
    
    @api.multi
    def push_images(self, product_template):
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                #add product image file_name = ‘sample.jpg’ fd = io.open(file_name, “rb”) content = fd.read() fd.close()
                #product_template = self.env['product.template'].search([('art_no','=','91053')], limit=1)
                print 'product_template product_template        ',product_template
                product_templates = self.env['product.template'].search([('id','in',product_template)])
                if product_templates:
                    path_list = []
                    for template in product_templates:
                        
                        #file_name = '/home/ali/Desktop/image.jpeg'
                        #file_name ='https://www.wollbody.de/media/image/b1/03/ec/Logo_Wollbody.png'
                        
                        if template.image and  not template.presta_image_id:
                            tmp_dir = tempfile.gettempdir()
                            
                            path = tmp_dir +"/" + template.art_no +'_' + template.color_no +".jpeg"
                            with open(path, "wb") as fh:
                                fh.write(template.image.decode('base64'))
                                path_list.append(path)
                                fh.close()
                                self._cr.commit()
                            
                            file_name = str(path)
                            fd = io.open(file_name, 'rb') 
                            content = fd.read() 
                            fd.close()
                            image = prestashop.add('/images/products/'+str(template.presta_id), files=[('image', file_name, content)])
                            
                            if image['prestashop']['image']['id']:
                                template.write({'presta_image_id': image['prestashop']['image']['id']})
        return True
        
    @api.multi
    def push_single_product(self, product_tmpl):
        if product_tmpl:
            
            category_list = []
            
            for category in product_tmpl.presta_categories:
                category_list.append(category.prestashop_id)
            
            if len(category_list) > 1:
                cat_dict = []
                #cat_dict.append({'id': 1})
                #cat_dict.append({'id': 2})
                for cat in category_list:
                    cat_dict.append({'id': cat})
                    
                
                    
            elif len(category_list) == 1:
                cat_dict = []
                #cat_dict.append({'id': 1})
                #cat_dict.append({'id': 2})
                for cat in category_list:
                    cat_dict.append({'id': cat})
            
            print 'len(product_tmpl.presta_feature.ids)      ',len(product_tmpl.presta_feature.ids)
            
            feature_dict = ''
            if product_tmpl.material_id:
                feature_dict = {'id': product_tmpl.material_id.presta_material_id, 'id_feature_value' : product_tmpl.material_id.presta_id}
            
            product_dict =  {'active': '1',
              'additional_shipping_cost': '0.00',
              'advanced_stock_management': '0',
              'associations': {'accessories': {'attrs': {'api': 'products',
                 'nodeType': 'product'},
                'value': ''},
                               
               'categories': {'attrs': {'api': 'categories', 'nodeType': 'category'},
                'category': cat_dict},
               'combinations': {'attrs': {'api': 'combinations',
                                            'nodeType': 'combination'},
                                   'value': ''},
               #'product_features': {'attrs': {'api': 'product_features','nodeType': 'product_feature'},
               #  'product_feature': feature_dict},    
               'product_bundle': {'attrs': {'api': 'products', 'nodeType': 'product'},
                'value': ''},
                'tags': {'attrs': {'api': 'tags', 'nodeType': 'tag'}, 'value': ''}},
                             
              'available_for_order': '1',
              'condition': 'new',
              
              #'description': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_description_german if product_tmpl.presta_description_german else ''},
              #  {'attrs': {'id': '2'}, 'value': product_tmpl.presta_description_english if product_tmpl.presta_description_english else ''}]},
                             
              #'description_short': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_description_short_german if product_tmpl.presta_description_short_german else ''},
              #  {'attrs': {'id': '2'}, 'value': product_tmpl.presta_description_short_english if product_tmpl.presta_description_short_english else ''}]},
                             
                             
              'link_rewrite': {'language': [{'attrs': {'id': '1'}, 'value': 'abc-xyz'},
                {'attrs': {'id': '2'}, 'value': 'abc-xyz'}]},
              'location': '',
              #'manufacturer_name': {'attrs': {'notFilterable': 'true'},
              #'value': product_tmpl.supplier_name},
              
            #'id_manufacturer' : product_tmpl.related_supplier_id.presta_supplier_id,
              
              
            'meta_description': {'language': [{'attrs': {'id': '1'},'value': product_tmpl.presta_meta_description_german if product_tmpl.presta_meta_description_german else ''},
              {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_description_english if product_tmpl.presta_meta_description_english else ''}]},
              
              'meta_keywords': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_meta_keywords_german if product_tmpl.presta_meta_keywords_german else ''},
                {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_keywords_english if product_tmpl.presta_meta_keywords_english else ''}]},
                             
              'meta_title': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_meta_title_german if product_tmpl.presta_meta_title_german else ''},
                {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_title_english if product_tmpl.presta_meta_title_english else ''}]},
                             
              'minimal_quantity': '1',
              'name': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.german_name},
                {'attrs': {'id': '2'}, 'value': product_tmpl.name}]},
                             
              'new': '',
              #'pack_stock_type': '3',
              #'price': product_tmpl.get_small_child.lst_price,
              'id_category_default': product_tmpl.presta_default_category_id.prestashop_id,
              'price': product_tmpl.impact_on_price,
              #'id_shop_default': '1',
              #'quantity': {'attrs': {'notFilterable': 'true'}, 'value': '0'},
              'redirect_type': '404',
              'reference': product_tmpl.get_small_child.default_code,
              'show_condition': '0',
              'show_price': '1',
              'state': '1',
              'supplier_reference': '',
              'text_fields': '0',
              'type': {'attrs': {'notFilterable': 'true'}, 'value': 'simple'},
              'unit_price_ratio': '0.000000',
              'unity': '',
              'upc': '',
              'uploadable_files': '0',
              'visibility': 'both',
              'weight': '0.000000',
              'wholesale_price': 0,
              'width': '0.000000'}
            
            
            product_dict = {'active': '1',
              'additional_delivery_times': '1',
              'additional_shipping_cost': '0.00',
              'advanced_stock_management': '0',
              'associations': {'accessories': {'attrs': {'api': 'products',
                 'nodeType': 'product'},
                'value': ''},
               'categories': {'attrs': {'api': 'categories', 'nodeType': 'category'},
                'category': {'id': '2'}},
               'combinations': {'attrs': {'api': 'combinations',
                 'nodeType': 'combination'},
                'value': ''},
               'images': {'attrs': {'api': 'images', 'nodeType': 'image'},
                'image': {'id': '21'}},
               'product_bundle': {'attrs': {'api': 'products', 'nodeType': 'product'},
                'value': ''},
               'product_features': {'attrs': {'api': 'product_features',
                 'nodeType': 'product_feature'},
                'value': ''},
               'product_option_values': {'attrs': {'api': 'product_option_values',
                 'nodeType': 'product_option_value'},
                'value': ''},
               'stock_availables': {'attrs': {'api': 'stock_availables',
                 'nodeType': 'stock_available'},
                'stock_available': {'id': '2', 'id_product_attribute': '0'}},
               'tags': {'attrs': {'api': 'tags', 'nodeType': 'tag'}, 'value': ''}},
              'available_date': '0000-00-00',
              'available_for_order': '1',
              'available_later': {'language': [{'attrs': {'id': '1'}, 'value': ''},
                {'attrs': {'id': '2'}, 'value': ''}]},
              'available_now': {'language': [{'attrs': {'id': '1'}, 'value': ''},
                {'attrs': {'id': '2'}, 'value': ''}]},
              'cache_default_attribute': '0',
              'cache_has_attachments': '0',
              'cache_is_pack': '0',
              'condition': 'new',
              'customizable': '0',
              #'date_add': '2018-06-18 12:09:57',
              #'date_upd': '2018-06-18 12:09:57',
              'delivery_in_stock': {'language': [{'attrs': {'id': '1'}, 'value': ''},
                {'attrs': {'id': '2'}, 'value': ''}]},
              'delivery_out_stock': {'language': [{'attrs': {'id': '1'}, 'value': ''},
                {'attrs': {'id': '2'}, 'value': ''}]},
              'depth': '0.000000',
              
            'description': {'language': [{'attrs': {'id': '1'},
               'value': product_tmpl.presta_description_german if product_tmpl.presta_description_german else ''},
              {'attrs': {'id': '2'},
               'value': product_tmpl.presta_description_english if product_tmpl.presta_description_english else ''}]},
            'description_short': {'language': [{'attrs': {'id': '1'},
               'value': product_tmpl.presta_description_short_german if product_tmpl.presta_description_short_german else ''},
              {'attrs': {'id': '2'},
               'value': product_tmpl.presta_description_short_english if product_tmpl.presta_description_short_english else ''}]},
                                        
              
            #   'description': {'language': [{'attrs': {'id': '1'},
            #      'value': ''},
            #     {'attrs': {'id': '2'},
            #      'value': ''}]},
            #   'description_short': {'language': [{'attrs': {'id': '1'},
            #      'value': ''},
            #     {'attrs': {'id': '2'},
            #      'value': ''}]},
              'ean13': '',
              'ecotax': '0.000000',
              'height': '0.000000',
              #'id': '2',
              #'id_category_default': product_tmpl.presta_default_category_id.prestashop_id,
              'id_category_default': '2',
              'id_default_combination': {'attrs': {'notFilterable': 'true'}, 'value': ''},
              'id_default_image': {'attrs': {'notFilterable': 'true'}, 'value': '21'},
              'id_manufacturer': product_tmpl.related_supplier_id.presta_supplier_id,
              #'id_shop_default': '1',
              'id_supplier': '0',
              'id_tax_rules_group': '1',
              'id_type_redirected': '0',
              'indexed': '1',
              'is_virtual': '0',
              'isbn': '',
              'link_rewrite': {'language': [{'attrs': {'id': '1'},
                 'value': 'brown-bear-printed-sweater'},
                {'attrs': {'id': '2'}, 'value': 'brown-bear-printed-sweater'}]},
              'location': '',
              'low_stock_alert': '0',
              'low_stock_threshold': '',
             # 'manufacturer_name': {'attrs': {'notFilterable': 'true'},
             #  'value': u'Wollbody\xae'},
            'meta_description': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_meta_description_german if product_tmpl.presta_meta_description_german else ''},
              {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_description_english if product_tmpl.presta_meta_description_english else ''}]},
            'meta_keywords': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_meta_keywords_german if product_tmpl.presta_meta_keywords_german else ''},
              {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_keywords_english if product_tmpl.presta_meta_keywords_english else ''}]},
            'meta_title': {'language': [{'attrs': {'id': '1'}, 'value': ''},
              {'attrs': {'id': '2'}, 'value': ''}]},
                                        
            'meta_description': {'language': [{'attrs': {'id': '1'}, 'value': ''},
              {'attrs': {'id': '2'}, 'value': ''}]},
            'meta_keywords': {'language': [{'attrs': {'id': '1'}, 'value': ''},
              {'attrs': {'id': '2'}, 'value': ''}]},
            'meta_title': {'language': [{'attrs': {'id': '1'}, 'value': ''},
              {'attrs': {'id': '2'}, 'value': ''}]},
                                        
              'minimal_quantity': '1',
              'name': {'language': [{'attrs': {'id': '1'},
                 'value': product_tmpl.german_name},
                {'attrs': {'id': '2'}, 'value': product_tmpl.name}]},
              'new': '',
              'on_sale': '0',
              'online_only': '0',
              'pack_stock_type': '3',
              'position_in_category': {'attrs': {'notFilterable': 'true'}, 'value': '1'},
              'price': str(product_tmpl.impact_on_price),
             # 'quantity': {'attrs': {'notFilterable': 'true'}, 'value': '0'},
             # 'quantity_discount': '0',
              'redirect_type': '404',
              'reference': product_tmpl.get_small_child.default_code,
              'show_condition': '0',
              'show_price': '1',
              'state': '1',
              'supplier_reference': '',
              'text_fields': '0',
              'type': {'attrs': {'notFilterable': 'true'}, 'value': 'simple'},
              'unit_price_ratio': '0.000000',
              'unity': '',
              'upc': '',
              'uploadable_files': '0',
              'visibility': 'both',
              'weight': '0.000000',
              'wholesale_price': '0.000000',
              'width': '0.000000'}
            
            
            
            
            
            print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.',product_dict
            flag = False
            pushed = False
            for presta in self:
                if presta.state == 'connected':
                    prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                    print 'prestashop  prestashop       ',dir(prestashop) 
                    if not product_tmpl.presta_id:
                        
#                         templates_pushed = self.env['product.template'].search([('art_no','=',product_tmpl.art_no),('presta_id','!=',0)], limit=1)
#                         print 'templates_pushed templates_pushed     ',templates_pushed
#                         if templates_pushed:
#                             
# 
#                             product_dict.update({'id': templates_pushed.presta_id})
#                             product_dict.pop('link_rewrite')
#                             final_dict = {'product': product_dict}
#                             resp = prestashop.edit('products',final_dict)
#                             flag = True
#                             pushed = False
#                         else:
                        
                         
                        final_dict = {'product': product_dict}
                        resp = prestashop.add('products', final_dict)
                        print 'resppppppp    ',resp
                        pushed = True

                            #pushing image
                            #self.export_image(product_tmpl)
                    
                        
                    print 'resp resp          ',resp
                    if resp['prestashop']['product']['id']:
                        
                        
                        
                        
                        
                            
                        url = presta.url + '/' +  resp['prestashop']['product']['id'] + '-' + resp['prestashop']['product']['link_rewrite']['language'][0]['value'] + '.html'
                        product_tmpl.write({'presta_id': resp['prestashop']['product']['id'], 'presta_link': url})
                        
                    
                            
                                
                        
                        
                        if product_tmpl.product_variant_ids:
                            for variant in product_tmpl.product_variant_ids:
                                
                                print 'variant.product_tmpl_id.presta_image_id           ',variant.product_tmpl_id.presta_image_id
                                print 'variant.product_tmpl_id                 ',variant.product_tmpl_id
                                presta_price = 0.0
                                if variant.presta_price_push > 0:
                                    presta_price = variant.presta_price_push
                                else:
                                    presta_price = variant.compute_sale_price / 1.19
                                try:
                                    default_on = ''
                                    if product_tmpl.get_small_child.id == variant.id:
                                        if flag == False:
                                            default_on = '1'
                                    child_dict = {'combination': {'associations': {'images': {'attrs': {'api': 'images/products',
                                                     'nodeType': 'image'},
                                                     'value': str(variant.product_tmpl_id.presta_image_id)+ '-small_default.jpg'},
                                                    
                                                    #'image': {'id': variant.product_tmpl_id.presta_image_id}},
                                                    
                                                    #'image': [{'id': variant.presta_image_id}, {'id': '159'}]
                                                    
                                                   'product_option_values': {'attrs': {'api': 'product_option_values',
                                                     'nodeType': 'product_option_value'},
                                                    #'product_option_value': [{'id': product_tmpl.get_color_id.prestashop_id}, {'id': variant.attribute_value_ids[0].prestashop_id}]}},
                                                    'product_option_value': [{'id': variant.product_tmpl_id.get_color_id.prestashop_id}, {'id': variant.attribute_value_ids[0].prestashop_id}]}},
                                                  'ean13': variant.barcode,
                                                  'id_product': resp['prestashop']['product']['id'],
                                                  'default_on' : default_on,
                                                  'minimal_quantity': '1',
                                                  'price': variant.child_impact_on_price,
                                                  'reference': variant.default_code,
                                                  'wholesale_price': variant.standard_price}}
                                    
    
    #                                                   'wholesale_price': '6.750000'}}
                                    
                                    print 'child_dict child_dictchild_dict    ',child_dict
                                    if not variant.presta_child_id:
                                        child_resp = prestashop.add('combinations', child_dict)
                                        
                                        print 'child_resp ^^^^^^^^^^^^^^^^^^^             ',child_resp
                                        variant.write({'presta_child_id': child_resp['prestashop']['combination']['id']})
                                    if variant.presta_child_id :
                                         child_dict = {'combination': {'associations': {'images': {'attrs': {'api': 'images/products',
                                                      'nodeType': 'image'},
                                                     },
                                                    'product_option_values': {'attrs': {'api': 'product_option_values',
                                                      'nodeType': 'product_option_value'},
                                                     #'product_option_value': [{'id': product_tmpl.get_color_id.prestashop_id}, {'id': variant.attribute_value_ids[0].prestashop_id}]}},
                                                     'product_option_value': [{'id': variant.product_tmpl_id.get_color_id.prestashop_id}, {'id': variant.attribute_value_ids[0].prestashop_id}]}},
                                                   'ean13': variant.barcode,
                                                   'id_product': resp['prestashop']['product']['id'],
                                                   'default_on' : default_on,
                                                   'minimal_quantity': '1',
                                                   'price': variant.presta_price_push,
                                                   'reference': variant.default_code,
                                                   'id': variant.presta_child_id,
                                                   'wholesale_price': variant.standard_price}}
                                         child_resp = prestashop.edit('combinations', child_dict)
                                         
                                    variant.write({'presta_child_id': child_resp['prestashop']['combination']['id']})
                                    #http://prestashop.wollbody.de/de/43-584-baby-body.html
                                    url = presta.url + '/' +  resp['prestashop']['product']['id'] + '-' + resp['prestashop']['product']['link_rewrite']['language'][0]['value'] + '.html'
                                    variant.product_tmpl_id.write({'presta_id': resp['prestashop']['product']['id'], 'presta_link': url})
                                    
                                    self.export_product_specific_prices(variant)
                                except:
                                    #resp = prestashop.delete('products', resp['prestashop']['product']['id'])
                                    variant.write({'presta_child_id': 0, 'presta_stock_id': 0})
                                    product_tmpl.write({'presta_id': 0, 'presta_image_id': 0,  'presta_link': ''})
                                    return True
        
    @api.multi
    def push_product(self, product_tmpl):
        if product_tmpl:
            
            category_list = []
            
            for category in product_tmpl.presta_categories:
                category_list.append(category.prestashop_id)
            
            if len(category_list) > 1:
                cat_dict = []
                #cat_dict.append({'id': 1})
                #cat_dict.append({'id': 2})
                for cat in category_list:
                    cat_dict.append({'id': cat})
                    
                
                    
            elif len(category_list) == 1:
                cat_dict = []
                #cat_dict.append({'id': 1})
                #cat_dict.append({'id': 2})
                for cat in category_list:
                    cat_dict.append({'id': cat})
            
            print 'len(product_tmpl.presta_feature.ids)      ',len(product_tmpl.presta_feature.ids)
            
#                 feature_dict = []
#                 for feature in product_tmpl.presta_feature:
#                     if len(product_tmpl.presta_feature.ids) > 1:
#                         
#                         feature_dict.append({'id': feature.parent_id.prestashop_id, 'id_feature_value' : feature.prestashop_value_id})
#                     
#                     else:
#                         feature_dict = {'id': feature.parent_id.prestashop_id, 'id_feature_value' : feature.prestashop_value_id}
            feature_dict = ''
            if product_tmpl.material_id:
                feature_dict = {'id': product_tmpl.material_id.presta_material_id, 'id_feature_value' : product_tmpl.material_id.presta_id}
            
#             product_dict_o =  {'active': '1',
#               'additional_shipping_cost': '0.00',
#               'advanced_stock_management': '0',
#               'associations': {'accessories': {'attrs': {'api': 'products',
#                  'nodeType': 'product'},
#                 'value': ''},
#                                
#                'categories': {'attrs': {'api': 'categories', 'nodeType': 'category'},
#                 'category': cat_dict},
#                'product_features': {'attrs': {'api': 'product_features',
#                  'nodeType': 'product_feature'},
#                 'value': ''},
#                'product_option_values': {'attrs': {'api': 'product_option_values',
#                  'nodeType': 'product_option_value'},
#                 'value': ''},
#                #'product_features': {'attrs': {'api': 'product_features','nodeType': 'product_feature'},
#                #  'product_feature': feature_dict},    
#                'product_bundle': {'attrs': {'api': 'products', 'nodeType': 'product'},
#                 'value': ''},
#                 'tags': {'attrs': {'api': 'tags', 'nodeType': 'tag'}, 'value': ''}},
#                              
#               'available_for_order': '1',
#               'condition': 'new',
#               
#               'description': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_description_german if product_tmpl.presta_description_german else ''},
#                 {'attrs': {'id': '2'}, 'value': product_tmpl.presta_description_english if product_tmpl.presta_description_english else ''}]},
#                              
#               'description_short': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_description_short_german if product_tmpl.presta_description_short_german else ''},
#                 {'attrs': {'id': '2'}, 'value': product_tmpl.presta_description_short_english if product_tmpl.presta_description_short_english else ''}]},
#                              
#                              
#               #'link_rewrite': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.german_name},
#               #  {'attrs': {'id': '2'}, 'value': product_tmpl.name}]},
#               
#               'link_rewrite': {'language': [{'attrs': {'id': '1'}, 'value': 'aaa-a'},
#                 {'attrs': {'id': '2'}, 'value': 'aaa-a'}]},
#               'location': '',
#               #'manufacturer_name': {'attrs': {'notFilterable': 'true'},
#               #'value': product_tmpl.supplier_name},
#               
#             'id_manufacturer' : product_tmpl.related_supplier_id.presta_supplier_id,
#               
#               
#             'meta_description': {'language': [{'attrs': {'id': '1'},'value': product_tmpl.presta_meta_description_german if product_tmpl.presta_meta_description_german else ''},
#               {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_description_english if product_tmpl.presta_meta_description_english else ''}]},
#               
#               'meta_keywords': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_meta_keywords_german if product_tmpl.presta_meta_keywords_german else ''},
#                 {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_keywords_english if product_tmpl.presta_meta_keywords_english else ''}]},
#                              
#               'meta_title': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_meta_title_german if product_tmpl.presta_meta_title_german else ''},
#                 {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_title_english if product_tmpl.presta_meta_title_english else ''}]},
#                              
#               'minimal_quantity': '1',
#               'name': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.german_name},
#                 {'attrs': {'id': '2'}, 'value': product_tmpl.name}]},
#                              
#               'new': '',
#               #'pack_stock_type': '3',
#               #'price': product_tmpl.get_small_child.lst_price,
#               'id_category_default': '2',
#               'position_in_category': {'attrs': {'notFilterable': 'true'}, 'value': product_tmpl.presta_default_category_id.prestashop_id},
#               #'price': product_tmpl.impact_on_price,
#               'price': '123.000',
#               #'id_shop_default': '1',
#               #'quantity': {'attrs': {'notFilterable': 'true'}, 'value': '0'},
#               'redirect_type': '404',
#               'reference': product_tmpl.get_small_child.default_code,
#               'show_condition': '0',
#               'show_price': '1',
#               'state': '1',
#               'supplier_reference': '',
#               'text_fields': '0',
#               'type': {'attrs': {'notFilterable': 'true'}, 'value': 'simple'},
#               'unit_price_ratio': '0.000000',
#               'unity': '',
#               'upc': '',
#               'uploadable_files': '0',
#               'visibility': 'both',
#               'weight': '0.000000',
#               'wholesale_price': 0,
#               'width': '0.000000'}
            
            
            product_dict = {'active': '1',
              'additional_delivery_times': '1',
              'additional_shipping_cost': '0.00',
              'advanced_stock_management': '0',
              'associations': {'accessories': {'attrs': {'api': 'products',
                 'nodeType': 'product'},
                'value': ''},
               'categories': {'attrs': {'api': 'categories', 'nodeType': 'category'},
                'category': cat_dict},
               'combinations': {'attrs': {'api': 'combinations',
                 'nodeType': 'combination'},
                'value': ''},
               #'images': {'attrs': {'api': 'images', 'nodeType': 'image'},
               # 'image': {'id': '21'}},
               'product_bundle': {'attrs': {'api': 'products', 'nodeType': 'product'},
                'value': ''},
               'product_features': {'attrs': {'api': 'product_features',
                 'nodeType': 'product_feature'},
                'value': ''},
               'product_option_values': {'attrs': {'api': 'product_option_values',
                 'nodeType': 'product_option_value'},
                'value': ''},
                'product_features': {'attrs': {'api': 'product_features','nodeType': 'product_feature'},
                'product_feature': feature_dict},
               #'stock_availables': {'attrs': {'api': 'stock_availables',
               #  'nodeType': 'stock_available'},
               # 'stock_available': {'id': '2', 'id_product_attribute': '0'}},
               'tags': {'attrs': {'api': 'tags', 'nodeType': 'tag'}, 'value': ''}},
              #'available_date': '0000-00-00',
              'available_for_order': '1',
              'available_later': {'language': [{'attrs': {'id': '1'}, 'value': ''},
                {'attrs': {'id': '2'}, 'value': ''}]},
              'available_now': {'language': [{'attrs': {'id': '1'}, 'value': ''},
                {'attrs': {'id': '2'}, 'value': ''}]},
              'cache_default_attribute': '0',
              'cache_has_attachments': '0',
              'cache_is_pack': '0',
              'condition': 'new',
              'customizable': '0',
              #'date_add': '2018-06-18 12:09:57',
              #'date_upd': '2018-06-18 12:09:57',
              'delivery_in_stock': {'language': [{'attrs': {'id': '1'}, 'value': ''},
                {'attrs': {'id': '2'}, 'value': ''}]},
              'delivery_out_stock': {'language': [{'attrs': {'id': '1'}, 'value': ''},
                {'attrs': {'id': '2'}, 'value': ''}]},
              'depth': '0.000000',
              
            'description': {'language': [{'attrs': {'id': '1'},
               'value': product_tmpl.presta_description_german if product_tmpl.presta_description_german else ''},
              {'attrs': {'id': '2'},
               'value': product_tmpl.presta_description_english if product_tmpl.presta_description_english else ''}]},
            'description_short': {'language': [{'attrs': {'id': '1'},
               'value': product_tmpl.presta_description_short_german if product_tmpl.presta_description_short_german else ''},
              {'attrs': {'id': '2'},
               'value': product_tmpl.presta_description_short_english if product_tmpl.presta_description_short_english else ''}]},
                                        
              'ean13': '',
              'ecotax': '0.000000',
              'height': '0.000000',
              
              'id_category_default': product_tmpl.presta_default_category_id.prestashop_id,
              #'id_category_default': '2',
              'id_default_combination': {'attrs': {'notFilterable': 'true'}, 'value': ''},
              'id_default_image': {'attrs': {'notFilterable': 'true'}, 'value': ''},
              'id_manufacturer': product_tmpl.related_supplier_id.presta_supplier_id,
              #'id_shop_default': '1',
              'id_supplier': '0',
              'id_tax_rules_group': '1',
              'id_type_redirected': '0',
              'indexed': '1',
              'is_virtual': '0',
              'isbn': '',
              'link_rewrite': {'language': [{'attrs': {'id': '1'},
                 'value': product_tmpl.german_name.replace(' ','-')},
                {'attrs': {'id': '2'}, 'value': product_tmpl.name.replace(' ','-')}]},
              'location': '',
              'low_stock_alert': '0',
              'low_stock_threshold': '',
             # 'manufacturer_name': {'attrs': {'notFilterable': 'true'},
             #  'value': u'Wollbody\xae'},
            'meta_description': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_meta_description_german if product_tmpl.presta_meta_description_german else ''},
              {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_description_english if product_tmpl.presta_meta_description_english else ''}]},
            'meta_keywords': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_meta_keywords_german if product_tmpl.presta_meta_keywords_german else ''},
              {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_keywords_english if product_tmpl.presta_meta_keywords_english else ''}]},
            'meta_title': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_meta_title_german if product_tmpl.presta_meta_title_german else ''},
              {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_title_english if product_tmpl.presta_meta_title_english else ''}]},
                                        
            
                                        
              'minimal_quantity': '1',
              'name': {'language': [{'attrs': {'id': '1'},
                 'value': product_tmpl.german_name},
                {'attrs': {'id': '2'}, 'value': product_tmpl.name}]},
              'new': '',
              'on_sale': '0',
              'online_only': '0',
              'pack_stock_type': '3',
              'position_in_category': {'attrs': {'notFilterable': 'true'}, 'value': '0'},
              #'position_in_category': {'attrs': {'notFilterable': 'true'}, 'value': product_tmpl.presta_default_category_id.prestashop_id},
              'price': str(product_tmpl.impact_on_price),
             # 'quantity': {'attrs': {'notFilterable': 'true'}, 'value': '0'},
             # 'quantity_discount': '0',
              'redirect_type': '404',
              'reference': product_tmpl.get_small_child.default_code,
              'show_condition': '0',
              'show_price': '1',
              'state': '1',
              'supplier_reference': '',
              'text_fields': '0',
              'type': {'attrs': {'notFilterable': 'true'}, 'value': 'simple'},
              'unit_price_ratio': '0.000000',
              'unity': '',
              'upc': '',
              'uploadable_files': '0',
              'visibility': 'both',
              'weight': '0.000000',
              'wholesale_price': '0.000000',
              'width': '0.000000'}
            
            
            
            pushed = False
            for presta in self:
                if presta.state == 'connected':
                    prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                    if not product_tmpl.presta_id:
                        final_dict = {'product': product_dict}
                        resp = prestashop.add('products', final_dict)
                        pushed = True
                        templates_all = self.env['product.template'].search([('art_no','=',product_tmpl.art_no)])
                        if templates_all:
                            for product_template in templates_all:
                                print 'product_template product_template product_template     ',product_template
                                url =  presta.shop_url + '/' +  resp['prestashop']['product']['id'] + '-' + resp['prestashop']['product']['link_rewrite']['language'][0]['value'] + '.html'
                                product_template.write({'presta_id': resp['prestashop']['product']['id'], 'presta_link': url})
                                
                                #self.export_image(product_template)
                                    
                    if product_tmpl.presta_id:
                        product_dict.update({'id': product_tmpl.presta_id})
                        product_dict.pop('link_rewrite')
                        final_dict = {'product': product_dict}
                        resp = prestashop.edit('products',final_dict)
                        pushed = False
                        
                    #print 'resp resp          ',resp
                    if resp['prestashop']['product']['id']:
                        if product_tmpl.get_all_child:
                            for variant in product_tmpl.get_all_child:
                                
                                print 'variant.product_tmpl_id.presta_image_id           ',variant.product_tmpl_id.presta_image_id
                                print 'variant.product_tmpl_id                 ',variant.product_tmpl_id
                                presta_price = 0.0
                                if variant.presta_price_push > 0:
                                    presta_price = variant.presta_price_push
                                else:
                                    presta_price = variant.compute_sale_price / 1.19
                                
                                #try:
                                default_on = ''
                                if product_tmpl.get_small_child.id == variant.id:
                                    default_on = '1'
                                
                                child_dict = {'combination' :{'associations': 
                                              
                                              {'images': {'attrs': {'api': 'images/products',
                                                'nodeType': 'image'},
                                               'image': {'id': '27'}},
                                              'product_option_values': {'attrs': {'api': 'product_option_values',
                                                'nodeType': 'product_option_value'},
                                               'product_option_value': [{'id': variant.product_tmpl_id.get_color_id.prestashop_id}, {'id': variant.attribute_value_ids[0].prestashop_id}]}},
                                             'available_date': '0000-00-00',
                                             'default_on': default_on,
                                             'ean13': variant.barcode,
                                             'ecotax': '0.000000',
                                             #'id': '45',
                                             'id_product': resp['prestashop']['product']['id'],
                                             'isbn': '',
                                             'location': '',
                                             'low_stock_alert': '0',
                                             'low_stock_threshold': '',
                                             'minimal_quantity': '1',
                                             'price': str(variant.child_impact_on_price),
                                            # 'quantity': str(variant.pakdo_qty),
                                             'reference': variant.default_code,
                                             'supplier_reference': '',
                                             'unit_price_impact': '0.000000',
                                             'upc': '',
                                             'weight': '0.000000',
                                             'wholesale_price': str(variant.standard_price)}}
                                


                                
                                print 'child_dict child_dictchild_dict    ',child_dict
                                
#                                 if variant.presta_child_id :
#                                     child_dict = {'combination' :{'associations': 
#                                               
#                                               {'images': {'attrs': {'api': 'images/products',
#                                                 'nodeType': 'image'},
#                                                'image': {'id': '27'}},
#                                               'product_option_values': {'attrs': {'api': 'product_option_values',
#                                                 'nodeType': 'product_option_value'},
#                                                'product_option_value': [{'id': variant.product_tmpl_id.get_color_id.prestashop_id}, {'id': variant.attribute_value_ids[0].prestashop_id}]}},
#                                              
#                                              'default_on': default_on,
#                                              'ean13': variant.barcode,
#                                              'id': variant.presta_child_id,
#                                              'id_product': resp['prestashop']['product']['id'],
#                                              'minimal_quantity': '1',
#                                              'price': str(variant.child_impact_on_price),
#                                              'quantity': str(variant.pakdo_qty),
#                                              'reference': variant.default_code,
#                                              'supplier_reference': '',
#                                              'wholesale_price': str(variant.standard_price)}}
#                                     
#                                     child_resp = prestashop.edit('combinations', child_dict)

                                    
                                    
                                if not variant.presta_child_id:
                                    child_resp = prestashop.add('combinations', child_dict)
                                    print 'child_resp ^^^^^^^^^^^^^^^^^^^             ',child_resp
                                    variant.write({'presta_child_id': child_resp['prestashop']['combination']['id']})
                                    
                                    
                                #http://prestashop.wollbody.de/de/43-584-baby-body.html
                                #url = presta.url + '/' +  resp['prestashop']['product']['id'] + '-' + resp['prestashop']['product']['link_rewrite']['language'][0]['value'] + '.html'
                                #variant.product_tmpl_id.write({'presta_id': resp['prestashop']['product']['id'], 'presta_link': url})
                                
                                
                                #except:
                                #    resp = prestashop.delete('products', resp['prestashop']['product']['id'])
                                #    variant.write({'presta_child_id': 0, 'presta_stock_id': 0})
                                #    product_template.write({'presta_id': 0, 'presta_image_id': 0, 'presta_link': ''})
                                #    return True
                                    
    @api.multi
    def update_product_details(self, product_tmpl):
        if product_tmpl:
            
            category_list = []
            
            for category in product_tmpl.presta_categories:
                category_list.append(category.prestashop_id)
            
            if len(category_list) > 1:
                cat_dict = []
                cat_dict.append({'id': 1})
                cat_dict.append({'id': 2})
                for cat in category_list:
                    cat_dict.append({'id': cat})
                    
                
                    
            elif len(category_list) == 1:
                cat_dict = []
                cat_dict.append({'id': 1})
                cat_dict.append({'id': 2})
                for cat in category_list:
                    cat_dict.append({'id': cat})
            
            print 'len(product_tmpl.presta_feature.ids)      ',len(product_tmpl.presta_feature.ids)
            
#                 feature_dict = []
#                 for feature in product_tmpl.presta_feature:
#                     if len(product_tmpl.presta_feature.ids) > 1:
#                         
#                         feature_dict.append({'id': feature.parent_id.prestashop_id, 'id_feature_value' : feature.prestashop_value_id})
#                     
#                     else:
#                         feature_dict = {'id': feature.parent_id.prestashop_id, 'id_feature_value' : feature.prestashop_value_id}
            feature_dict = ''
            if product_tmpl.material_id:
                feature_dict = {'id': product_tmpl.material_id.presta_material_id, 'id_feature_value' : product_tmpl.material_id.presta_id}
            
            product_dict =  {'active': '1',
              'additional_shipping_cost': '0.00',
              'advanced_stock_management': '0',
              'associations': {'accessories': {'attrs': {'api': 'products',
                 'nodeType': 'product'},
                'value': ''},
                               
               'categories': {'attrs': {'api': 'categories', 'nodeType': 'category'},
                'category': cat_dict},
               'product_features': {'attrs': {'api': 'product_features','nodeType': 'product_feature'},
                 'product_feature': feature_dict},    
               'product_bundle': {'attrs': {'api': 'products', 'nodeType': 'product'},
                'value': ''},
                'tags': {'attrs': {'api': 'tags', 'nodeType': 'tag'}, 'value': ''}},
                             
              'available_for_order': '1',
              'condition': 'new',
              
              'description': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_description_german if product_tmpl.presta_description_german else ''},
                {'attrs': {'id': '2'}, 'value': product_tmpl.presta_description_english if product_tmpl.presta_description_english else ''}]},
                             
              'description_short': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_description_short_german if product_tmpl.presta_description_short_german else ''},
                {'attrs': {'id': '2'}, 'value': product_tmpl.presta_description_short_english if product_tmpl.presta_description_short_english else ''}]},
                             
                             
              'link_rewrite': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.german_name},
                {'attrs': {'id': '2'}, 'value': product_tmpl.name}]},
              'location': '',
              #'manufacturer_name': {'attrs': {'notFilterable': 'true'},
              #'value': product_tmpl.supplier_name},
              
            'id_manufacturer' : product_tmpl.related_supplier_id.presta_supplier_id,
              
              
            'meta_description': {'language': [{'attrs': {'id': '1'},'value': product_tmpl.presta_meta_description_german if product_tmpl.presta_meta_description_german else ''},
              {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_description_english if product_tmpl.presta_meta_description_english else ''}]},
              
              'meta_keywords': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_meta_keywords_german if product_tmpl.presta_meta_keywords_german else ''},
                {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_keywords_english if product_tmpl.presta_meta_keywords_english else ''}]},
                             
              'meta_title': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_meta_title_german if product_tmpl.presta_meta_title_german else ''},
                {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_title_english if product_tmpl.presta_meta_title_english else ''}]},
                             
              'minimal_quantity': '1',
              'name': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.german_name},
                {'attrs': {'id': '2'}, 'value': product_tmpl.name}]},
                             
              'new': '',
              #'pack_stock_type': '3',
              #'price': product_tmpl.get_small_child.lst_price,
              'id_category_default': product_tmpl.presta_default_category_id.prestashop_id,
              'price': product_tmpl.impact_on_price,
              'id_shop_default': '1',
              #'quantity': {'attrs': {'notFilterable': 'true'}, 'value': '0'},
              'redirect_type': '404',
              'reference': product_tmpl.get_small_child.default_code,
              'show_condition': '0',
              'show_price': '1',
              'state': '1',
              'supplier_reference': '',
              'text_fields': '0',
              'type': {'attrs': {'notFilterable': 'true'}, 'value': 'simple'},
              'unit_price_ratio': '0.000000',
              'unity': '',
              'upc': '',
              'uploadable_files': '0',
              'visibility': 'both',
              'weight': '0.000000',
              'wholesale_price': 0,
              'width': '0.000000'}
            
            for presta in self:
                if presta.state == 'connected':
                    prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                    if product_tmpl.presta_id:
                        
                        product_dict.update({'id': product_tmpl.presta_id})
                        product_dict.pop('link_rewrite')
                        final_dict = {'product': product_dict}
                        #_logger.info("...............     " + str(final_dict) )
                        resp = prestashop.edit('products',final_dict)
    
    
    @api.multi
    def update_all_product_details(self):
        template_ids = self.env['product.template'].search([('presta_id','!=',0)])
        
        done_list = []
        for product_tmpl in template_ids:
            
            product_tmpl = self.env['product.template'].search([('presta_id','=',product_tmpl.presta_id),('presta_id','!=',0)], limit=1)
            if product_tmpl.id not in done_list:
                print 'tmpl_id   ',product_tmpl
                category_list = []
         
                for category in product_tmpl.presta_categories:
                    category_list.append(category.prestashop_id)
                 
                if len(category_list) > 1:
                    cat_dict = []
                    cat_dict.append({'id': 1})
                    cat_dict.append({'id': 2})
                    for cat in category_list:
                        cat_dict.append({'id': cat})
                         
                     
                         
                elif len(category_list) == 1:
                    cat_dict = []
                    cat_dict.append({'id': 1})
                    cat_dict.append({'id': 2})
                    for cat in category_list:
                        cat_dict.append({'id': cat})
                 
                feature_dict = ''
                if product_tmpl.material_id:
                    feature_dict = {'id': product_tmpl.material_id.presta_material_id, 'id_feature_value' : product_tmpl.material_id.presta_id}
                 
                product_dict =  {'active': '1',
                  'additional_shipping_cost': '0.00',
                  'advanced_stock_management': '0',
                  'associations': {'accessories': {'attrs': {'api': 'products',
                     'nodeType': 'product'},
                    'value': ''},
                                    
                   'categories': {'attrs': {'api': 'categories', 'nodeType': 'category'},
                    'category': cat_dict},
                   'product_features': {'attrs': {'api': 'product_features','nodeType': 'product_feature'},
                     'product_feature': feature_dict},    
                   'product_bundle': {'attrs': {'api': 'products', 'nodeType': 'product'},
                    'value': ''},
                    'tags': {'attrs': {'api': 'tags', 'nodeType': 'tag'}, 'value': ''}},
                                  
                  'available_for_order': '1',
                  'condition': 'new',
                   
                  'description': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_description_german if product_tmpl.presta_description_german else ''},
                    {'attrs': {'id': '2'}, 'value': product_tmpl.presta_description_english if product_tmpl.presta_description_english else ''}]},
                                  
                  'description_short': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_description_short_german if product_tmpl.presta_description_short_german else ''},
                    {'attrs': {'id': '2'}, 'value': product_tmpl.presta_description_short_english if product_tmpl.presta_description_short_english else ''}]},
                                  
                                  
                  'link_rewrite': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.german_name},
                    {'attrs': {'id': '2'}, 'value': product_tmpl.name}]},
                  'location': '',
                  #'manufacturer_name': {'attrs': {'notFilterable': 'true'},
                  #'value': product_tmpl.supplier_name},
                   
                'id_manufacturer' : product_tmpl.related_supplier_id.presta_supplier_id,
                   
                   
                'meta_description': {'language': [{'attrs': {'id': '1'},'value': product_tmpl.presta_meta_description_german if product_tmpl.presta_meta_description_german else ''},
                  {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_description_english if product_tmpl.presta_meta_description_english else ''}]},
                   
                  'meta_keywords': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_meta_keywords_german if product_tmpl.presta_meta_keywords_german else ''},
                    {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_keywords_english if product_tmpl.presta_meta_keywords_english else ''}]},
                                  
                  'meta_title': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.presta_meta_title_german if product_tmpl.presta_meta_title_german else ''},
                    {'attrs': {'id': '2'}, 'value': product_tmpl.presta_meta_title_english if product_tmpl.presta_meta_title_english else ''}]},
                                  
                  'minimal_quantity': '1',
                  'name': {'language': [{'attrs': {'id': '1'}, 'value': product_tmpl.german_name},
                    {'attrs': {'id': '2'}, 'value': product_tmpl.name}]},
                                  
                  'new': '',
                  #'pack_stock_type': '3',
                  #'price': product_tmpl.get_small_child.lst_price,
                  'id_category_default': product_tmpl.presta_default_category_id.prestashop_id,
                  'price': product_tmpl.impact_on_price,
                  'id_shop_default': '1',
                  #'quantity': {'attrs': {'notFilterable': 'true'}, 'value': '0'},
                  'redirect_type': '404',
                  'reference': product_tmpl.get_small_child.default_code,
                  'show_condition': '0',
                  'show_price': '1',
                  'state': '1',
                  'supplier_reference': '',
                  'text_fields': '0',
                  'type': {'attrs': {'notFilterable': 'true'}, 'value': 'simple'},
                  'unit_price_ratio': '0.000000',
                  'unity': '',
                  'upc': '',
                  'uploadable_files': '0',
                  'visibility': 'both',
                  'weight': '0.000000',
                  'wholesale_price': 0,
                  'width': '0.000000'}
                 
                for presta in self:
                    if presta.state == 'connected':
                        prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                        if product_tmpl.presta_id:
                             
                            product_dict.update({'id': product_tmpl.presta_id})
                            product_dict.pop('link_rewrite')
                            final_dict = {'product': product_dict}
                            _logger.info("Update all mother details.......................      " + str(product_tmpl.art_no) + ' ' + str(product_tmpl.color_name.encode('utf8')) )
                            resp = prestashop.edit('products',final_dict)
                
                
            
            done_list.append(product_tmpl.id)
        
    @api.multi
    def update_sale_price(self):
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                products = self.env['product.product'].search([('presta_child_id','!=',0)])
                #products = self.env['product.product'].search([('id','=',12575)])
                print 'products  ',products
                error_data = ''
                for product in products:
                    if product.presta_child_id and product.product_tmpl_id.presta_id:
                        #try:
                        child_dict = {'combination': {'associations': {
                                                   'product_option_values': {'attrs': {'api': 'product_option_values',
                                                     'nodeType': 'product_option_value'},
                                                    'product_option_value': [{'id': product.product_tmpl_id.get_color_id.prestashop_id}, {'id': product.attribute_value_ids[0].prestashop_id}]
                                                    }},
                                                  'ean13': product.barcode,
                                                  'id_product': product.product_tmpl_id.presta_id,
                                                  #'default_on' : default_on,
                                                  'minimal_quantity': '1',
                                                  'price': product.child_impact_on_price,
                                                  'reference': product.default_code,
                                                  'id': product.presta_child_id,
                                                  'wholesale_price': product.standard_price}}
                        child_resp = prestashop.edit('combinations', child_dict)
                        _logger.info("Prestashop Exporting normal sale price    ..............." + str(product.default_code) )
                        #except:
                        #    pass
                        #    _logger.info("Prestashop Exporting normal sale price errorrrrrrrrrrrrrrrr    ..............." + str(product.default_code) )
        return True
    
    @api.multi
    def update_sale_compute_price(self):
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                products = self.env['product.product'].search([('presta_child_id','!=',0)])
                #products = self.env['product.product'].search([('id','=',12575)])
                print 'products  ',products
                error_data = ''
                for product in products:
                    if product.presta_child_id and product.product_tmpl_id.presta_id:
                        try:
                            presta_price = 0.0
                            if product.presta_price_push > 0:
                                presta_price = product.presta_price_push
                            else:
                                presta_price = product.compute_sale_price / 1.19
                                
                            child_dict = {'combination': {'associations': {
                                                       'product_option_values': {'attrs': {'api': 'product_option_values',
                                                         'nodeType': 'product_option_value'},
                                                         'product_option_value': [{'id': product.product_tmpl_id.get_color_id.prestashop_id}, {'id': product.attribute_value_ids[0].prestashop_id}]
                                                        }},
                                                      'ean13': product.barcode,
                                                      'id_product': product.product_tmpl_id.presta_id,
                                                      #'default_on' : default_on,
                                                      'minimal_quantity': '1',
                                                      'price': presta_price,
                                                      'reference': product.default_code,
                                                      'id': product.presta_child_id,
                                                      'wholesale_price': product.standard_price}}
                            child_resp = prestashop.edit('combinations', child_dict)
                        except:
                            pass
        return True
                                   
    @api.multi
    def export_product_specific_prices(self,variant):
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                
                #specific_prices = prestashop.get('specific_prices')
                #print 'specific_prices    ',specific_prices
                #specific_prices     {'specific_price': {'reduction_type': 'amount', 'id_cart': '0', 'reduction_tax': '1', 
                #        'id_country': '0', 'to': '0000-00-00 00:00:00', 'id_shop': '0', 'price': '-1.000000', 'reduction': '10.000000', 'from_quantity': '1', 
                #        'id_customer': '0', 'id_product_attribute': '742', 'id_specific_price_rule': '0', 'id_currency': '0', 'id_product': '46', 'from': '0000-00-00 00:00:00', 
                #        'id_group': '0', 'id': '8', 'id_shop_group': '0'}}
                
                if variant:
                    if variant.presta_child_id and variant.presta_specific_price > 0:
                        price_dict = {'reduction_type': 'amount', 'reduction_tax': '1', 'id_customer': '0','from': '0000-00-00 00:00:00', 'to': '0000-00-00 00:00:00', 
                        'id_shop': '0', 'price': '-1.000000', 'reduction': variant.presta_specific_price, 'from_quantity': '1', 'id_currency': '0','id_country': '0',
                        'id_product_attribute': variant.presta_child_id, 'id_specific_price_rule': '0', 'id_product': variant.product_tmpl_id.presta_id, 'id_cart': '0','id_group': '0',
                         'id_shop_group': '0'}
                        
                        if variant.presta_specific_price_id:
                            price_dict.update({ 'id' : variant.presta_specific_price_id})
                        
                        if 'id' in price_dict:
                            specific_prices   =  {'specific_price': price_dict}
                            specific_prices_resp = prestashop.edit('specific_prices', specific_prices)
                            print 'updating specific_prices_resp           ',specific_prices_resp
                            
                        else:
                            specific_prices   =  {'specific_price': price_dict}
                            specific_prices_resp = prestashop.add('specific_prices', specific_prices)
                            print 'creating new specifiv price       ',specific_prices_resp
                            variant.write({'presta_specific_price_id' : specific_prices_resp['prestashop']['specific_price'].get('id')})
                
        return True
    
    
    @api.multi
    def export_product_specific_prices_new(self):
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                
                #specific_prices = prestashop.get('specific_prices')
                #print 'specific_prices    ',specific_prices
                #specific_prices     {'specific_price': {'reduction_type': 'amount', 'id_cart': '0', 'reduction_tax': '1', 
                #        'id_country': '0', 'to': '0000-00-00 00:00:00', 'id_shop': '0', 'price': '-1.000000', 'reduction': '10.000000', 'from_quantity': '1', 
                #        'id_customer': '0', 'id_product_attribute': '742', 'id_specific_price_rule': '0', 'id_currency': '0', 'id_product': '46', 'from': '0000-00-00 00:00:00', 
                #        'id_group': '0', 'id': '8', 'id_shop_group': '0'}}
                
                #percentage
                variants = self.env['presta.price'].search([('presta_id','!=',False),('presta_child_id','!=',False)])
                for variant in variants:
                    
                    if variant.presta_child_id:
                        price_dict = {'reduction_type': 'amount', 'reduction_tax': '1', 'id_customer': '0','from': '0000-00-00 00:00:00', 'to': '0000-00-00 00:00:00', 
                            'id_shop': '0', 'price': '-1.000000', 'reduction': variant.price, 'from_quantity': '1', 'id_currency': '0','id_country': '0',
                            'id_product_attribute': variant.presta_child_id, 'id_specific_price_rule': '0', 'id_product': variant.presta_id, 'id_cart': '0','id_group': '0',
                             'id_shop_group': '0'}
                        if variant.price != 0 and variant.price_percent == 0:
                            price_dict['reduction_type'] = 'amount'
                            price_dict['reduction'] = variant.price
                        
                        if variant.price_percent != 0 and variant.price == 0:
                            price_dict['reduction_type'] = 'percentage'
                            price_dict['reduction'] = variant.price_percent
                            
                        
                        if variant.date_from:
                            #from_date = variant.date_from + ' 00:00:00'
                            price_dict.update({'from': variant.date_from})
                        if variant.date_to:
                            #to_date = variant.date_to + ' 23:59:59'
                            price_dict.update({'to': variant.date_to})
                        
                        #never uncommet this section
#                         price_dict = {'reduction_type': 'amount', 'reduction_tax': '1', 'id_customer': '0','from': '0000-00-00 00:00:00', 'to': '0000-00-00 00:00:00', 
#                         'id_shop': '0', 'price': '-1.000000', 'reduction': variant.presta_specific_price, 'from_quantity': '1', 'id_currency': '0','id_country': '0',
#                         'id_product_attribute': variant.presta_child_id, 'id_specific_price_rule': '0', 'id_product': variant.product_tmpl_id.presta_id, 'id_cart': '0','id_group': '0',
#                          'id_shop_group': '0'}
                        #uptill here
                        
                        if variant.presta_specific_price_id:
                            price_dict.update({ 'id' : variant.presta_specific_price_id})
                            specific_prices   =  {'specific_price': price_dict}
                            specific_prices_resp = prestashop.edit('specific_prices', specific_prices)
                            _logger.info("updating Exporting specific price    ..............." + str(specific_prices_resp) )
                        else:
                            specific_prices   =  {'specific_price': price_dict}
                            specific_prices_resp = prestashop.add('specific_prices', specific_prices)
                            _logger.info("***** creating  Exporting specific price    ..............." + str(specific_prices_resp) )
                            variant.write({'presta_specific_price_id' : specific_prices_resp['prestashop']['specific_price'].get('id')})
                
        return True
    
    
    @api.multi
    def export_all_product_specific_prices(self):
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                
                #specific_prices = prestashop.get('specific_prices')
                #print 'specific_prices    ',specific_prices
                #specific_prices     {'specific_price': {'reduction_type': 'amount', 'id_cart': '0', 'reduction_tax': '1', 
                #        'id_country': '0', 'to': '0000-00-00 00:00:00', 'id_shop': '0', 'price': '-1.000000', 'reduction': '10.000000', 'from_quantity': '1', 
                #        'id_customer': '0', 'id_product_attribute': '742', 'id_specific_price_rule': '0', 'id_currency': '0', 'id_product': '46', 'from': '0000-00-00 00:00:00', 
                #        'id_group': '0', 'id': '8', 'id_shop_group': '0'}}
                variants = self.env['product.product'].search([('presta_child_id','!=',0)])
                for variant in variants:
                    if variant:
                        if variant.presta_child_id and variant.presta_specific_price > 0:
                            _logger.info("Prestashop Exporting specific price    ..............." + str(variant.default_code) )
                            price_dict = {'reduction_type': 'amount', 'reduction_tax': '1', 'id_customer': '0','from': '0000-00-00 00:00:00', 'to': '0000-00-00 00:00:00', 
                            'id_shop': '0', 'price': '-1.000000', 'reduction': variant.presta_specific_price, 'from_quantity': '1', 'id_currency': '0','id_country': '0',
                            'id_product_attribute': variant.presta_child_id, 'id_specific_price_rule': '0', 'id_product': variant.product_tmpl_id.presta_id, 'id_cart': '0','id_group': '0',
                             'id_shop_group': '0'}
                            
                            if variant.presta_specific_price_id:
                                price_dict.update({ 'id' : variant.presta_specific_price_id})
                            
                            if 'id' in price_dict:
                                specific_prices   =  {'specific_price': price_dict}
                                specific_prices_resp = prestashop.edit('specific_prices', specific_prices)
                                print 'updating specific_prices_resp           ',specific_prices_resp
                                
                            else:
                                specific_prices   =  {'specific_price': price_dict}
                                specific_prices_resp = prestashop.add('specific_prices', specific_prices)
                                print 'creating new specifiv price       ',specific_prices_resp
                                variant.write({'presta_specific_price_id' : specific_prices_resp['prestashop']['specific_price'].get('id')})
                
        return True
           
    @api.multi
    def push_color_size(self):
        #size = 4 color = 5 id
        
        for presta in self:
#             prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
#             product_option_values = prestashop.get('product_option_values')
#             product_option_value_list = []
#             for product_option_value in product_option_values['product_option_values']['product_option_value']:
#                 product_option_value_list.append(product_option_value['attrs'].get('id'))
#                    
#             print 'product_option_value_list     ',product_option_value_list
#                
#             for product_value in product_option_value_list: 
#                 value_resp = prestashop.get('product_option_values',product_value)
#                 print 'value_resp value_resp     ',value_resp
#                 value = value_resp['product_option_value']['name']['language'][0]['value']
#                 presta_id = value_resp['product_option_value']['id']
#                  
#                 odoo_value = self.env['product.color'].search([('name','=',value)])
#                 if odoo_value:
#                     odoo_value.write({'prestashop_id':presta_id})
                
                

            
            
            
            prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
               
            attributes = self.env['product.attribute.value'].search([('prestashop_id','=',False)])
            if attributes:
                for attribute in attributes:
                    value_dict = {'product_option_value': {'color': '',
                                      'id_attribute_group': '1',
                                      'name': {'language': [{'attrs': {'id': '1'}, 'value': attribute.name},
                                        {'attrs': {'id': '2'}, 'value': attribute.name}]},
                                      'position': ''}}
                        
                    value_resp = prestashop.add('product_option_values', value_dict)
                    print 'value_resp   ',value_resp
                    if value_resp:
                        attribute.write({'prestashop_id': value_resp['prestashop']['product_option_value']['id']})
              
            colors = self.env['product.color'].search([])
            if colors:
                for color in colors:
                    #5
                    if color.prestashop_id:
                        color_dict = {'product_option_value': {'color': '',
                                          'id_attribute_group': '2',
                                          'id': color.prestashop_id,
                                          'name': {'language': [{'attrs': {'id': '1'}, 'value': color.name},
                                            {'attrs': {'id': '2'}, 'value': color.english_name or color.name}]},
                                          'position': ''}}
                          
                        color_resp = prestashop.edit('product_option_values', color_dict)
                        
                    if not color.prestashop_id:
                        color_dict = {'product_option_value': {'color': '',
                                          'id_attribute_group': '2',
                                          'name': {'language': [{'attrs': {'id': '1'}, 'value': color.name},
                                            {'attrs': {'id': '2'}, 'value': color.english_name or color.name}]},
                                          'position': ''}}
                          
                        color_resp = prestashop.add('product_option_values', color_dict)
                        if color_resp:
                            color.write({'prestashop_id': color_resp['prestashop']['product_option_value']['id']})
                    
                    
                        
                     
             
        
         
        return True     
    
    
    @api.multi
    def import_customer(self):
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                customers = prestashop.get('customers')
                
                
                prestashop_customer_list = []
                for customer in customers['customers']['customer']:
                    prestashop_customer_list.append(customer['attrs'].get('id'))
                
                
                
                for customer in prestashop_customer_list:
                    customer_resp = prestashop.get('customers',customer)
                
    
    @api.multi
    def import_address(self, presta_id, address_type=''):
        if presta_id:
            for presta in self:
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                addresses = prestashop.get('addresses',presta_id)
                partner_invoice = False
                partner_delivery = False
                if address_type == 'Invoice':
                    partner_vals = {
                                    'first_name'            : addresses['address'].get('firstname'),
                                    'last_name'             : addresses['address'].get('lastname'),
                                    'shopware_company_name' : addresses['address'].get('company'),
                                    'street'                : addresses['address'].get('address1'),
                                    'street2'               : addresses['address'].get('address2'),
                                    'city'                  : addresses['address'].get('city'),
                                    'zip'                   : addresses['address'].get('postcode'),
                                    'phone'                 : addresses['address'].get('phone'),
                                    'mobile'                : addresses['address'].get('phone_mobile'),
                                    'presta_address_id'     : addresses['address'].get('id'),
                                    'customer'              : True
                    }
                    
                    if partner_vals.get('first_name') and partner_vals.get('last_name'):
                        partner_vals.update({'name': partner_vals.get('first_name') +' '+ partner_vals.get('last_name')})
                    elif partner_vals.get('first_name'):
                        partner_vals.update({'name': partner_vals.get('first_name')})
                    
                    customers = prestashop.get('customers',addresses['address'].get('id_customer'))
                    
                    if customers:
                        partner_vals.update({
                                            'presta_customer_id'    : customers['customer'].get('id'),
                                            'website'               : customers['customer'].get('webiste'),
                                            'email'                 : customers['customer'].get('email')
                            })
                    
                    countries = prestashop.get('countries',addresses['address'].get('id_country'))
                    
                    if countries.get('country'):
                        odoo_country = self.env['res.country'].search([('code','=',countries['country'].get('iso_code'))], limit=1)
                        if odoo_country:
                            partner_vals.update({'country_id': odoo_country.id})
                    
                    partner_invoice = self.env['res.partner'].search([('presta_address_id','=',addresses['address'].get('id')),('presta_customer_id','=',customers['customer'].get('id'))], limit=1)
                    
                    if partner_invoice:
                        partner_invoice.write(partner_vals)
                        return partner_invoice
                    
                    if not partner_invoice:
                        partner_invoice = self.env['res.partner'].create(partner_vals)
                        return partner_invoice
                
                if address_type == 'Delivery':
                    
                    delivery_vals = {
                                    'first_name'            : addresses['address'].get('firstname'),
                                    'last_name'             : addresses['address'].get('lastname'),
                                    'shopware_company_name' : addresses['address'].get('company'),
                                    'street'                : addresses['address'].get('address1'),
                                    'street2'               : addresses['address'].get('address2'),
                                    'city'                  : addresses['address'].get('city'),
                                    'zip'                   : addresses['address'].get('postcode'),
                                    'phone'                 : addresses['address'].get('phone'),
                                    'mobile'                : addresses['address'].get('phone_mobile'),
                                    'presta_address_id'     : addresses['address'].get('id'),
                                    'customer'              : True,
                                    'type'                  : 'delivery'
                    }
                    
                    parent_id = self.env['res.partner'].search([('presta_customer_id','=', addresses['address'].get('id_customer'))],limit=1)
                    if parent_id: 
                        delivery_vals.update({'parent_id': parent_id.id})
                    
                    if delivery_vals.get('first_name') and delivery_vals.get('last_name'):
                        delivery_vals.update({'name': delivery_vals.get('first_name') +' '+ delivery_vals.get('last_name')})
                    elif delivery_vals.get('first_name'):
                        delivery_vals.update({'name': delivery_vals.get('first_name')})
                    
                    customers = prestashop.get('customers',addresses['address'].get('id_customer'))
                    
                    if customers:
                        delivery_vals.update({
                                            #'presta_customer_id'    : customers['customer'].get('id'),
                                            'website'               : customers['customer'].get('webiste'),
                                            'email'                 : customers['customer'].get('email')
                            })
                    
                    countries = prestashop.get('countries',addresses['address'].get('id_country'))
                    if countries.get('country'):
                        odoo_country = self.env['res.country'].search([('code','=',countries['country'].get('iso_code'))], limit=1)
                        if odoo_country:
                            delivery_vals.update({'country_id': odoo_country.id})
                    
                    partner_delivery = self.env['res.partner'].search([('presta_address_id','=',addresses['address'].get('id')),('type','=','delivery')], limit=1)
                    
                    if partner_delivery:
                        partner_delivery.write(delivery_vals)
                        return partner_delivery
                    
                    if not partner_delivery:
                        partner_delivery = self.env['res.partner'].create(delivery_vals)
                        return partner_delivery
              
    @api.multi
    def import_order(self):
        for presta in self:
            if presta.state == 'connected':
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                partner_pool = self.env['res.partner']
                sale_pool = self.env['sale.order']
                line_pool = self.env['sale.order.line']
                prod_pool = self.env['product.product']
                orders = prestashop.get('orders')
                
                
                prestashop_order_list = []
                for prod in orders['orders']['order']:
                    #if int(prod['attrs'].get('id')) > 7150002:
                    #if int(prod['attrs'].get('id')) == 11:
                    prestashop_order_list.append(prod['attrs'].get('id'))
                
                
                for order in prestashop_order_list:
                    order_resp = prestashop.get('orders',order)
                    sale_order = self.env['sale.order'].search([('presta_id','=',order_resp['order'].get('id'))], limit=1)
                    print '>>>>>>>>>>>>     ',order_resp
                    print 'total_shipping total_shipping      ',type(order_resp['order']['total_shipping'])
                    if not sale_order:
                 
                 
                        order_vals = {
                                        'name'                  : order_resp['order']['reference'],
                                        'date_order'            : order_resp['order']['date_add'],
                                        'presta_date_time'      : order_resp['order']['date_add'],
                                        'presta_id'             : order_resp['order']['id'],
                                        'presta_order_total'    : order_resp['order']['total_paid'],
                                        'is_presta'             : True,
                                        'presta_shop'           : order_resp['order']['id_shop'],
                                        'presta_reference'      : order_resp['order']['reference']
                            }
                        
                        
                         
                        current_state = self.env['prestashop.order.state'].search([('prestashop_id','=',order_resp['order']['current_state'])])
                        if current_state:
                            order_vals.update({'presta_order_state': current_state.id})
                         
                        partner_invoice = partner_pool.search([('presta_address_id','=',order_resp['order']['id_address_invoice']),('presta_customer_id','=',order_resp['order']['id_customer'])],limit=1)
                        if partner_invoice:
                            partner_invoice = self.import_address(order_resp['order']['id_address_invoice'],'Invoice')
                            order_vals.update({'partner_invoice_id': partner_invoice.id, 'partner_id': partner_invoice.id})
                        else:
                            partner_invoice = self.import_address(order_resp['order']['id_address_invoice'],'Invoice')
                            order_vals.update({'partner_invoice_id': partner_invoice.id, 'partner_id': partner_invoice.id})
                         
                         
                        partner_delivery = partner_pool.search([('presta_address_id','=',order_resp['order']['id_address_delivery'])],limit=1)
                        if partner_delivery:
                            partner_delivery = self.import_address(order_resp['order']['id_address_delivery'],'Delivery')
                            order_vals.update({'partner_shipping_id': partner_delivery.id})
                        else:
                            partner_delivery = self.import_address(order_resp['order']['id_address_delivery'],'Delivery')
                            order_vals.update({'partner_shipping_id': partner_delivery.id})
                         
                         
                        sale_order = sale_pool.create(order_vals)
                        
                        product_uom = self.env['product.uom.categ'].search([('name','=','Unit')])
                        if isinstance (order_resp['order']['associations']['order_rows']['order_row'], list):
                            order_row = order_resp['order']['associations']['order_rows']['order_row']
                        else:
                            order_row = [order_resp['order']['associations']['order_rows']['order_row']]
                        
                        for order_line in order_row:
                            print 'order_line order_lineorder_line               ',order_line
                            product = self.env['product.product'].search([('presta_child_id','=',order_line.get('product_attribute_id'))], limit=1)
                            if product:
                                name = product.name_get()[0][1]
                                if product.description_sale:
                                    name += '\n' + product.description_sale
                                tax_list = []
                                for tax in product.taxes_id:
                                    tax_list.append(tax.id)
                                line_vals = {
                                                            'order_id'          : sale_order.id,
                                                            'product_id'        : product.id,
                                                            'name'              : name,
                                                            'product_uom_qty'   : order_line['product_quantity'],
                                                            'price_unit'        : order_line['unit_price_tax_incl'], 
                                                            'product_uom'       : product_uom.id if product_uom else False  #unit
                                                             
                                                        }
                                if tax_list:
                                    line_vals['tax_id'] = [[6, 0, tax_list]]
                                line_pool.create(line_vals)
                            else:
                                sale_order.write({'is_missing' : True})
                                missing_line = self.env['sale.line.missing'].search([('sale_id','=',sale_order.id),('sku','=',str(order_line['product_reference']))])
                                if not missing_line:
                                    self.env['sale.line.missing'].create({'sale_id' : sale_order.id, 'name' : order_line['product_name'], 'sku' : str(order_line['product_reference']),'qty':order_line['product_quantity'], 'price_unit' :order_line['unit_price_tax_incl']})
                        
                        if float(order_resp['order']['total_shipping']) >  0:
                            prod_ship_id = prod_pool.search([('name','ilike','Versand')])
                            if not prod_ship_id:
                                raise UserError(_('Versand  !', 'Product with name Versand does not exist.... '))
                            
                            ship_vals = { 
                                                'order_id'           : sale_order.id,
                                                'product_id'         : prod_ship_id and prod_ship_id.id or False,
                                                'name'               : 'Versand',
                                                'product_uom_qty'    : 1,
                                                'price_unit'         : order_resp['order']['total_shipping'],
                                                'product_uom'        : product_uom.id, #unit
                                        }
                            line_pool.create(ship_vals)
                        
                        self.env.cr.commit()
                        
                        
                        #code for automatic pakdo creation
                        flag_list = []
                        partner = sale_order.partner_id
                         
                        name_len = len(partner.name)
                        if name_len > 30:
                            flag_list.append('False')
                         
                        street_number = []
                         
                        for s in partner.street:
                            if s.isdigit():
                                street_number.append('True')
                         
                        if 'True' in street_number:
                            street_len = len(partner.street) - partner.street.count(' ') 
                            if street_len < 5:
                                flag_list.append('False')
                         
                        zip_len = len(partner.zip) - partner.zip.count(' ')
                        if zip_len != 5:
                            flag_list.append('False')
                         
                        if not 'False' in flag_list:
                            print 'automatic pakdo creation'
                            pakdo = self.env['pakdo.config'].search([])
         
                            #Push order code
                            conn = pakdo.test_connection()[0]
                            token = conn[0]
                            session = conn[-1]
                            print 'token token token      ',token
                            headers = {'Authorization': 'Token token='+token}
                             
                            #unixtime_order_date = time.mktime(self.order_date.timetuple())
                            unixtime_order_date = time.mktime(datetime.strptime(sale_order.order_date, "%Y-%m-%d").timetuple())
                             
                            order_data = {"client_order_number":sale_order.name,"date":unixtime_order_date,"payment_date":unixtime_order_date,"gender":"0","firm":False,"first_name":sale_order.partner_id.name,"last_name":False,
                                          "mail":sale_order.partner_id.email,"country":sale_order.partner_id.country_id.code if sale_order.partner_id.country_id else "DE","city":sale_order.partner_id.city,"zip":sale_order.partner_id.zip,"street":sale_order.partner_id.street1,"street_2": sale_order.partner_id.street2 if sale_order.partner_id.street2 else False,
                                          "house_number":False,
                                          "region":sale_order.partner_id.state_id.name if sale_order.partner_id.state_id else '',
                                          'separate_picking':''}
                             
                             
                            sku_list = []
                            qty_list = []
                            price_list = []
                            vat_list = []
                            line_lists = []
                            for line in sale_order.order_line:
                                if line.product_id.barcode and line.product_id.type == 'product':
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
                                    if line.product_id.pakdo_qty < line.product_uom_qty:
                                        raise UserError(_(line.product_id.default_code + ' has Qty less.Required Qty ' + str(line.product_uom_qty) + ' but Pakdo has qty ' + str(line.product_id.pakdo_qty)))
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
                                    raise UserError(_(resp_dict.get('error')[0]))
                                 
                                for l in line_lists:
                                    l.write({'shipped_type':'pakdo'})
                                user = self.env['res.users'].browse(self.env.uid)
                                vals = {
                                            'body': u'<p><br/>Pakdo Order <b>%s</b> Created <br/> By <b>%s</b> at <b>%s</b></p><br/>' %(sale_order.name ,user.name, datetime.today()), 
                                            'model': 'sale.order', 
                                            'res_id': sale_order.id, 
                                            'subtype_id': False, 
                                            'author_id': user.partner_id.id, 
                                            'message_type': 'comment', }        
                                 
                                self.env['mail.message'].create(vals)
                                _logger.info('Pakdo Push order created successfully........ from presta automatic creation')
                            except:
                                if 'error' in resp_dict:
                                    raise UserError(_('Please try after some times, other process in que.....or ' + str(resp_dict.get('error')[0])))
                                else:
                                    raise UserError(_('Please try after some times, other process in que.....'))
                                 
                        
                        
                        
                        
                        
    @api.multi
    def import_order_states(self):
        
        for presta in self:
            prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
            order_states = prestashop.get('order_states')
            print 'order_states',order_states
            prestashop_order_state_list = []
            for prod in order_states['order_states']['order_state']:
                prestashop_order_state_list.append(prod['attrs'].get('id'))
            
            
            for state in prestashop_order_state_list:
                order_state_resp = prestashop.get('order_states',state)
                print 'order_state_resp order_state_resp     ',order_state_resp
                order_state_vals = {
                            'prestashop_id'     : order_state_resp['order_state']['id'],
                            'name'              : order_state_resp['order_state']['name']['language'][1]['value'],
                            'name_german'       : order_state_resp['order_state']['name']['language'][0]['value'],
                }
                odoo_order_state = self.env['prestashop.order.state'].search([('prestashop_id','=',order_state_resp['order_state']['id'])])
                if not odoo_order_state:
                    self.env['prestashop.order.state'].create(order_state_vals)
                print '*********************************************************************'
    
    @api.multi
    def push_trackingcode(self, sale):
        #if sale and not sale.tracking_code_push:
        if sale:
            for presta in self:
                prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
                today = datetime.now()
                today = today.strftime("%Y-%m-%d %H:%M:%S")
                
                #Getting
                try:
                    ship_get = prestashop.get('order_carriers', sale.presta_id)
                except:
                    raise UserError(_('Shipping is not generated in prestashop.'))
                
                #Updating
                try:
                    shipping_vals = {'order_carrier': {'date_add': today,
                                      'id': ship_get['order_carrier']['id'],
                                      'id_carrier': ship_get['order_carrier']['id_carrier'],
                                      'id_order': sale.presta_id,
                                      #'id_order_invoice': '2',
                                      #'shipping_cost_tax_excl': '1.000000',
                                      #'shipping_cost_tax_incl': '1.000000',
                                      'tracking_number': sale.pakdo_tracking_code
                                      #'weight': '0.000000'
                                      }}
                    
                    ship_resp = prestashop.edit('order_carriers', shipping_vals)
                    sale_vals = {'tracking_code_push' : True}
                    
        #                 presta_order = self.env['prestashop.order.state'].search([('name','=','Shipped')])
        #                 if presta_order:
        #                     sale_vals.update({'presta_order_state': presta_order.id})
        #                     order_vals = {'order': {
        #                               'id_address_delivery': str(sale.partner_shipping_id.presta_address_id),
        #                               'id_address_invoice': str(sale.partner_invoice_id.presta_address_id),
        #                               'id_cart': '1',
        #                               'reference': sale.name,
        #                               'id_currency': '1',
        #                               'id_customer': str(sale.partner_id.presta_customer_id),
        #                               'id_lang': '1',
        #                               'id_shop': '1',
        #                               'id_shop_group': '1',
        #                               'current_state': str(presta_order.prestashop_id),
        #                               'id': sale.presta_id,
        #                               'id_shop': '1',
        #                               'id_shop_group': '1',
        #                               'id_carrier': '2',
        #                               }}
        # 
        #                     order_resp = prestashop.edit('orders', order_vals)
        
                    sale.write(sale_vals)
                    
                    
                except:
                    raise UserError(_('Tracking code cannot pushed to prestashop.'))
        return True
    
    @api.model
    def push_trackingcode_cron(self, use_new_cursor=False):
        sales = self.env['sale.order'].search([('is_presta','=',True),('tracking_code_push','=',False),('pakdo_tracking_code','!=',False)])
        _logger.info('Push tracking code '+str(sales))
        for sale in sales:
            _logger.info('Push tracking code '+str(sale))
            presta = self.env['prestashop.config'].search([], limit=1)[0]
            
            prestashop = PrestaShopWebServiceDict(presta.url, presta.api_key)
            today = datetime.now()
            today = today.strftime("%Y-%m-%d %H:%M:%S")
        
        
            #Getting
            #try:
            ship_get = prestashop.get('order_carriers', sale.presta_id)
            _logger.info('Push tracking code '+str(ship_get))
            #except:
            #    raise UserError(_('Shipping is not generated in prestashop.'))
            
            #Updating
            #try:
            shipping_vals = {'order_carrier': {'date_add': today,
                              'id': ship_get['order_carrier']['id'],
                              'id_carrier': ship_get['order_carrier']['id_carrier'],
                              'id_order': sale.presta_id,
                              #'id_order_invoice': '2',
                              #'shipping_cost_tax_excl': '1.000000',
                              #'shipping_cost_tax_incl': '1.000000',
                              'tracking_number': sale.pakdo_tracking_code
                              #'weight': '0.000000'
                              }}
            
            ship_resp = prestashop.edit('order_carriers', shipping_vals)
            _logger.info('Push tracking code '+str(ship_resp))
            sale.write({'tracking_code_push' : True})
            #except:
            #    raise UserError(_('Tracking code cannot pushed to prestashop.'))
        

    @api.multi
    def null_presta_stock_id(self):
        stocks = self.env['pakdo.presta.stock'].search([])
        if stocks:
            for stock in stocks:
                stock.write({'presta_stock_id':False})
        
class PrestashopCategory(models.Model):
    _name = 'prestashop.category'
    
    name                 = fields.Char('Name')
    name_german          = fields.Char('German Name') 
    prestashop_id        = fields.Integer('Prestashop ID')
    parent_id            = fields.Many2one('prestashop.category','Parent Category')
    prestashop_parent_id = fields.Integer('Prestashop Parent ID')
    
    meta_description     = fields.Text('Meta Description English')
    meta_description_german     = fields.Text('Meta Description German')
    
    meta_keywords        = fields.Char('Meta Keywords English')
    meta_keywords_german        = fields.Char('Meta Keywords German')
    
    meta_title           = fields.Char('Meta Title English')
    meta_title_german           = fields.Char('Meta Title German')
    is_english           = fields.Boolean('Is English')
    is_german           = fields.Boolean('Is German')
    
            
    @api.multi
    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.parent_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.parent_id
            return res

        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]
    

class PrestashopFeature(models.Model):
    _name = 'prestashop.feature'
    
    name                 = fields.Char('Name')
    name_german          = fields.Char('German Name') 
    prestashop_id        = fields.Integer('Prestashop ID')
    prestashop_value_id  = fields.Integer('Prestashop value ID')
    parent_id            = fields.Many2one('prestashop.feature','Parent Category')
    prestashop_parent_id = fields.Integer('Prestashop Parent ID')
    
    
    is_english           = fields.Boolean('Is English')
    is_german           = fields.Boolean('Is German')
    
            
    @api.multi
    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.parent_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.parent_id
            return res

        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]

class PrestashopOrderstate(models.Model):
    _name = 'prestashop.order.state'
    
    name                 = fields.Char('Name')
    name_german          = fields.Char('German Name') 
    prestashop_id        = fields.Integer('Prestashop ID')
    
        
   