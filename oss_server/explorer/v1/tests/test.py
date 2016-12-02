import httplib
import os

from django.test import TestCase

from explorer.models import *
from explorer.update_db import BlockDBUpdater


def setUpModule():
    # load block file to DB
    updater = BlockDBUpdater(os.path.dirname(os.path.realpath(__file__)))
    updater.update()


def tearDownModule():
    Block.objects.all().delete()
    Datadir.objects.all().delete()


class GetLatestBlocksTest(TestCase):

    def test_get_latest_blocks(self):
        url = '/explorer/v1/blocks'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['blocks']), 50)
        # get the latest block
        block = response.json()['blocks'][0]
        self.assertEqual(block['hash'], '000001618d6fae9349bed836a56422bd161103ff44083bf9ff58358c8d882191')
        self.assertEqual(block['branch'], 'main')
        for i in range(1, 50):
            next_block = response.json()['blocks'][i]
            self.assertEqual(next_block['branch'], 'main')
            self.assertLessEqual(int(next_block['time']), int(block['time']))
            block = next_block


class GetBlockByHashTest(TestCase):

    def test_get_block_by_hash(self):
        url = '/explorer/v1/blocks/000001618d6fae9349bed836a56422bd161103ff44083bf9ff58358c8d882191'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['block']['hash'],
                         '000001618d6fae9349bed836a56422bd161103ff44083bf9ff58358c8d882191')
        self.assertEqual(response.json()['block']['branch'], 'main')

        url = '/explorer/v1/blocks/0000054d57bff2bcd1b82b1e7667ecc40f9273e1f4839955b0aa99f73298f464'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['block']['hash'],
                         '0000054d57bff2bcd1b82b1e7667ecc40f9273e1f4839955b0aa99f73298f464')
        self.assertEqual(response.json()['block']['branch'], 'orphan')

    def test_block_not_found(self):
        url = '/explorer/v1/blocks/000001618d6fae9349bed836a56422bd161103ff44083bf9ff58358c8d000000'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'block not exist'})


class GetBlockByHeightTest(TestCase):

    def test_get_block_by_height(self):
        url = '/explorer/v1/blocks/265'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['block']['hash'],
                         '000001618d6fae9349bed836a56422bd161103ff44083bf9ff58358c8d882191')
        self.assertEqual(response.json()['block']['branch'], 'main')

        # height 240 has two blocks, one in main chain another in fork
        url = '/explorer/v1/blocks/240'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['block']['hash'],
                         '0000043e1ef201ec2a1648c3b1730e86e0237175c2f1fc5aee9b5379111e30af')
        self.assertEqual(response.json()['block']['branch'], 'main')

    def test_block_not_found(self):
        # the block height in the test blk00000.dat is only 265
        url = '/explorer/v1/blocks/266'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'block not exist'})


