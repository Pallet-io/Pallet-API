import httplib
import mock

from django.test import TestCase
from gcoinrpc.data import TransactionInfo
from gcoinrpc.exceptions import InvalidParameter


class GetLicenseInfoTest(TestCase):
    def setUp(self):
        self.url = "/base/v1/license/2"
        self.sample_license_info = {
            "member_control": "false",
            "metadata_hash": "0000000000000000000000000000000000000000000000000000000000000000",
            "divisibility": "true",
            "name": "Test",
            "mint_schedule": "free",
            "description": "",
            "metadata_link": "",
            "fee_type": "fixed",
            "version": 1,
            "upper_limit": 0,
            "fee_collector": "",
            "fee_rate": "0E-8",
            "issuer": ""
        }

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_get_license_info(self, mock_rpc):
        mock_rpc().getlicenseinfo.return_value = self.sample_license_info

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json(), self.sample_license_info)

    def test_wrong_http_method(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, httplib.METHOD_NOT_ALLOWED)

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_license_not_exist(self, mock_rpc):
        mock_rpc().getlicenseinfo.side_effect = InvalidParameter({'code': -8, 'message': 'License color not exist.'})

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)


class GetRawTransactionTest(TestCase):
    def setUp(self):
        self.url = "/base/v1/transaction/c53cd739cbfd95705393602c76f954962bdf9f86686bf861c0f15aea5716bd1e"
        sample_transaction = {
            "vout": [{
                "color": 0,
                "scriptPubKey": {
                        "reqSigs": 1,
                        "hex": "2102958e42b2466eebf112d33afc9231189ff5f7f0537b50bda81432c527c943da1bac",
                        "addresses": ["1A7R8nWmDv4DR7x2ZFyxPt4rBCc3ZBViQF"],
                        "asm": "02958e42b2466eebf112d33afc9231189ff5f7f0537b50bda81432c527c943da1b OP_CHECKSIG",
                        "type": "pubkey"
                    },
                "value": 0,
                "n": 0
            }],
            "blockhash": "00000cf2acf8ff6bf0c0d01cf9044161e9a320a36234a61742640fe7bd3d6679",
            "hex": "01000000010000000000000000000000000000000000000000000000000000000000000000"
                   "ffffffff49483045022100f2b9b4ef2324f1d7bcfe0c5b4eea1667655fc819ec6e5f1b8c30"
                   "c763c1e7876b02200b1e53ffa336fa2fa4a474f98eff62b97672efd71cd569927511a32013"
                   "50ce4f01ffffffff010000000000000000232102958e42b2466eebf112d33afc9231189ff5"
                   "f7f0537b50bda81432c527c943da1bac00000000d5a3465700000000",
            "vin": [{
                "coinbase": "483045022100f2b9b4ef2324f1d7bcfe0c5b4eea1667655fc819ec6e5f1b8c30c7"
                            "63c1e7876b02200b1e53ffa336fa2fa4a474f98eff62b97672efd71cd569927511"
                            "a3201350ce4f01",
                "scriptSig": {
                    "hex": "483045022100f2b9b4ef2324f1d7bcfe0c5b4eea1667655fc819ec6e5f1b8c30c763"
                           "c1e7876b02200b1e53ffa336fa2fa4a474f98eff62b97672efd71cd569927511a320"
                           "1350ce4f01",
                    "asm": "3045022100f2b9b4ef2324f1d7bcfe0c5b4eea1667655fc819ec6e5f1b8c30c763c1e"
                           "7876b02200b1e53ffa336fa2fa4a474f98eff62b97672efd71cd569927511a3201350"
                           "ce4f01"
                    },
                "sequence": 4294967295
            }],
            "txid": "c53cd739cbfd95705393602c76f954962bdf9f86686bf861c0f15aea5716bd1e",
            "blocktime": 1464247255,
            "version": 1,
            "confirmations": 4,
            "time": 1464247255,
            "locktime": 1464247253,
            "type": "NORMAL",
            "size": 176
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
        mock_rpc().getrawtransaction.side_effect = InvalidParameter({'code': -8, 'message': 'test invalid parameter'})

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_invalid_address_or_key(self, mock_rpc):
        mock_rpc().getrawtransaction.side_effect = InvalidParameter({'code': -5, 'message': 'test invalid address or key'})

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)

class GetBalanceTest(TestCase):
    def setUp(self):
        self.url = "/base/v1/balance/1NYbzjaq486dGjuXz1Kiu9L7PY6svgaDn7"
        self.sample_txoutaddress = [{
                                        "txid" : "tx_id", "vout" : 0, "color" : 1, "value" : 1
                                    },
                                    {
                                        "txid" : "tx_id", "vout" : 1, "color" : 1, "value" : 998999
                                    }]
        self.sample_balance = {"1": 999000}
        self.wrong_address_url = "/base/v1/balance/123321"

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

