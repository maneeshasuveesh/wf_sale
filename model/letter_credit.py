from odoo import fields,models,api,_
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
class LetterofCredit(models.Model):
    _name = "letter.credit"
    _description = "Letter Of Credit"

    @api.depends('state', 'origin.order_line.invoice_status', 'origin.order_line.invoice_lines')
    def _get_invoiced(self):

         for rec in self:
             rec.update({
                 'invoice_count': rec.origin.invoice_count,
                 'invoice_ids': rec.origin.invoice_ids.ids
             })


    name = fields.Char(string='L/C Reference',  copy=False, readonly=True, index=True)
    origin = fields.Many2one('sale.order','Origin',readonly="1")
    vat = fields.Char('VAT/BIN No')
    irc = fields.Char('IRC No')
    tin = fields.Char('TIN No')
    erc = fields.Char('ERC No')
    date_expiry = fields.Date('Date of Expiry')
    lc_date = fields.Date('LC Date')
    bank_name = fields.Char('LC Bank Name',required="1")
    bank_branch = fields.Char('LC Bank Branch',required="1")
    bank_address = fields.Char('Bank Address',require="1")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting'),
        ('ready', 'Ready'),
        ('done', 'done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True,
        default='draft')
    invoice_count = fields.Integer(string='Invoice Count', compute='_get_invoiced', readonly=True)
    invoice_ids = fields.Many2many("account.invoice", string='Invoices', compute="_get_invoiced", readonly=True,
                                   copy=False)


    @api.model
    def create(self, vals):
        vals.update({'name':self.env['ir.sequence'].next_by_code('letter.credit')})
        res = super(LetterofCredit, self).create(vals)
        return res

    @api.multi
    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action



    @api.model
    def default_get(self, fields):
        res = super(LetterofCredit, self).default_get(fields)
        if self._context.get('active_model') == 'sale.order':
            print(self._context.get('active_id'))
            if self._context.get('active_id'):
                res.update({'origin':self.env['sale.order'].browse(self._context.get('active_id')).id})
        return res

    @api.multi
    def action_confirm(self):

        return {
            'type': 'ir.actions.act_window',
            'name': _('Make invoice'),
            'res_model': 'sale.invoice',
            'view_type': 'form',
            'target': 'new',
            'view_mode': 'form',
            'context': {'active_ids': self.origin.ids,'lc_id':self.ids}
        }


    @api.multi
    def action_cancel(self):
        self.state = 'cancel'