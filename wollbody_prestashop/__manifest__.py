# -*- coding: utf-8 -*-

{
    'name': 'Wollbody Prestashop',
    'category': 'General',
    'summary': 'Wollbody Prestashop Connections',
    'version': '1.0',
    'description': """Wollbody Prestashop Connection""",
    'author': 'Ali Ravani',
    'depends': ['wollbody_amazon_connection','product','sale'],
    'data': [
             'security/ir.model.access.csv',
             'data/cron.xml',
             'views/prestashop_view.xml',
             'views/product_view.xml',
             'views/res_partner_view.xml',
             'views/sale_view.xml',
             'views/pakdo_presta_view.xml',
             
             
    ],
    'installable': True,
}
