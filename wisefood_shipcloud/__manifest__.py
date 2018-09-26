# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Wisefood Shipcloud',
    'version': '1.1',
    'category': 'Sales',
    'summary': 'Wisefood Shipcloud',
    'description': """
    Wisefood Shipcloud
    """,
    'depends': ['sale'],
    'data': [
            'views/shipcloud_view.xml',
            'views/sale_view.xml'
    ],
    
    'installable': True,
    'auto_install': False,
}
