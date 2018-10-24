# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Shopify',
    'version': '1.1',
    'category': 'Sales',
    'summary': 'Shopify Api Cconnection',
    'description': """
    Shopify Api Cconnection
    """,
    'depends': ['sale','product'],
    'data': [
            #'security/ir.model.access.csv',
            
            'views/shopify_view.xml',
            
            
    ],
    
    'installable': True,
    'auto_install': False,
}
