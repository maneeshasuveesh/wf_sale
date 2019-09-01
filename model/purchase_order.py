from odoo import models,fields,api,_
from odoo.exceptions import UserError
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def get_manager_access(self):
        if self.env.user.has_group('sales_team.group_sale_manager'):
            self.is_manager =True
            print(self.is_manager)

    is_manager = fields.Boolean('manager', compute='get_manager_access', default=False)
    enquiry_id = fields.Many2one('sale.enquiry', 'Enquiry Ref')
    sent_for_approval = fields.Boolean('Sent for approval', default=False)
    approved = fields.Boolean('Approved', default=False)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent_for_approval', 'Sent For Approval'),
        ('approved', 'Approved'),
        ('sent', 'Quotation Sent'),
        ('to_approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange',
        default='draft')
    lc_id = fields.Many2one('letter.credit', 'L/C Ref')
    payment_type = fields.Selection([
        ('normal', 'Normal'),
        ('lc', 'L/C'),
    ], string='Payment Type',
        default='normal')

    @api.multi
    def action_sent_for_approval(self):
        self.sent_for_approval = True
        self.state = 'sent_for_approval'

    @api.multi
    def action_approve(self):
        self.approved = True
        self.state = 'approved'

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent','approved']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                        and order.amount_total < self.env.user.company_id.currency_id._convert(
                        order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                        order.date_order or fields.Date.today())) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.lc_id:
                if order.lc_id.state != 'done':
                    raise UserError('L/C Credit For Sale is not Confirmed!')

        return True