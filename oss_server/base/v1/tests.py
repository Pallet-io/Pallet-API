import httplib
import mock

from django.test import TestCase
from gcoinrpc.data import TransactionInfo
from gcoinrpc.exceptions import InvalidParameter, WalletError


class GetRawTxTest(TestCase):

    def setUp(self):
        self.url = '/base/v1/transaction/c53cd739cbfd95705393602c76f954962bdf9f86686bf861c0f15aea5716bd1e'
        sample_transaction = {
            'vout': [{
                'color': 0,
                'scriptPubKey': {
                    'reqSigs': 1,
                    'hex': '2102958e42b2466eebf112d33afc9231189ff5f7f0537b50bda81432c527c943da1bac',
                    'addresses': ['1A7R8nWmDv4DR7x2ZFyxPt4rBCc3ZBViQF'],
                    'asm': '02958e42b2466eebf112d33afc9231189ff5f7f0537b50bda81432c527c943da1b OP_CHECKSIG',
                    'type': 'pubkey'
                },
                'value': 0,
                'n': 0
            }],
            'blockhash': '00000cf2acf8ff6bf0c0d01cf9044161e9a320a36234a61742640fe7bd3d6679',
            'hex': '01000000010000000000000000000000000000000000000000000000000000000000000000'
                   'ffffffff49483045022100f2b9b4ef2324f1d7bcfe0c5b4eea1667655fc819ec6e5f1b8c30'
                   'c763c1e7876b02200b1e53ffa336fa2fa4a474f98eff62b97672efd71cd569927511a32013'
                   '50ce4f01ffffffff010000000000000000232102958e42b2466eebf112d33afc9231189ff5'
                   'f7f0537b50bda81432c527c943da1bac00000000d5a3465700000000',
            'vin': [{
                'coinbase': '483045022100f2b9b4ef2324f1d7bcfe0c5b4eea1667655fc819ec6e5f1b8c30c7'
                            '63c1e7876b02200b1e53ffa336fa2fa4a474f98eff62b97672efd71cd569927511'
                            'a3201350ce4f01',
                'scriptSig': {
                    'hex': '483045022100f2b9b4ef2324f1d7bcfe0c5b4eea1667655fc819ec6e5f1b8c30c763'
                           'c1e7876b02200b1e53ffa336fa2fa4a474f98eff62b97672efd71cd569927511a320'
                           '1350ce4f01',
                    'asm': '3045022100f2b9b4ef2324f1d7bcfe0c5b4eea1667655fc819ec6e5f1b8c30c763c1e'
                           '7876b02200b1e53ffa336fa2fa4a474f98eff62b97672efd71cd569927511a3201350'
                           'ce4f01'
                },
                'sequence': 4294967295
            }],
            'txid': 'c53cd739cbfd95705393602c76f954962bdf9f86686bf861c0f15aea5716bd1e',
            'blocktime': 1464247255,
            'version': 1,
            'confirmations': 4,
            'time': 1464247255,
            'locktime': 1464247253,
            'type': 'NORMAL',
            'size': 176
        }

        self.sample_transaction = TransactionInfo(**sample_transaction)

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_get_raw_transaction(self, mock_rpc):
        mock_rpc().getrawtransaction.return_value = self.sample_transaction

        response = self.client.get(self.url)
        self.assertEqual(response.json(), self.sample_transaction.__dict__)
        self.assertEqual(response.status_code, httplib.OK)

    def test_wrong_http_method(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, httplib.METHOD_NOT_ALLOWED)

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_invalid_parameter(self, mock_rpc):
        mock_rpc().getrawtransaction.side_effect = InvalidParameter({'code': -8,
                                                                     'message': 'test invalid parameter'})

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_invalid_address_or_key(self, mock_rpc):
        mock_rpc().getrawtransaction.side_effect = InvalidParameter({'code': -5,
                                                                     'message': 'test invalid address or key'})

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)


class GetBalanceTest(TestCase):

    def setUp(self):
        self.url = '/base/v1/balance/1NYbzjaq486dGjuXz1Kiu9L7PY6svgaDn7'
        self.sample_txoutaddress = [
            {
                'txid': 'tx_id', 'vout': 0, 'color': 1, 'value': 1
            },
            {
                'txid': 'tx_id', 'vout': 1, 'color': 1, 'value': 998999
            }
        ]
        self.sample_balance = {'1': 999000}
        self.wrong_address_url = '/base/v1/balance/123321'

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_get_balance(self, mock_rpc):
        mock_rpc().gettxoutaddress.return_value = self.sample_txoutaddress
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json(), self.sample_balance)

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_get_wrong_address_balance(self, mock_rpc):
        mock_rpc().gettxoutaddress.return_value = None
        response = self.client.get(self.wrong_address_url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json(), {})