class GetTxByHashTest(TestCase):

    def test_coinbase_tx_by_hash(self):
        # coinbase transaction has no input
        url = '/explorer/v1/transactions/7fb50dd5ff00d6a929ef39f51e7821ce78d141f6d45e7d93918cd5811acaa36b'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['tx']['hash'],
                         '7fb50dd5ff00d6a929ef39f51e7821ce78d141f6d45e7d93918cd5811acaa36b')
        self.assertEqual(response.json()['tx']['block_hash'],
                         '000001618d6fae9349bed836a56422bd161103ff44083bf9ff58358c8d882191')
        self.assertEqual(response.json()['tx']['type'], 'NORMAL')
        # txin
        self.assertEqual(response.json()['tx']['vins'][0]['tx_id'], None)
        # txout
        self.assertEqual(int(response.json()['tx']['vouts'][0]['color']), 0)
        self.assertEqual(int(response.json()['tx']['vouts'][0]['amount']), 0)

    def test_get_mint_tx_by_hash(self):
        # mint transaction has no input
        url = '/explorer/v1/transactions/7b641d130b2348c1262bceb0dba586f475b0ff07f2eba37e3f71bcfcf0e7e7ca'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['tx']['hash'],
                         '7b641d130b2348c1262bceb0dba586f475b0ff07f2eba37e3f71bcfcf0e7e7ca')
        self.assertEqual(response.json()['tx']['block_hash'],
                         '0000035d2e4d972e94f11316c5f1a09114a955ce6a959f297d3efcb65292bd9e')
        self.assertEqual(response.json()['tx']['type'], 'MINT')
        # txin
        self.assertEqual(response.json()['tx']['vins'][0]['tx_id'], None)
        # txout
        self.assertEqual(int(response.json()['tx']['vouts'][0]['color']), 1)
        self.assertEqual(int(response.json()['tx']['vouts'][0]['amount']), 10000000000)

    def test_get_license_tx_by_hash(self):
        # license transaction would convert 1 color 0 to color 2
        url = '/explorer/v1/transactions/5480bb28d079a4a4f7c4e2ac78393d710b689b17ff60bdc0f42464ae7ae4d4f7'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['tx']['hash'],
                         '5480bb28d079a4a4f7c4e2ac78393d710b689b17ff60bdc0f42464ae7ae4d4f7')
        self.assertEqual(response.json()['tx']['block_hash'],
                         '0000098d2547428e80638fb70668166878dbefebcffd92501d69764a32a30426')
        self.assertEqual(response.json()['tx']['type'], 'LICENSE')
        # txin
        self.assertEqual(response.json()['tx']['vins'][0]['tx_id'],
                         '9ff002170a51523cc60239fdb50426def43a61658f71cec865bbc8f468031215')
        # txout
        self.assertEqual(int(response.json()['tx']['vouts'][0]['color']), 2)
        self.assertEqual(int(response.json()['tx']['vouts'][0]['amount']), 100000000)
        self.assertEqual(int(response.json()['tx']['vouts'][1]['color']), 2)
        self.assertEqual(int(response.json()['tx']['vouts'][1]['amount']), 0)

    def test_get_vote_tx_by_hash(self):
        # vote transaction would consume 1 color 0
        url = '/explorer/v1/transactions/7d6b25544e571675429ee772c677fbc1c4984c8e25c29bb30f5892c1d5cedb6a'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['tx']['hash'],
                         '7d6b25544e571675429ee772c677fbc1c4984c8e25c29bb30f5892c1d5cedb6a')
        self.assertEqual(response.json()['tx']['block_hash'],
                         '00000efca7c5fd0154886d32f6352a67cde96e1d55ae7ddddb57315d0b6dc90b')
        self.assertEqual(response.json()['tx']['type'], 'VOTE')
        # txin, vote would use 1 color 0
        self.assertEqual(response.json()['tx']['vins'][0]['tx_id'],
                         '354c390658fd4fcf760493006d41132dd5a75f9d3b018777d1d2b78a8c2b790c')
        # txout
        self.assertEqual(int(response.json()['tx']['vouts'][0]['color']), 0)
        self.assertEqual(int(response.json()['tx']['vouts'][0]['amount']), 100000000)

    def test_get_normal_tx_by_hash(self):
        # normal send money transaction has three inputs and two outputs
        url = '/explorer/v1/transactions/64e8cd9f81e795f20c7c64951fc4540f55e8d89a70da363002dff5e21ed5b352'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['tx']['hash'],
                         '64e8cd9f81e795f20c7c64951fc4540f55e8d89a70da363002dff5e21ed5b352')
        self.assertEqual(response.json()['tx']['block_hash'],
                         '00000b44acf5951351822e5f065194285bd3df09f025ef60c019d5cbbcdaa8db')
        self.assertEqual(response.json()['tx']['type'], 'NORMAL')
        # txin, three inputs
        self.assertEqual(response.json()['tx']['vins'][0]['tx_id'],
                         'e351dcc3f5fe6bb7b9abae54886a536c35726e74f77bf473da29c970f87a8d2a')
        self.assertEqual(response.json()['tx']['vins'][1]['tx_id'],
                         '17545d685480bc7cc67a164d861a88ea5630fc01d9a35c4f72e9392948664f08')
        self.assertEqual(response.json()['tx']['vins'][2]['tx_id'],
                         '53b4322c4c9a0288e0349eb4bf8951131c4e4201d8802bb623cc84cf06c7191f')
        # txout
        self.assertEqual(int(response.json()['tx']['vouts'][0]['color']), 1)
        self.assertEqual(int(response.json()['tx']['vouts'][0]['amount']), 100000000000)
        self.assertEqual(int(response.json()['tx']['vouts'][1]['color']), 1)
        self.assertEqual(int(response.json()['tx']['vouts'][1]['amount']), 810700000000)

    def test_tx_not_found(self):
        url = '/explorer/v1/transactions/d562f957f68be51e11f7ffd1964df48dc55fdfed1357e51034990b8500000000'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'tx not exist'})


