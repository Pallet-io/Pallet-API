import httplib
import mock

from django.test import TestCase

from gcoinrpc.exceptions import InvalidParameter


class GetAssetInfoTest(TestCase):
    def setUp(self):
        self.url = "/base/v1/asset/2"
        self.sample_asset_info = {
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
    def test_get_asset_info(self, mock_rpc):
        mock_rpc().getassetinfo.return_value = self.sample_asset_info

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json(), self.sample_asset_info)

    def test_wrong_http_method(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, httplib.METHOD_NOT_ALLOWED)

    @mock.patch('base.v1.views.get_rpc_connection')
    def test_asset_not_exist(self, mock_rpc):
        mock_rpc().getassetinfo.side_effect = InvalidParameter({'code': -8, 'message': 'License color not exist.'})

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)

