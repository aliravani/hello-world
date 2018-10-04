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
    'depends': ['sale','stock'],
    'data': [
            'views/shipcloud_view.xml',
            'views/sale_view.xml',
            'views/product_view.xml',
            'views/res_partner_view.xml',
            'views/control_center_view.xml',
            
            'report/report.xml',
            'report/sale_report_template.xml',
            
            'wizard/bulk_confirm_order_view.xml',
    ],
    
    'installable': True,
    'auto_install': False,
}
