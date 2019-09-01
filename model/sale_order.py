from odoo import models,fields,api,_

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def get_manager_access(self):
        if self.env.user.has_group('sales_team.group_sale_manager'):
            self.is_manager =True

    @api.depends('po_id')
    def _get_order_ids(self):
        for order in self:
            order_ids = order.mapped('po_id')
            order.update({
                'order_count': len(set(order_ids.ids)),
                'order_ids': order_ids.ids
            })

    order_count = fields.Integer(string='Order Count', compute='_get_order_ids', readonly=True)
    order_ids = fields.Many2many("purchase.order", string='PO', compute="_get_order_ids", readonly=True,
                                 copy=False)
    payment_type = fields.Selection([
        ('normal', 'Normal'),
        ('lc','L/C'),
    ], string='Payment Type',
        default='normal')
    lc_id = fields.Many2one('letter.credit','L/C Ref')
    po_id = fields.Many2one('purchase.order','PO')
    is_manager = fields.Boolean('manager',compute='get_manager_access',default=False)
    enquiry_id = fields.Many2one('sale.enquiry','Enquiry Ref')
    sent_for_approval = fields.Boolean('Sent for approval',default = False)
    approved = fields.Boolean('Approved',default=False)
    customer_approved = fields.Boolean('Customer Approved',default=False)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent_for_approval','Sent For Approval'),
        ('approved','Approved'),
        ('customer_approved','Customer Approved'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange',
        default='draft')

    @api.depends('payment_type')
    def onchange_payment_type(self):
        if self.payment_type and self.payment_type == 'lc':
            domain = {}

            domain['lc_id'] = [('origin', 'in', self.id)]
            return {'domain': domain}



    @api.multi
    def action_view_order(self):

        order_ids = self.mapped('order_ids')
        action = {
            'name': _('Quotation'),
            'domain': [('id', '=', order_ids.ids)],
            'view_type': 'form',
            'res_model': 'purchase.order',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }
        return action


    @api.multi
    def action_sent_for_approval(self):
        self.sent_for_approval = True
        self.state = 'sent_for_approval'

    @api.multi
    def action_approve(self):
        self.approved = True
        self.state = 'approved'

           
    @api.multi
    def action_customer_approved(self):
        self.customer_approved = True
        self.state = 'customer_approved'

    def action_confirm(self):
       super(SaleOrder, self).action_confirm()
       vals = {
              'name':'New',
              'partner_id': self.partner_id.id,
              'origin': self.name,
              'enquiry_id':self.enquiry_id.id,
              'payment_type':self.payment_type
              }
       if self.lc_id:
           vals.update({'lc_id':self.lc_id.id})
       purchase_order = self.env['purchase.order'].create(vals)
       if purchase_order:
           po_line_obj = self.env['purchase.order.line']
           for line in self.order_line:

               product_lang = line.product_id.with_context(
                   lang=self.partner_id.lang,
                   partner_id=self.partner_id.id,
               )
               name = product_lang.display_name
               if product_lang.description_purchase:
                   name += '\n' + product_lang.description_purchase

               po_line = po_line_obj.create({
                   'name':name,
                   'price_unit': line.price_unit,
                   'product_qty': line.product_uom_qty,
                   'order_id': purchase_order.id,
                   'discount': 0.0,
                   'product_uom':line.product_uom_qty,
                   'product_id': line.product_id.id,
                   'date_planned':fields.Datetime.to_string(fields.datetime.now())
               })
           self.po_id = purchase_order.id
       return True