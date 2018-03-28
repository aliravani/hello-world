# -*- coding: utf-8 -*-

{
    'name': 'Service Package',
    'category': 'General',
    'summary': 'Service package',
    'version': '1.0',
    'description': """product combo product, pacakge as product in SO and create project-task from it.""",
    'author': 'Ali Ravani (ali.ravani14@gmail.com)',
    'depends': ['project','product','sale'],
    'data': [
             'security/ir.model.access.csv',
             'wizard/create_task_view.xml',
             'data/data_view.xml',
             'views/product_template_view.xml',
             'views/sale_view.xml',
             'views/project_view.xml',
             
    ],
    'installable': True,
}
