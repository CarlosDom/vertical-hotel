from openerp.tests.common import TransactionCase
from openerp.tools import mute_logger, float_round
from openerp.exceptions import ValidationError


class TestHotelFolio(TransactionCase):
    """Tests for folio (hotel.folio)
    """

    def setUp(self):
        super(TestHotelFolio, self).setUp()
        # self.folio_model = self.registry('hotel.folio')
        self.folioObj = self.env['hotel.folio']
        self.saleOrderObj = self.env['sale.order']
        self.saleOrderLineObj = self.env['sale.order.line']
        self.invoiceObj = self.env['account.invoice']
        self.voucherObj = self.env['account.voucher']
        self.product_product = self.registry('product.product')
        self.product_pricelist = self.registry('product.pricelist')
        self.uom = self.env['product.uom']

    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_folio_create(self):
        '''Creating Folio'''
        folio1 = self.folioObj.create({
            'partner_id': 1,
            'partner_invoice_id': 1,
            'partner_shipping_id': 1,
            'checkin_date': '2015-07-20 11:04:38',
            'checkout_date': '2015-07-28 11:04:38',
            'duration': 8,
            'date_order': '2015-07-20 11:04:54.09324',
            'pricelist_id': 1,
            'room_lines': [(0, 0, {
                'product_id': 7,
                'name': 'Test Room',
                'checkin_date': '2015-07-20 11:04:38',
                'checkout_date': '2015-07-28 11:04:38',
                'product_uom_qty': 8,
                'price_unit': 200.00,
                'product_uom': self.uom
            })],
            'service_lines': [(0, 0, {
                'product_id': 0,
                'name': 'Test Service',
                'product_uom_qty': 1,
                'price_unit': 100.00
            })]
        })

        self.assertTrue(folio1, 'Error: folio not created')

    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_folio_flow(self):
        '''Workflow Folio'''
        folio1 = self.folioObj.create({
            'partner_id': 1,
            'partner_invoice_id': 1,
            'partner_shipping_id': 1,
            'checkin_date': '2015-07-20 11:04:38',
            'checkout_date': '2015-07-28 11:04:38',
            'duration': 8,
            'date_order': '2015-07-20 11:04:54.09324',
            'pricelist_id': 1,
            'room_lines': [(0, 0, {
                'product_id': 7,
                'name': 'Test Room',
                'checkin_date': '2015-07-20 11:04:38',
                'checkout_date': '2015-07-28 11:04:38',
                'product_uom_qty': 8,
                'price_unit': 200.00,
                'product_uom': self.uom
            })],
            'service_lines': [(0, 0, {
                'product_id': 0,
                'name': 'Test Service',
                'product_uom_qty': 1,
                'price_unit': 100.00
            })]
        })

        sale_order_line1 = self.saleOrderLineObj.create({
            'product_uom': 1,
            'price_unit': 200.00,
            'product_uom_qty': 4.000,
            'name': 'Test Room',
            'delay': 0,
            'state': 'draft',
            'order_id': folio1.id
        })
        self.saleOrderObj.browse(folio1.id).action_button_confirm()
        '''Check if the order has been confirmed correctly'''
        self.assertEqual(self.saleOrderObj.browse(folio1.id).state,
                         'manual',
                         'Folio is in wrong state')

        self.saleOrderObj.browse(folio1.id).action_invoice_create()
        '''Check if order has invoice created'''
        self.assertEqual(self.saleOrderObj.browse(folio1.id).state,
                         'progress',
                         'Folio is in wrong state')

        self.cr.execute('SELECT invoice_id \
                         FROM sale_order_invoice_rel \
                         WHERE order_id = cast(%s as integer)',
                        (str(folio1.id)))
        res = self.cr.fetchone()
        print res
        self.invoiceObj.browse(res).invoice_validate()
        '''Check if invoice is validated'''
        self.assertEqual(self.invoiceObj.browse(res).state,
                         'open',
                         'Folio is in wrong state')

        self.invoiceObj.browse(res).invoice_pay_customer()
        self.cr.execute("""SELECT voucher_id
                         FROM account_voucher_line as v, account_invoice_line as i
                         WHERE v.voucher_id = i.invoice_id""")
        res2 = self.cr.fetchone()
        print res2
        self.voucherObj.browse(res2).button_proforma_voucher()
        '''Check if invoice has been paid'''
        self.assertEqual(self.invoiceObj.browse(res).state,
                         'paid',
                         'Folio is in wrong state')