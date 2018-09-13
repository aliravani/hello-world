# -*- coding: utf-8 -*-

{
    'name': 'Wollbody Amazon Connection',
    'category': 'General',
    'summary': 'Wollbody Amazon Connection',
    'version': '1.0',
    'description': """Wollbody Amazon Connection""",
    'author': 'Ali Ravani',
    'depends': ['sale','product','stock','sale_stock','project_issue'],
    'data': [
             'security/ir.model.access.csv',
             'security/security.xml',
             
             'wizard/csv_update_view.xml',
             'wizard/fba_order_view.xml',
             'wizard/account_invoice_refund_view.xml',
             'wizard/csv_note_view.xml',
             'wizard/csv_template_view.xml',
             'wizard/export_sale_csv_view.xml',
             
             'views/product_template_view.xml',
             'views/product_view.xml',
             'views/amazon_view.xml',
             'views/sale_view.xml',
             'views/extra_menu_hide.xml',
             'views/res_partner_view.xml',
             'views/account_invoice_view.xml',
             'views/project_issue_view.xml',
             
             'views/report_view.xml',
             
             'report/report_printlabel.xml',
             'report/report_printbarcode.xml',
             'report/report_printfnsku.xml',
             'report/report_printlabellilano.xml',
             'report/report_printlabellilano_2.xml',
             'report/layout.xml',
             'report/report_invoice.xml',
             'report/report_salereciept.xml',
             'report/report_reminder.xml',
             
             'views/print_label_view.xml',
             'data/schedular.xml',
             'data/email_template.xml',
             'data/sequence.xml',
    ],
    
    'installable': True,
}