class GetColorTxsTest(TestCase):

    def test_get_color_txs_with_multiple_page(self):
        # color 0
        base_url = '/explorer/v1/transactions/color/0'

        # default page
        url = base_url
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         '7fb50dd5ff00d6a929ef39f51e7821ce78d141f6d45e7d93918cd5811acaa36b')
        self.assertEqual(response.json()['page']['ending_before'],
                         '619d1b580970afe28dc159ff9ce50e4d0d1b479b8a195c11d627db2484127288')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=619d1b580970afe28dc159ff9ce50e4d0d1b479b8a195c11d627db2484127288')

        # second page
        url = response.json()['page']['next_uri']
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         'fbd2f92fd259546753e9f07058e0657c94d9f5c5f18287aa5e691a87f7bfbe32')
        self.assertEqual(response.json()['page']['ending_before'],
                         'e31cb07ac3f3b0001d31a97e2b79dae66f9cf9c2255965aca9fd60af0bf4dcf3')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=e31cb07ac3f3b0001d31a97e2b79dae66f9cf9c2255965aca9fd60af0bf4dcf3')

        # last page
        url = base_url + '?starting_after=2175c59360de8da046d447cd95f834a354615057a31fee33c41e2c863ec97a16'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 24)
        self.assertEqual(response.json()['page']['starting_after'],
                         'd9014fbaa7f3b706913e6266547ede59b14fc55fbc1cba818c698593a0aac626')
        self.assertEqual(response.json()['page']['ending_before'],
                         'e6c46939e54cba94097ab1d2d456c59dfd38eaa1cf1b6f7b2caf021dbd5b7178')
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_color_txs_type(self):
        # color 1
        url = '/explorer/v1/transactions/color/1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 16)
        for tx in response.json()['txs']:
            # at least one output color is 1
            check = False
            for vout in tx['vouts']:
                check = check or int(vout['color']) == 1
            self.assertTrue(check)
            self.assertTrue(tx['type'] == 'NORMAL' or tx['type'] == 'MINT')

    def test_page_with_param(self):
        # color 1
        base_url = '/explorer/v1/transactions/color/1'

        # start with specific tx hash
        url = base_url + '?starting_after=3b81646bfcc14ffc284c30b428db9d411916e4378268d726aa5b0c7dd1c16057'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 12)
        self.assertEqual(response.json()['page']['starting_after'],
                         '418965ec3394220dd855e1fd4e8ed92ca0199bd3db61264ed0f540b3cf5d324a')
        self.assertEqual(response.json()['page']['ending_before'],
                         'af7368bdaee21d544e90e81589e959838c72320f0a292ee5e93a04a2600c958b')
        self.assertEqual(response.json()['page']['next_uri'], None)
        for tx in response.json()['txs']:
            # at least one output color is 1
            check = False
            for vout in tx['vouts']:
                check = check or int(vout['color']) == 1
            self.assertTrue(check)
            self.assertTrue(tx['type'] == 'NORMAL' or tx['type'] == 'MINT')

        # start with the last tx hash
        url = base_url + '?starting_after=af7368bdaee21d544e90e81589e959838c72320f0a292ee5e93a04a2600c958b'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 0)
        self.assertEqual(response.json()['page']['starting_after'], None)
        self.assertEqual(response.json()['page']['ending_before'], None)
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_color_without_tx(self):
        # color 4
        base_url = '/explorer/v1/transactions/color/4'
        response = self.client.get(base_url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 0)
        self.assertEqual(response.json()['page']['starting_after'], None)
        self.assertEqual(response.json()['page']['ending_before'], None)
        self.assertEqual(response.json()['page']['next_uri'], None)

        url = base_url + '?starting_after=3b81646bfcc14ffc284c30b428db9d411916e4378268d726aa5b0c7dd1c16057'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 0)
        self.assertEqual(response.json()['page']['starting_after'], None)
        self.assertEqual(response.json()['page']['ending_before'], None)
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_tx_not_found(self):
        url = '/explorer/v1/transactions/color/1?starting_after=abc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'tx not exist'})


