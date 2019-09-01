from odoo import models,fields,api,_
from googletrans import Translator
class SaleOrder(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def get_arabic_vals(self):
        translator = Translator()
        inv_number = ''
        date = ''
        origin = ''
        lpo = ''
        comment = ''
        for data in self:
            if data.number:
                list1 = data.number.split('/')
                for val in list1:
                    print(val)
                    print(translator.translate(val, dest='ar').text)
                    if val == 'INV':
                       inv_number = 'INV'+ '/' + translator.translate(val, dest='ar').text
                    else:
                        inv_number = inv_number + '/' + translator.translate(val, dest='ar').text
                data.number_ar = inv_number
            if data.date_invoice:
                list2 = str(data.date_invoice).split('-')
                for val in list2:
                    date = date  +'/' +translator.translate(val, dest='ar').text
                data.date_invoice_ar = date
            if data.origin:
                if 'SO' in data.origin:
                  origin = translator.translate(data.origin.replace('SO',''), dest='ar').text
                data.origin_ar = 'SO' + origin
            if data.lpo:
                if 'PO' in data.origin:
                    lpo = translator.translate(data.lpo.replace('PO', ''), dest='ar').text
                data.origin_ar = 'PO' + lpo
            if data.comment:
                list3 = data.comment.split('\n')
                for val in list3:
                    comment = comment +  translator.translate(val, dest='ar').text + '\n'
                data.comments_ar = comment



    number_ar = fields.Char('Number arabic',compute='get_arabic_vals')
    date_invoice_ar = fields.Char('date arabic',compute='get_arabic_vals')
    origin_ar = fields.Char('Origin arabic',compute='get_arabic_vals')
    lpo = fields.Char('Local Purchase Order')
    lpo_ar = fields.Char('Local Purchase Order',compute='get_arabic_vals')
    comments_ar = fields.Char('Comments',compute='get_arabic_vals')


    @api.multi
    def get_comments(self):
        comment = []
        if self.comment:
            comment = self.comment.split('\n')
        return comment
    @api.multi
    def get_comments_ar(self):
        comment = []
        if self.comments_ar:
           comment = self.comments_ar.split('\n')
        return comment
