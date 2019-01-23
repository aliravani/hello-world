# -*- coding: utf-8 -*-

{
    'name': 'Wollbody Pakdo',
    'category': 'General',
    'summary': 'Wollbody Pakdo Connection',
    'version': '1.0',
    'description': """Wollbody Pakdo Connection""",
    'author': 'Ali Ravani',
    'depends': ['wollbody_amazon_connection','product','sale'],
    'data': [
             'security/ir.model.access.csv',
             'wizard/pakdo_order_view.xml',
             
             'views/pakdo_view.xml',
             'views/product_template_view.xml',
             'views/sale_order_view.xml',
             'views/schedular.xml'
             
             
    ],
    'installable': True,
}