class GetAddressTxsTest(TestCase):

    def test_get_address_txs_with_multiple_page(self):
        # address 1BMYKFxXgnnRaLBEka1bKFHTQYkNV4L99H
        base_url = '/explorer/v1/transactions/address/1BMYKFxXgnnRaLBEka1bKFHTQYkNV4L99H'

        # default page
        url = base_url
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         '7fb50dd5ff00d6a929ef39f51e7821ce78d141f6d45e7d93918cd5811acaa36b')
        self.assertEqual(response.json()['page']['ending_before'],
                         '9e56df7040a2898634f852129995d504a65558acf1dddab9ae37b0cdacb459fb')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=9e56df7040a2898634f852129995d504a65558acf1dddab9ae37b0cdacb459fb')

        # second page
        url = response.json()['page']['next_uri']
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         '7d6b25544e571675429ee772c677fbc1c4984c8e25c29bb30f5892c1d5cedb6a')
        self.assertEqual(response.json()['page']['ending_before'],
                         'e011780c1f2b82f3f348371efa441f5861cce9a5331bb8adf4122afb11b93a1a')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=e011780c1f2b82f3f348371efa441f5861cce9a5331bb8adf4122afb11b93a1a')

        # last page
        url = base_url + '?starting_after=e290781817430b41415077574c38e09639ef7a47808e3cade67594053fd76dd0'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 5)
        self.assertEqual(response.json()['page']['starting_after'],
                         'afb421c771fb748d6b0bc2b867996d3bd4ae32a1382e90bb3945844c03e62a65')
        self.assertEqual(response.json()['page']['ending_before'],
                         '03785d248b1423434d53a83e4f52eb1a7151fb588b2e4e3d5efcd5ebd3830823')
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_txs_address(self):
        url = '/explorer/v1/transactions/address/1Brqrjvj9UojrojRvd6diGYxEk3L4Q1b3t'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 19)
        for tx in response.json()['txs']:
            # at least one output address is 1Brqrjvj9UojrojRvd6diGYxEk3L4Q1b3t
            check = False
            for vout in tx['vouts']:
                check = check or vout['address'] == '1Brqrjvj9UojrojRvd6diGYxEk3L4Q1b3t'
            self.assertTrue(check)

    def test_page_with_starting_tx(self):
        # address 1Brqrjvj9UojrojRvd6diGYxEk3L4Q1b3t
        base_url = '/explorer/v1/transactions/address/1Brqrjvj9UojrojRvd6diGYxEk3L4Q1b3t'

        # start with specific tx hash
        url = base_url + '?starting_after=250a21994745296c1733285fc16fde06845fb451911d0a88228569e0566e3b72'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 16)
        self.assertEqual(response.json()['page']['starting_after'],
                         'b73a6937a0e38e153899847fc4f9cf8c3243e572e7558ccf9fbc3e5f9719c5f7')
        self.assertEqual(response.json()['page']['ending_before'],
                         '7d6b25544e571675429ee772c677fbc1c4984c8e25c29bb30f5892c1d5cedb6a')
        self.assertEqual(response.json()['page']['next_uri'], None)
        for tx in response.json()['txs']:
            # at least one output address is 1Brqrjvj9UojrojRvd6diGYxEk3L4Q1b3t
            check = False
            for vout in tx['vouts']:
                check = check or vout['address'] == '1Brqrjvj9UojrojRvd6diGYxEk3L4Q1b3t'
            self.assertTrue(check)

        # start with the last tx hash
        url = base_url + '?starting_after=7d6b25544e571675429ee772c677fbc1c4984c8e25c29bb30f5892c1d5cedb6a'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 0)
        self.assertEqual(response.json()['page']['starting_after'], None)
        self.assertEqual(response.json()['page']['ending_before'], None)
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_txs_address_with_type(self):
        # tx type NORMAL
        url = '/explorer/v1/transactions/address/1Brqrjvj9UojrojRvd6diGYxEk3L4Q1b3t?tx_type=0'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 16)
        for tx in response.json()['txs']:
            self.assertEqual(tx['type'], 'NORMAL')

        # tx type MINT
        url = '/explorer/v1/transactions/address/1FPWFMPvYNTBx3fJYVmbFyhKtfi4QPQ6MY?tx_type=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 7)
        for tx in response.json()['txs']:
            self.assertEqual(tx['type'], 'MINT')

        # tx type LICENSE
        url = '/explorer/v1/transactions/address/1FPWFMPvYNTBx3fJYVmbFyhKtfi4QPQ6MY?tx_type=2'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 2)
        for tx in response.json()['txs']:
            self.assertEqual(tx['type'], 'LICENSE')

        # tx type VOTE
        url = '/explorer/v1/transactions/address/1Brqrjvj9UojrojRvd6diGYxEk3L4Q1b3t?tx_type=3'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 1)
        for tx in response.json()['txs']:
            self.assertEqual(tx['type'], 'VOTE')

    def test_page_with_type(self):
        base_url = '/explorer/v1/transactions/address/1BMYKFxXgnnRaLBEka1bKFHTQYkNV4L99H'

        # first page
        url = base_url + '?tx_type=0'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         '7fb50dd5ff00d6a929ef39f51e7821ce78d141f6d45e7d93918cd5811acaa36b')
        self.assertEqual(response.json()['page']['ending_before'],
                         '0f20cf47d979684d3eb585c2f35ed16ccce4ee43f5ea86b1dca7351069348252')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=0f20cf47d979684d3eb585c2f35ed16ccce4ee43f5ea86b1dca7351069348252&tx_type=0')

        # second page
        url = response.json()['page']['next_uri']
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         'e77be251c7f1ffd03480a68fe6dce1a083a9439bef6dd12889e2a6a11b06ff5c')
        self.assertEqual(response.json()['page']['ending_before'],
                         'ee6853ca7fc3ef76f401897c5c17ffce2e29442fd48667b38ec2b704e9130798')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=ee6853ca7fc3ef76f401897c5c17ffce2e29442fd48667b38ec2b704e9130798&tx_type=0')

        # last page
        url = base_url + '?starting_after=221073f43f0cd54681d646a093bd43f6cfe50a05112c38a557a4fa9c60cb7887&tx_type=0'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 49)
        self.assertEqual(response.json()['page']['starting_after'],
                         '646e65ed17e35ce732b5c8f3716abaed68885288b4d7d94de3abace83f72d195')
        self.assertEqual(response.json()['page']['ending_before'],
                         '03785d248b1423434d53a83e4f52eb1a7151fb588b2e4e3d5efcd5ebd3830823')
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_txs_address_with_since_until(self):
        base_url = '/explorer/v1/transactions/address/1BMYKFxXgnnRaLBEka1bKFHTQYkNV4L99H'

        # since: 04 Aug 2016 15:55:58 GMT
        url = base_url + '?since=1470326158'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         '7fb50dd5ff00d6a929ef39f51e7821ce78d141f6d45e7d93918cd5811acaa36b')
        self.assertEqual(response.json()['page']['ending_before'],
                         '9e56df7040a2898634f852129995d504a65558acf1dddab9ae37b0cdacb459fb')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=9e56df7040a2898634f852129995d504a65558acf1dddab9ae37b0cdacb459fb&since=1470326158')
        for tx in response.json()['txs']:
            self.assertGreaterEqual(int(tx['time']), 1470326158)

        # until: 10 Aug 2016 08:01:59 GMT
        url = base_url + '?until=1470816119'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['page']['starting_after'],
                         'ca6d14f6174df15bf9d96768c46019ba7dfcccbe6bab5be02d0c3309c319e89b')
        self.assertEqual(response.json()['page']['ending_before'],
                         '6b962002a4f2e3724fab4e8757d97e6ed6405c5e5fb2551806a77c10cd728856')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=6b962002a4f2e3724fab4e8757d97e6ed6405c5e5fb2551806a77c10cd728856&until=1470816119')
        for tx in response.json()['txs']:
            self.assertLessEqual(int(tx['time']), 1470816119)

        # both
        url = base_url + '?since=1470326158&until=1470816119'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         'ca6d14f6174df15bf9d96768c46019ba7dfcccbe6bab5be02d0c3309c319e89b')
        self.assertEqual(response.json()['page']['ending_before'],
                         '6b962002a4f2e3724fab4e8757d97e6ed6405c5e5fb2551806a77c10cd728856')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=6b962002a4f2e3724fab4e8757d97e6ed6405c5e5fb2551806a77c10cd728856&since=1470326158&until=1470816119')
        for tx in response.json()['txs']:
            self.assertGreaterEqual(int(tx['time']), 1470326158)
            self.assertLessEqual(int(tx['time']), 1470816119)

    def test_page_with_since(self):
        base_url = '/explorer/v1/transactions/address/1BMYKFxXgnnRaLBEka1bKFHTQYkNV4L99H'

        # first page, since: 04 Aug 2016 15:55:58 GMT
        url = base_url + '?since=1470326158'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         '7fb50dd5ff00d6a929ef39f51e7821ce78d141f6d45e7d93918cd5811acaa36b')
        self.assertEqual(response.json()['page']['ending_before'],
                         '9e56df7040a2898634f852129995d504a65558acf1dddab9ae37b0cdacb459fb')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=9e56df7040a2898634f852129995d504a65558acf1dddab9ae37b0cdacb459fb&since=1470326158')

        # second page
        url = response.json()['page']['next_uri']
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 31)
        self.assertEqual(response.json()['page']['starting_after'],
                         '7d6b25544e571675429ee772c677fbc1c4984c8e25c29bb30f5892c1d5cedb6a')
        self.assertEqual(response.json()['page']['ending_before'],
                         'e7a432db63d1ae15fbd4db62df304b023f837945ca1ea02e1babe5dfb9ca6f6f')
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_txs_address_with_all_params(self):
        base_url = '/explorer/v1/transactions/address/1BMYKFxXgnnRaLBEka1bKFHTQYkNV4L99H'
        url = base_url + '?since=1470242210&until=1470816119&tx_type=1&page_size=20&starting_after=354c390658fd4fcf760493006d41132dd5a75f9d3b018777d1d2b78a8c2b790c'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 3)
        self.assertEqual(response.json()['page']['starting_after'],
                         '428e928f033cc9e4801eefb4ccc41a331fc10445264916a9d6f6897ad9f761f9')
        self.assertEqual(response.json()['page']['ending_before'],
                         '9ff002170a51523cc60239fdb50426def43a61658f71cec865bbc8f468031215')
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_address_without_tx(self):
        # address 1Brqrjvj9UojrojRvd6diGYxEk3Laaaaaa
        base_url = '/explorer/v1/transactions/address/1Brqrjvj9UojrojRvd6diGYxEk3Laaaaaa'
        response = self.client.get(base_url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 0)
        self.assertEqual(response.json()['page']['starting_after'], None)
        self.assertEqual(response.json()['page']['ending_before'], None)
        self.assertEqual(response.json()['page']['next_uri'], None)

        url = base_url + '?starting_after=3b81646bfcc14ffc284c30b428db9d411916e4378268d726aa5b0c7dd1c16057'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 0)
        self.assertEqual(response.json()['page']['starting_after'], None)
        self.assertEqual(response.json()['page']['ending_before'], None)
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_tx_not_found(self):
        url = '/explorer/v1/transactions/address/1Brqrjvj9UojrojRvd6diGYxEk3Laaaaaa?starting_after=abc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'tx not exist'})


