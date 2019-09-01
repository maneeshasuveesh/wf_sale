from odoo import models,fields,api,_
from googletrans import Translator
class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.depends('name','street','street2','state_id','country_id')
    def get_arabic_vals(self):
        translator = Translator()
        street = ''
        street2 = ''
        for data in self:

            if data.street:
                list1 = str(data.street).strip('')
                for val in list1:
                    street = street + '' +translator.translate(val, dest='ar').text
                data.street_ar = street
            if data.street2:
                list2 = str(data.street2).strip('')
                for val in list2:
                    street2 = street2 + '' + translator.translate(val, dest='ar').text
                data.street2_ar = street
            if data.state_id:
                state = translator.translate(data.state_id.name, dest='ar').text
                data.state_ar = state
            if data.country_id:
                country = translator.translate(data.country_id.name, dest='ar').text
                data.country_ar = country
            if data.name:
                name = translator.translate(data.name, dest='ar').text
                data.name_ar = name
    fax = fields.Char('Fax')
    name_ar = fields.Char('Name Arabic',compute='get_arabic_vals',store=True)
    street_ar = fields.Char('Street Arabic',compute='get_arabic_vals',store=True)
    street2_ar = fields.Char('Street2 Arabic',compute='get_arabic_vals',store=True)
    state_ar = fields.Char('State Arabic',compute='get_arabic_vals',store=True)
    country_ar = fields.Char('Country Arabic',compute='get_arabic_vals',store=True)