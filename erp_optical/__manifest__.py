# -*- coding: utf-8 -*-

{
    'name': 'ERP for Optical',
    'category': 'General',
    'summary': 'Optical Erp',
    'version': '1.0',
    'description': """Optical Erp system""",
    'author': 'Ali Ravani (ali.ravani14@gmail.com)',
    'depends': ['product','sale_management'],
    'data': [
             'security/ir.model.access.csv',
             
             #'data/ir_sequence_data.xml',
             'views/res_partner_view.xml',
             #'views/easy_checkup_view.xml',
             'views/sale_view.xml',
             'views/product_view.xml',
             #'views/report.xml',
             
             #'report/report_easycheckup.xml',
    ],
    'installable': True,
}