class TxPaginationTest(TestCase):

    def test_address_txs(self):
        base_url = '/explorer/v1/transactions/address/1BMYKFxXgnnRaLBEka1bKFHTQYkNV4L99H'
        url = base_url + '?page_size=20'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 20)
        self.assertEqual(response.json()['page']['starting_after'],
                         '7fb50dd5ff00d6a929ef39f51e7821ce78d141f6d45e7d93918cd5811acaa36b')
        self.assertEqual(response.json()['page']['ending_before'],
                         '9dcde5d7c98216d45ff18d656cfe8d7e1057f79b038ce49cfab616d6a0b7fc14')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=9dcde5d7c98216d45ff18d656cfe8d7e1057f79b038ce49cfab616d6a0b7fc14&page_size=20')

    def test_color_txs(self):
        base_url = '/explorer/v1/transactions/color/0'
        url = base_url + '?page_size=20'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 20)
        self.assertEqual(response.json()['page']['starting_after'],
                         '7fb50dd5ff00d6a929ef39f51e7821ce78d141f6d45e7d93918cd5811acaa36b')
        self.assertEqual(response.json()['page']['ending_before'],
                         '9dcde5d7c98216d45ff18d656cfe8d7e1057f79b038ce49cfab616d6a0b7fc14')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=9dcde5d7c98216d45ff18d656cfe8d7e1057f79b038ce49cfab616d6a0b7fc14&page_size=20')


class GetAddressUtxoTest(TestCase):

    def test_get_address_utxo(self):
        url = '/explorer/v1/addresses/1FPWFMPvYNTBx3fJYVmbFyhKtfi4QPQ6MY/utxos'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['utxo']), 12)

    def test_address_no_ntux(self):
        url = '/explorer/v1/addresses/1FPWFMPvYNTBx3fJYVmbFyhKtfi4aaaaaa/utxos'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['utxo']), 0)


class GetAddressBalanceTest(TestCase):

    def test_get_address_balance(self):
        url = '/explorer/v1/addresses/1FPWFMPvYNTBx3fJYVmbFyhKtfi4QPQ6MY/balances'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(int(response.json().get('1')), 3820400000000)
        self.assertEqual(int(response.json().get('2')), 482100000000)

    def test_address_no_balance(self):
        url = '/explorer/v1/addresses/1FPWFMPvYNTBx3fJYVmbFyhKtfi4aaaaaa/balances'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json(), {})
