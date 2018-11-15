# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'WooCommerce',
    'version': '1.1',
    'category': 'Sales',
    'summary': 'WooCommerce Api Cconnection',
    'description': """
    WooCommerce Api Cconnection
    """,
    'depends': ['sale','product'],
    'data': [
            #'security/ir.model.access.csv',
            
            'views/woo_config_view.xml',
            
            
    ],
    
    'installable': True,
    'auto_install': False,
}
