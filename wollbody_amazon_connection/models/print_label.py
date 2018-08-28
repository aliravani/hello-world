# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

import odoo.addons.decimal_precision as dp


import os
import base64
from PIL import Image
import barcode
from barcode.writer import ImageWriter
from StringIO import StringIO
from barcode import generate

barcode.PROVIDED_BARCODES
[u'code39', u'code128', u'ean', u'ean13', u'ean8', u'gs1', u'gtin',
 u'isbn', u'isbn10', u'isbn13', u'issn', u'jan', u'pzn', u'upc', u'upca']


class PrintLabel(models.Model):
    _name = "print.label"
    
    name          = fields.Char('Search Product')
    amazon_name   = fields.Char('Amazon Name', size=124)
    supplier_id   = fields.Many2one('res.partner','Supplier')
    art_name      = fields.Char('Article Name')
    art_no        = fields.Char('Article Number')
    color_no      = fields.Char('Color number')
    size          = fields.Char('Size')
    color_name    = fields.Char('Color')
    material_id   = fields.Many2one('article.material','Material')
    image         = fields.Binary('Image')
    fnsku         = fields.Char('FNSKU') 
    barcode_img   = fields.Binary('Barcode')   
    logo          = fields.Binary('Logo')
    
    @api.multi
    def _get_barcode(self, data):
        
        # name = generate('EAN13', barcode, output='barcode')
        EAN = barcode.get_barcode_class('code128')
        ean = EAN(data, writer=ImageWriter())
        try:
            name = ean.save('ean13_barcode')
            filetmp = os.getcwd()+'/'+name
        except:
            filetmp = ean.save('/home/openerp/barcode/ean13_barcode')
        
        im = Image.open(filetmp)
        size = 1500, 1500
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(filetmp, "png")
        with open(filetmp, "rb") as image_file:
            encoded_string=base64.b64encode(image_file.read())
        return encoded_string
    
    @api.multi
    def do_search(self):
        vals = {}
        product_obj = self.env['product.product'].sudo().search(['|','|','|','|',('default_code','=',self.name),('get_int_no','ilike',self.name),('barcode','=',self.name),('asin','=',self.name),('fnsku','=',self.name)], limit=1)
        error_msg = ''
        if product_obj:
            self.write({'barcode_img': False})
            vals.update(
                    {
                      'supplier_id'         : product_obj.related_supplier_id.id,
                      'art_name'            : product_obj.art_name,
                      'art_no'              : product_obj.art_no,
                      'color_no'            : product_obj.color_no,
                      'size'                : product_obj.get_size,
                      'color_name'          : product_obj.color_name,
                      'material_id'         : product_obj.material_id.id,
                      'image'               : product_obj.image_medium,
                      'fnsku'               : product_obj.fnsku,
                      'amazon_name'         : product_obj.amazon_name,
                      'logo'                : product_obj.related_supplier_id.company_id.logo,
                    }
                )
            
            label_obj = self.env['print.label'].search([('fnsku','=',product_obj.fnsku)], limit=1)
            
            if label_obj:
                raise UserError(_('Record already exists....'))
                return False
            
            if not label_obj:
                if product_obj.fnsku:
                    barocde_str = self._get_barcode(product_obj.fnsku)
                    vals.update({
                                'barcode_img': unicode(barocde_str, "utf-8"),
                        })
                self.write(vals)
        else:
            raise UserError(_('Record not found....'))
            return False
        
        return True


