import httplib
import mock

from django.test import TestCase
from gcoinrpc.data import TransactionInfo
from gcoinrpc.exceptions import InvalidParameter, WalletError


class GetRawTxTest(TestCase):

    def setUp(self):
        self.url = '/base/v1/transaction/a3fe310b88a904de3d45220fccc974158f9706d844531e8708fbd015bf2e56e3'
        sample_transaction = {
            'vout': [
                {
                    'scriptPubKey': '76a914cc8df42c2580bb319a1c6d14ff96a07f58fa153388ac',
                    'value': 1,
                    'n': 0
                },
                {
                    'scriptPubKey': '76a914cc8df42c2580bb319a1c6d14ff96a07f58fa153388ac',
                    'value': 492,
                    'n': 1
                }
            ],
            'blockhash': '000000213c9f2274f3d0c7e8765c3a2b57b7d26365a8ac47863e10cc7bbf4660',
            'hex': '0100000002b59e25f42fc29e2f15a163e32730819c9d3e88644096a7ac5659173161f9ca31'
                   '010000006b483045022100adee476194436549dd0565a9ba99b9d3bd36d893cddff20ae5e1'
                   '8f43254cb09802200538a4244f38094d5c4d4df0b91b4bacf226e6786d00a0c73da9cbd950'
                   'e6483e0121033c79dc28662e084f6663b165539b2391808edf728e43057184d4d2f64e5d13'
                   '3effffffffb59e25f42fc29e2f15a163e32730819c9d3e88644096a7ac5659173161f9ca31'
                   '000000006b483045022100c00b9fa3634f00fa08e29863bf9e59c8f44711007b0d731093ea'
                   '3983f9e08dcd022034c110b8039c628433460384250b914aec186f296b13ed1a9b9e04f98e'
                   'a1e0e20121033c79dc28662e084f6663b165539b2391808edf728e43057184d4d2f64e5d13'
                   '3effffffff0200e1f505000000001976a914cc8df42c2580bb319a1c6d14ff96a07f58fa15'
                   '3388ac006c8c740b0000001976a914cc8df42c2580bb319a1c6d14ff96a07f58fa153388ac'
                   '00000000',
            'vin': [
                {
                    'tx_hash': '31caf96131175956aca7964064883e9d9c813027e363a1152f9ec22ff4259eb5',
                    'vout': 1,
                    'address': '1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK',
                    'amount': 1,
                    'scriptSig': '483045022100adee476194436549dd0565a9ba99b9d3bd36d893cddff20ae5e18f43254cb09802200538a4244f38094d5c4d4df0b91b4bacf226e6786d00a0c73da9cbd950e6483e0121033c79dc28662e084f6663b165539b2391808edf728e43057184d4d2f64e5d133e',
                    'sequence': '4294967295'
                },
                {
                    'tx_hash': '31caf96131175956aca7964064883e9d9c813027e363a1152f9ec22ff4259eb5',
                    'vout': 0,
                    'address': '1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK',
                    'amount': 493,
                    'scriptSig': '483045022100c00b9fa3634f00fa08e29863bf9e59c8f44711007b0d731093ea3983f9e08dcd022034c110b8039c628433460384250b914aec186f296b13ed1a9b9e04f98ea1e0e20121033c79dc28662e084f6663b165539b2391808edf728e43057184d4d2f64e5d133e',
                    'sequence': '4294967295'
                },

            ],
            'txid': 'a3fe310b88a904de3d45220fccc974158f9706d844531e8708fbd015bf2e56e3',
            'blocktime': 1464247255,
            'version': 1,
            'confirmations': 126,
            'time': 1511242888,
            'locktime': 0,
            'size': 374
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
                'txid': 'tx_id', 'vout': 0, 'value': 1
            },
            {
                'txid': 'tx_id', 'vout': 1, 'value': 998999
            }
        ]
        self.sample_balance = {"balance" : 999000}
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
        self.assertEqual(response.json(), {'balance': 0})


class CreateRawTxTest(TestCase):

    def setUp(self):
        self.url = '/base/v1/transaction/prepare'
        self.sample_txoutaddress = [
            {'txid': 'b67399d1d520a8646a592485c9f2004bd7e79729354cc0717101c3b1fa0a1e15',
             'vout': 0,
             'value': 2,
             'scriptPubKey': '2103dd5ed2dd68648b0a77a4a7f3e23c35e05f311e14e73a8012304f0e22ce3ae23fac'},
            {'txid': '6324183149d9093e7454ec9f3141b8d3d543431ebc7f2e22dd00528de72b8351',
             'vout': 0,
             'value': 10,
             'scriptPubKey': '76a914232e8540e8a3ff0b688854def11147970e7b6ce188ac'},
        ]
        self.from_address = '17nJ6HR8aiNhNf6f7UTm5fRT6DDGCCJ9Rt'
        self.to_address = '1MnwbemNqG4d41iGy6CeQGCPgigzLX3vyL'

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_create_raw_tx_using(self, mock_rpc):
        mock_rpc().gettxoutaddress.return_value = self.sample_txoutaddress
        response = self.client.get(self.url, {'from_address': self.from_address,
                                              'to_address': self.to_address,
                                              'amount': 11})
        self.assertEqual(response.status_code, httplib.OK)
        self.assertIn('raw_tx', response.json())

    # Test insufficient fund
    @mock.patch('base.v1.views.get_rpc_connection')
    def test_create_raw_tx_without_sufficient_fee(self, mock_rpc):
        mock_rpc().gettxoutaddress.return_value = self.sample_txoutaddress
        response = self.client.get(self.url, {'from_address': self.from_address,
                                              'to_address': self.to_address,
                                              'amount': 12})
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