class CreateRawTxTest(TestCase):

    def setUp(self):
        self.url = '/base/v1/transaction/prepare'
        self.sample_txoutaddress = [
            {'txid': 'b67399d1d520a8646a592485c9f2004bd7e79729354cc0717101c3b1fa0a1e15',
             'vout': 0,
             'color': 1,
             'value': 2,
             'scriptPubKey': '2103dd5ed2dd68648b0a77a4a7f3e23c35e05f311e14e73a8012304f0e22ce3ae23fac'},
            {'txid': '6324183149d9093e7454ec9f3141b8d3d543431ebc7f2e22dd00528de72b8351',
             'vout': 0,
             'color': 2,
             'value': 10,
             'scriptPubKey': '76a914232e8540e8a3ff0b688854def11147970e7b6ce188ac'},
        ]
        self.sample_txoutaddress_without_fee = [
            {'txid': '6324183149d9093e7454ec9f3141b8d3d543431ebc7f2e22dd00528de72b8351',
             'vout': 0,
             'color': 2,
             'value': 10,
             'scriptPubKey': '76a914232e8540e8a3ff0b688854def11147970e7b6ce188ac'},
        ]
        self.from_address = '17nJ6HR8aiNhNf6f7UTm5fRT6DDGCCJ9Rt'
        self.to_address = '1MnwbemNqG4d41iGy6CeQGCPgigzLX3vyL'

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_create_raw_tx_using_color1(self, mock_rpc):
        mock_rpc().gettxoutaddress.return_value = self.sample_txoutaddress
        response = self.client.get(self.url, {'from_address': self.from_address,
                                              'to_address': self.to_address,
                                              'color_id': 1,
                                              'amount': 1})
        self.assertEqual(response.status_code, httplib.OK)
        self.assertIn('raw_tx', response.json())

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_create_raw_tx_using_other_color(self, mock_rpc):
        mock_rpc().gettxoutaddress.return_value = self.sample_txoutaddress
        response = self.client.get(self.url, {'from_address': self.from_address,
                                              'to_address': self.to_address,
                                              'color_id': 2,
                                              'amount': 10})
        self.assertEqual(response.status_code, httplib.OK)
        self.assertIn('raw_tx', response.json())

    # Test insufficient fee
    @mock.patch('base.v1.views.get_rpc_connection')
    def test_create_raw_tx_with_color1_without_sufficient_fee(self, mock_rpc):
        mock_rpc().gettxoutaddress.return_value = self.sample_txoutaddress
        response = self.client.get(self.url, {'from_address': self.from_address,
                                              'to_address': self.to_address,
                                              'color_id': 1,
                                              'amount': 2})
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
        self.assertEqual(response.json(), {'error': 'insufficient fee'})

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_create_raw_tx_with_color1_without_sufficient_fee(self, mock_rpc):
        mock_rpc().gettxoutaddress.return_value = self.sample_txoutaddress_without_fee
        response = self.client.get(self.url, {'from_address': self.from_address,
                                              'to_address': self.to_address,
                                              'color_id': 2,
                                              'amount': 10})
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
        self.assertEqual(response.json(), {'error': 'insufficient fee'})

    # Test insufficient funds
    @mock.patch('base.v1.views.get_rpc_connection')
    def test_create_raw_tx_with_color1_without_sufficient_funds(self, mock_rpc):
        mock_rpc().gettxoutaddress.return_value = self.sample_txoutaddress
        response = self.client.get(self.url, {'from_address': self.from_address,
                                              'to_address': self.to_address,
                                              'color_id': 1,
                                              'amount': 3})
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
        self.assertEqual(response.json(), {'error': 'insufficient funds'})

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_create_raw_tx_with_color1_without_sufficient_funds(self, mock_rpc):
        mock_rpc().gettxoutaddress.return_value = self.sample_txoutaddress
        response = self.client.get(self.url, {'from_address': self.from_address,
                                              'to_address': self.to_address,
                                              'color_id': 2,
                                              'amount': 11})
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
        self.assertEqual(response.json(), {'error': 'insufficient funds'})

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_create_raw_tx_with_amount_exceed_8_decimal_digit(self, mock_rpc):
        mock_rpc().gettxoutaddress.return_value = self.sample_txoutaddress
        response = self.client.get(self.url, {'from_address': self.from_address,
                                              'to_address': self.to_address,
                                              'color_id': 1,
                                              'amount': 0.123456789})
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
        self.assertEqual(response.json(), {'error': '`amount` only allow up to 8 decimal digits'})

    def test_missing_form_data(self):
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)


class SendRawTxTest(TestCase):

    def setUp(self):
        self.url = '/base/v1/transaction/send'

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_send_raw_tx(self, mock_rpc):
        tx_id = 'b67399d1d520a8646a592485c9f2004bd7e79729354cc0717101c3b1fa0a1e15'
        mock_rpc().sendrawtransaction.return_value = tx_id

        response = self.client.post(self.url, {'raw_tx': 'aaaabbbbccccddddeeeeffff'})
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json(), {'tx_id': tx_id})

    def test_wrong_http_method(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, httplib.METHOD_NOT_ALLOWED)

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_exception(self, mock_rpc):
        mock_rpc().sendrawtransaction.side_effect = Exception()

        response = self.client.post(self.url, {'raw_tx': ''})
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