class PrintLabellilano(models.Model):
    _name = "print.label.lilano"
    
    name          = fields.Char('Search Product')
    amazon_name   = fields.Char('Amazon Name', size=55)
    supplier_id   = fields.Many2one('res.partner','Supplier')
    art_name      = fields.Char('Article Name')
    art_no        = fields.Char('Article Number')
    color_no      = fields.Char('Color number')
    size          = fields.Char('Size')
    color_name    = fields.Char('Color')
    material_id   = fields.Many2one('article.material','Material',size=22)
    image         = fields.Binary('Image')
    fnsku         = fields.Char('FNSKU') 
    barcode_img   = fields.Binary('Barcode')
    barcode_img2   = fields.Binary('Barcode 2')   
    logo          = fields.Binary('Logo')
    
    @api.multi
    def _get_barcode(self, data):
        
        # name = generate('EAN13', barcode, output='barcode')
        EAN = barcode.get_barcode_class('code128')
        ean = EAN(data, writer=ImageWriter())
        try:
            name = ean.save('ean13_barcode')
            filetmp = os.getcwd()+'/'+name
        except:
            filetmp = ean.save('/home/openerp/barcode/ean13_barcode')
        
        im = Image.open(filetmp)
        size = 1500, 1500
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(filetmp, "png")
        with open(filetmp, "rb") as image_file:
            encoded_string=base64.b64encode(image_file.read())
        return encoded_string
    
    @api.multi
    def do_search(self):
        vals = {}
        product_obj = self.env['product.product'].sudo().search(['|','|','|','|',('default_code','=',self.name),('get_int_no','ilike',self.name),('barcode','=',self.name),('asin','=',self.name),('fnsku','=',self.name)], limit=1)
        print 'product_obj product_obj   ',product_obj
        error_msg = ''
        if product_obj:
            self.write({'barcode_img': False, 'barcode_img2': False})
            art_no = ''
            if product_obj.art_no_original:
                art_no = product_obj.art_no_original
            else:
                art_no = product_obj.art_no
                
            vals.update(
                    {
                      'supplier_id'         : product_obj.related_supplier_id.id,
                      'art_name'            : product_obj.art_name,
                      'art_no'              : art_no,
                      'color_no'            : product_obj.color_no,
                      'size'                : product_obj.get_size,
                      'color_name'          : product_obj.color_name,
                      'material_id'         : product_obj.material_id.id,
                      'image'               : product_obj.image_medium,
                      'fnsku'               : product_obj.fnsku,
                      'amazon_name'         : product_obj.amazon_name,
                      'logo'                : product_obj.related_supplier_id.image
                    }
                )
            
            label_obj = self.env['print.label.lilano'].search([('fnsku','=',product_obj.fnsku)], limit=1)
            print 'label_obj label_obj        ',label_obj
            
#             if label_obj:
#                 raise UserError(_('Record already exists....'))
#                 return False
            
            #if not label_obj:
            if product_obj.fnsku:
                barocde_str = self._get_barcode(product_obj.art_no + product_obj.color_no + product_obj.get_size)
                vals.update({
                            'barcode_img': unicode(barocde_str, "utf-8"),
                    })
            
            if product_obj.get_int_no:
                barocde_str2 = self._get_barcode(product_obj.get_int_no)
                vals.update({
                            'barcode_img2': unicode(barocde_str2, "utf-8"),
                    })
                
            self.write(vals)
        else:
            raise UserError(_('Record not found....'))
            return False
        
        return True

class PrintBarcode(models.Model):
    _name = "print.barcode"
    
    name          = fields.Char('Search Product')
    art_no        = fields.Char('Article Number')
    color_no      = fields.Char('Color number')
    size          = fields.Char('Size')
    
    
    image         = fields.Binary('Image')
    barcode         = fields.Char('Barcode') 
    barcode_img   = fields.Binary('Barcode')   
    logo          = fields.Binary('Logo')
    
    @api.multi
    def _get_barcode(self, data):
        
        # name = generate('EAN13', barcode, output='barcode')
        #EAN = barcode.get_barcode_class('ean13')
        EAN = barcode.get_barcode_class('code128')
        ean = EAN(data, writer=ImageWriter())
        try:
            name = ean.save('ean13_barcode_print')
            filetmp = os.getcwd()+'/'+name
        except:
            filetmp = ean.save('/home/openerp/barcode/ean13_barcode_print')
        
        im = Image.open(filetmp)
        size = 1500, 1500
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(filetmp, "png")
        with open(filetmp, "rb") as image_file:
            encoded_string=base64.b64encode(image_file.read())
        return encoded_string
    
    @api.multi
    @api.onchange('name')
    def onchange_name(self):
        vals = {}
        if not self.name:
            self.art_no = False
            self.color_no = False
            self.size = False
            self.barcode = False
            self.logo = False
        
        if self.name:
            product_obj = self.env['product.product'].sudo().search(['|','|','|',('default_code','=',self.name),('get_int_no','ilike',self.name),('barcode','=',self.name),('fnsku','=',self.name)], limit=1)
            if product_obj:
                self.barcode_img = False
                vals.update(
                    {
                      'art_no'              : product_obj.art_no,
                      'color_no'            : product_obj.color_no,
                      'size'                : product_obj.get_size,
                      'barcode'             : product_obj.barcode,
                      'logo'                : product_obj.related_supplier_id.company_id.logo,
                    }
                )
                label_obj = self.env['print.barcode'].search([('barcode','=',product_obj.barcode)], limit=1)
                
                if label_obj:
                    raise UserError(_('Record already exists....'))
                    return False
                
                if not label_obj:
                    if product_obj.barcode:
                        barocde_str = self._get_barcode(product_obj.barcode)
                        vals.update({
                                    'barcode_img': unicode(barocde_str, "utf-8"),
                                    
                            })
                    self.update(vals)
            else:
                raise UserError(_('Record not found....'))
                return False
        
            
    @api.multi
    def do_search(self):
        vals = {}
        product_obj = self.env['product.product'].sudo().search(['|','|','|',('default_code','=',self.name),('get_int_no','ilike',self.name),('barcode','=',self.name),('fnsku','=',self.name)], limit=1)
        error_msg = ''
        if product_obj:
            self.write({'barcode_img': False})
            vals.update(
                    {
                      #'supplier_id'         : product_obj.related_supplier_id.id,
                      'art_no'              : product_obj.art_no,
                      'color_no'            : product_obj.color_no,
                      'size'                : product_obj.get_size,
                      'barcode'             : product_obj.barcode,
                      'logo'                : product_obj.related_supplier_id.company_id.logo,
                    }
                )
            
            label_obj = self.env['print.barcode'].search([('barcode','=',product_obj.barcode)], limit=1)
            
            if label_obj:
                raise UserError(_('Record already exists....'))
                return False
            
            if not label_obj:
                if product_obj.barcode:
                    barocde_str = self._get_barcode(product_obj.barcode)
                    vals.update({
                                'barcode_img': unicode(barocde_str, "utf-8"),
                        })
                self.write(vals)
        else:
            raise UserError(_('Record not found....'))
            return False
        
        return True




