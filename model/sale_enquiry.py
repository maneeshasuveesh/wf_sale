from odoo import fields,models,api,_
from odoo.addons import decimal_precision as dp

class SaleEnquiry(models.Model):
    _name = "sale.enquiry"
    _description = "Sale Enquiry"

    @api.multi
    def get_manager_access(self):
        if self.env.user.has_group('sales_team.group_sale_manager'):
            self.is_manager = True

    @api.multi
    def get_all_approved(self):
        line_count = 0
        approve_count = 0
        for line in self.enquiry_line:
            line_count += 1
            if line.approved:
                  approve_count += 1
        if line_count == approve_count:
            self.all_approved = True
        else:
            self.partially_approved = True
            if approve_count:
               self.state = 'partial'

    @api.depends('enquiry_line')
    def _get_order_ids(self):
        for enquiry in self:
            order_ids = enquiry.enquiry_line.mapped('sale_line_id').mapped('order_id')
            enquiry.update({
                'order_count': len(set(order_ids.ids )),
                'order_ids': order_ids.ids
            })
    name = fields.Char(string='Enquiry Reference', required=True, copy=False, readonly=True,
                       states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    client_order_ref = fields.Char(string='Customer Reference', copy=False)
    state = fields.Selection([
        ('draft', 'Enquiry'),
        ('sent', 'Sent For Approval'),
        ('waiting', 'Waiting'),
        ('partial', 'Partially Approved'),
        ('approved', 'Approved'),
        ('quotation','Quotation'),
        ('done', 'done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')
    date_enquiry = fields.Datetime(string='Enquiry Date',  readonly=True, index=True,
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False,
                                 default=fields.Datetime.now)

    enquiry_line = fields.One2many('sale.enquiry.line', 'enquiry_id', string='Order Lines',
                                 states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True,
                                 auto_join=True)
    order_count = fields.Integer(string='Order Count', compute='_get_order_ids', readonly=True)
    order_ids = fields.Many2many("sale.order", string='Quotations', compute="_get_order_ids", readonly=True,
                                   copy=False)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True,
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True,
                                 change_default=True, index=True, track_visibility='always', track_sequence=1,
                                 help="You can find a customer by its Name, TIN, Email or Internal Reference.")

    all_approved = fields.Boolean('All approved',default=False,compute='get_all_approved')
    partially_approved = fields.Boolean('Partially Approved',default=False,compute='get_all_approved')
    is_manager = fields.Boolean('manager', compute='get_manager_access', default=False)
    @api.multi
    def action_create_quotation(self):

        sale_order = self.env['sale.order'].create({'partner_id':self.partner_id.id,'enquiry_id':self.id,'payment_type':'lc'})
        print(self._context)
        if sale_order:
            sale_line_obj = self.env['sale.order.line']
            for line in self.enquiry_line:
                if line.state in ('available','approved'):
                    so_line = sale_line_obj.create({
                        'price_unit': line.price_unit,
                        'product_uom_qty': line.product_uom_qty,
                        'order_id': sale_order.id,
                        'discount': 0.0,
                        'product_id': line.product_id.id,
                    })
                    line.sale_line_id = so_line.id
        self.state = 'quotation'
        if self._context.get('open_quotation', False):
            return self.action_view_order()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_view_order(self):
        order_ids = self.mapped('order_ids')
        action=  {
            'name':_('Quotation'),
            'domain': [('id', '=', order_ids.ids)],
            'view_type': 'form',
            'res_model': 'sale.order',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }
        return action
    @api.onchange('all_approved')
    def onchange_all_approved(self):
        if self.all_approved:
            self.state = 'approved'



    @api.multi
    def action_cancel(self):
        self.state = 'cancel'

    @api.multi
    def action_approve_all_prices(self):
        for line in self.enquiry_line:
            line.state = 'approved'
            line.approved = True
        self.all_approved = True
        self.state = 'approved'
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.enquiry') or _('New')
        enquiry_line = vals.get('enquiry_line')
        for line in enquiry_line:
            if line[2].get('product_id') and line[2].get('price_unit'):
                product_id = self.env['product.product'].browse(line[2].get('product_id'))
                if product_id:
                    if line[2].get('price_unit') <= product_id.lst_price:
                        line[2].update({'state':'available','approved':True})
                    else:
                        line[2].update({'state': 'draft'})
        vals.update({'enquiry_line':enquiry_line})
        result = super(SaleEnquiry, self).create(vals)
        return result

    @api.multi
    def action_send_for_clarification(self):
        self.state = 'sent'
    @api.multi
    def action_approve(self):
        self.state = 'approved'
class SaleEnquiryLine(models.Model):
    _name = 'sale.enquiry.line'
    _description = 'Sales Enquiry Line'
    _order = 'enquiry_id, id'

    approved = fields.Boolean('Approved',default=False)
    sale_line_id = fields.Many2one('sale.order.line',)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('sale.order'))
    enquiry_id = fields.Many2one('sale.enquiry', string='Enquiry Reference',ondelete='cascade', index=True,
                               copy=False)
    name = fields.Text(string='Description')
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict')
    product_uom_qty = fields.Float(string='Ordered Quantity', digits=dp.get_precision('Product Unit of Measure'),
                                   required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')

    price_unit = fields.Float('Price Proposed', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    state = fields.Selection([
        ('draft', 'Not Available'),
        ('sent', 'Quotation Sent'),
        ('available', 'Available'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, store=True)

    @api.onchange('price_unit','product_id')
    def onchange_price_unit(self):
        for line in self:
            if line.product_id and line.price_unit:
                if line.price_unit <= line.product_id.lst_price:
                    line.state = 'available'
                else:
                    line.state = 'draft'


    @api.multi
    def action_approve(self):
        for line in self:
            if line.state == 'draft':
                line.state = 'approved'
                line.approved = True

    @api.onchange('state')
    def onchange_state(self):
        line_count = 0
        approve_count = 0
        for line in self:
            line_count += 1
            if line.approved:
                approve_count += 1
            if line_count == approve_count:
                line.enquiry_id.all_approved = True
            else:
                line.enquiry_id.partially_approved = True
                if approve_count:
                    line.enquiry_id.state = 'partial'

