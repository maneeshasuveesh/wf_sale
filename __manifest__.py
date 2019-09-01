{
    "name": "Sale Worflow",
    "version": "12",
    "license": "AGPL-3",
    "author": "",
    "category": "Sales",
    "website": "",
    "depends": ["sale"],
    "data": [
        'security/sale_group.xml',
  'security/ir.model.access.csv',
        'wizard/sale_invoice.xml',
  'data/ir_sequence_data.xml',
  'report/tax_invoice_report.xml',
  'report/tax_invoice_report_template.xml',
  'view/res_company.xml',
  'view/sale_enquiry.xml',
        'view/sale_order.xml',
        'view/letter_of_credit.xml',
        'view/purchase_order.xml',
        'view/account_invoice.xml',


    ],
    "installable": True,
}