class PrintFNSKU(models.Model):
    _name = "print.fnsku"
    
    name          = fields.Char('Search Product')
    art_no        = fields.Char('Article Number')
    color_no      = fields.Char('Color number')
    art_name      = fields.Char('Article Name')
    size          = fields.Char('Size')
    amazon_name   = fields.Char('Amazon Name',size=124)
    
    image         = fields.Binary('Image')
    fnsku         = fields.Char('FNSKU')
     
    fnsku_img   = fields.Binary('FNSKU')   
    logo          = fields.Binary('Logo')
    supplier_id   = fields.Many2one('res.partner','Supplier')
    color_name    = fields.Char('Color')
      
    
    @api.multi
    def _get_barcode(self, data):
        
        # name = generate('EAN13', barcode, output='barcode')
        EAN = barcode.get_barcode_class('code128')
        ean = EAN(data, writer=ImageWriter())
        try:
            name = ean.save('ean13_barcode')
            filetmp = os.getcwd()+'/'+name
        except:
            filetmp = ean.save('/home/openerp/barcode/ean13_barcode')
        
        im = Image.open(filetmp)
        size = 1500, 1500
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(filetmp, "png")
        with open(filetmp, "rb") as image_file:
            encoded_string=base64.b64encode(image_file.read())
        return encoded_string
    
    
    @api.multi
    def do_search(self):
        vals = {}
        product_obj = self.env['product.product'].sudo().search(['|','|','|',('default_code','=',self.name),('get_int_no','ilike',self.name),('barcode','=',self.name),('fnsku','=',self.name)], limit=1)
        error_msg = ''
        if product_obj:
            self.write({'fnsku_img': False})
            vals.update(
                    {
                      'supplier_id'         : product_obj.related_supplier_id.id,
                      'art_name'            : product_obj.art_name,
                      'art_no'              : product_obj.art_no,
                      'color_no'            : product_obj.color_no,
                      'size'                : product_obj.get_size,
                      'color_name'          : product_obj.color_name,
                      'material_id'         : product_obj.material_id.id,
                      'image'               : product_obj.image_medium,
                      'fnsku'               : product_obj.fnsku,
                      'amazon_name'         : product_obj.amazon_name,
                      'logo'                : product_obj.related_supplier_id.company_id.logo,
                    }
                )
            
            label_obj = self.env['print.fnsku'].search([('fnsku','=',product_obj.fnsku)], limit=1)
            
            if label_obj:
                raise UserError(_('Record already exists....'))
                return False
            
            if not label_obj:
                if product_obj.fnsku:
                    barocde_str = self._get_barcode(product_obj.fnsku)
                    vals.update({
                                'fnsku_img': unicode(barocde_str, "utf-8"),
                        })
                self.write(vals)
        else:
            raise UserError(_('Record not found....'))
            return False
        
        return True
    
    