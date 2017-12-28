import httplib
import json
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
        base_url = '/explorer/v1/blocks'
        response = self.client.get(base_url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['blocks']), 50)
        # get the latest 50 blocks
        block = response.json()['blocks'][0]
        self.assertEqual(block['hash'], '00000f6326e6b87fb5197acfcdf1b99a7e04650ad9db5c2a7759025330a5f068')
        self.assertEqual(block['branch'], 'main')
        for i in range(1, 50):
            next_block = response.json()['blocks'][i]
            self.assertEqual(next_block['branch'], 'main')
            self.assertLessEqual(int(next_block['time']), int(block['time']))
            block = next_block

        self.assertEqual(response.json()['page']['starting_after'],
                         '00000f6326e6b87fb5197acfcdf1b99a7e04650ad9db5c2a7759025330a5f068')
        self.assertEqual(response.json()['page']['ending_before'],
                         '0000018d13f3a211f38d21affb67ee9ec678b0b459d169bb70c4ba0fd7c3954f')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=0000018d13f3a211f38d21affb67ee9ec678b0b459d169bb70c4ba0fd7c3954f')

        # next page
        url = base_url + '?starting_after=0000018d13f3a211f38d21affb67ee9ec678b0b459d169bb70c4ba0fd7c3954f'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['blocks']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         '000006406fbe15a525de54db02f68a810cddb8acf24ff142c63b4e3f90c771f6')
        self.assertEqual(response.json()['page']['ending_before'],
                         '00000d56c42128faa037cf72f8818dae68166975cecfff4314f339e294a0ea6a')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=00000d56c42128faa037cf72f8818dae68166975cecfff4314f339e294a0ea6a')

    def test_get_blocks_with_since_until(self):
        base_url = '/explorer/v1/blocks'
        response = self.client.get(base_url + '?since=1511409670&until=1511417980')
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['blocks']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         '00000f6326e6b87fb5197acfcdf1b99a7e04650ad9db5c2a7759025330a5f068')
        self.assertEqual(response.json()['page']['ending_before'],
                         '0000018d13f3a211f38d21affb67ee9ec678b0b459d169bb70c4ba0fd7c3954f')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=0000018d13f3a211f38d21affb67ee9ec678b0b459d169bb70c4ba0fd7c3954f&since=1511409670&until=1511417980')


class GetBlockByHashTest(TestCase):

    def test_get_block_by_hash(self):
        url = '/explorer/v1/blocks/00000d56c42128faa037cf72f8818dae68166975cecfff4314f339e294a0ea6a'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['block']['hash'],
                         '00000d56c42128faa037cf72f8818dae68166975cecfff4314f339e294a0ea6a')
        self.assertEqual(response.json()['block']['branch'], 'main')

    def test_block_not_found(self):
        url = '/explorer/v1/blocks/000001618d6fae9349bed836a56422bd161103ff44083bf9ff58358c8d000000'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'block not exist'})


class GetBlockByHeightTest(TestCase):

    def test_get_block_by_height(self):
        url = '/explorer/v1/blocks/96'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['block']['hash'],
                         '0000018d13f3a211f38d21affb67ee9ec678b0b459d169bb70c4ba0fd7c3954f')
        self.assertEqual(response.json()['block']['branch'], 'main')

    def test_block_not_found(self):
        # the block height in the test blk00000.dat is only 145
        url = '/explorer/v1/blocks/146'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'block not exist'})


class GetTxByHashTest(TestCase):

    def test_coinbase_tx_by_hash(self):
        # coinbase transaction has no input
        url = '/explorer/v1/transactions/4a4314b399b56cc3562f00d036d29d7eb850eb48f8b352d834f1e3d7a4ad0c96'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['tx']['hash'],
                         '4a4314b399b56cc3562f00d036d29d7eb850eb48f8b352d834f1e3d7a4ad0c96')
        self.assertEqual(response.json()['tx']['blockhash'],
                         '000001177de14a9db230f84034dcc6bca3bb5b21cf7dde935209c9b92bed3946')
        # txin
        self.assertEqual(response.json()['tx']['vins'][0]['tx_hash'], None)
        # txout
        self.assertEqual(int(response.json()['tx']['vouts'][0]['amount']), 5000012240)

    def test_get_normal_tx_by_hash(self):
        # normal send money transaction has one inputs and two outputs
        url = '/explorer/v1/transactions/5b1cb755bc3d4d85e5b70e77724e67f0831b5913ed56061672f6482ac791c503'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['tx']['hash'],
                         '5b1cb755bc3d4d85e5b70e77724e67f0831b5913ed56061672f6482ac791c503')
        self.assertEqual(response.json()['tx']['blockhash'],
                         '000001177de14a9db230f84034dcc6bca3bb5b21cf7dde935209c9b92bed3946')
        # txin
        self.assertEqual(response.json()['tx']['vins'][0]['tx_hash'],
                         '95154e178256b2ac222666bce7556f9e22b0efa165b7792e2e01b93d8c2b4f86')
        # txout
        self.assertEqual(int(response.json()['tx']['vouts'][0]['amount']), 3000000000)
        self.assertEqual(int(response.json()['tx']['vouts'][1]['amount']), 1999996160)

    def test_tx_not_found(self):
        url = '/explorer/v1/transactions/d562f957f68be51e11f7ffd1964df48dc55fdfed1357e51034990b8500000000'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'tx not exist'})


class GetAddressTxsTest(TestCase):

    def test_get_address_txs_with_multiple_page(self):
        # address 1MwwRgJQPnBzdrJXw4HBgB1uS37iC5NFHt
        base_url = '/explorer/v1/transactions/address/1MwwRgJQPnBzdrJXw4HBgB1uS37iC5NFHt'

        # default page
        url = base_url
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         '601848ca618407de701bafce16a699e64177caa52769bdf90f404a3da7a9e3f3')
        self.assertEqual(response.json()['page']['ending_before'],
                         '969740d72bf61fe9fb27cc96c7c1ca6a5c73e083e1176d910c0a42273048d8dc')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=969740d72bf61fe9fb27cc96c7c1ca6a5c73e083e1176d910c0a42273048d8dc')

        # second page
        url = response.json()['page']['next_uri']
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         '373f193fe975741524202fce89df06b2922fcdd0d6c38fcb6dc59ac1050fc917')
        self.assertEqual(response.json()['page']['ending_before'],
                         '926e032d113716cbd529d93c4a56aeb4e1a7f155168b5dfb83883bee895247d4')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=926e032d113716cbd529d93c4a56aeb4e1a7f155168b5dfb83883bee895247d4')

        # last page
        url = base_url + '?starting_after=926e032d113716cbd529d93c4a56aeb4e1a7f155168b5dfb83883bee895247d4'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 4)
        self.assertEqual(response.json()['page']['starting_after'],
                         '5682c517e323974048508c94db2feecac90db030a9539acf1075482ac3bf9171')
        self.assertEqual(response.json()['page']['ending_before'],
                         '2e1e00ab63b1838ac1b56f7faea0ef17030a1cba6cb05f163957a242b7fbf019')
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_txs_address(self):
        url = '/explorer/v1/transactions/address/1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 11)
        for tx in response.json()['txs']:
            # at least one output address is 1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK
            check = False
            for vout in tx['vouts']:
                check = check or vout['address'] == '1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK'
            self.assertTrue(check)

    def test_page_with_starting_tx(self):
        # address 1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK
        base_url = '/explorer/v1/transactions/address/1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK'

        # start with specific tx hash
        url = base_url + '?starting_after=588484fd1177fb66a831e2fb5dad36744e262787646e2b30af345946bb2f5801'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 8)
        self.assertEqual(response.json()['page']['starting_after'],
                         'a71d351d73119e9120a5834bdf5e48f97cc5e2c538dc70a86380cc7e2e51f7d6')
        self.assertEqual(response.json()['page']['ending_before'],
                         '5b1cb755bc3d4d85e5b70e77724e67f0831b5913ed56061672f6482ac791c503')
        self.assertEqual(response.json()['page']['next_uri'], None)
        for tx in response.json()['txs']:
            # at least one output address is 1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK
            check = False
            for vout in tx['vouts']:
                check = check or vout['address'] == '1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK'
            self.assertTrue(check)

        # start with the last tx hash
        url = base_url + '?starting_after=5b1cb755bc3d4d85e5b70e77724e67f0831b5913ed56061672f6482ac791c503'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 0)
        self.assertEqual(response.json()['page']['starting_after'], None)
        self.assertEqual(response.json()['page']['ending_before'], None)
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_txs_address_with_since_until(self):
        base_url = '/explorer/v1/transactions/address/1MwwRgJQPnBzdrJXw4HBgB1uS37iC5NFHt'

        # since: 23-Nov-17 03:52:05
        url = base_url + '?since=1511409125'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         '601848ca618407de701bafce16a699e64177caa52769bdf90f404a3da7a9e3f3')
        self.assertEqual(response.json()['page']['ending_before'],
                         '969740d72bf61fe9fb27cc96c7c1ca6a5c73e083e1176d910c0a42273048d8dc')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=969740d72bf61fe9fb27cc96c7c1ca6a5c73e083e1176d910c0a42273048d8dc&since=1511409125')
        for tx in response.json()['txs']:
            self.assertGreaterEqual(int(tx['time']), 1511409125)

        # until: 23-Nov-17 03:53:22 UTC
        url = base_url + '?until=1511409202'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['page']['starting_after'],
                         'a0fca44ab50fa1583469d966de9ea81a7163d42bfc57949716311c1634cb9f07')
        self.assertEqual(response.json()['page']['ending_before'],
                         '2e1e00ab63b1838ac1b56f7faea0ef17030a1cba6cb05f163957a242b7fbf019')
        self.assertEqual(response.json()['page']['next_uri'], None)
        for tx in response.json()['txs']:
            self.assertLessEqual(int(tx['time']), 1511409202)

        # both
        url = base_url + '?since=1511409125&until=1511409202'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 14)
        self.assertEqual(response.json()['page']['starting_after'],
                         'a0fca44ab50fa1583469d966de9ea81a7163d42bfc57949716311c1634cb9f07')
        self.assertEqual(response.json()['page']['ending_before'],
                         '895c4a509728eee7cc39fcf71cc93cc2543405cb20a14c54586b4019a764354d')
        self.assertEqual(response.json()['page']['next_uri'], None)
        for tx in response.json()['txs']:
            self.assertGreaterEqual(int(tx['time']), 1511409125)
            self.assertLessEqual(int(tx['time']), 1511409202)

    def test_page_with_since(self):
        base_url = '/explorer/v1/transactions/address/1MwwRgJQPnBzdrJXw4HBgB1uS37iC5NFHt'

        # first page, since: 23-Nov-17 03:52:05
        url = base_url + '?since=1511409125'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         '601848ca618407de701bafce16a699e64177caa52769bdf90f404a3da7a9e3f3')
        self.assertEqual(response.json()['page']['ending_before'],
                         '969740d72bf61fe9fb27cc96c7c1ca6a5c73e083e1176d910c0a42273048d8dc')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=969740d72bf61fe9fb27cc96c7c1ca6a5c73e083e1176d910c0a42273048d8dc&since=1511409125')

        # second page
        url = response.json()['page']['next_uri']
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'],
                         '373f193fe975741524202fce89df06b2922fcdd0d6c38fcb6dc59ac1050fc917')
        self.assertEqual(response.json()['page']['ending_before'],
                         '926e032d113716cbd529d93c4a56aeb4e1a7f155168b5dfb83883bee895247d4')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=926e032d113716cbd529d93c4a56aeb4e1a7f155168b5dfb83883bee895247d4&since=1511409125')

    def test_txs_address_with_all_params(self):
        base_url = '/explorer/v1/transactions/address/1MwwRgJQPnBzdrJXw4HBgB1uS37iC5NFHt'
        url = base_url + '?since=1511409125&until=1511409202&page_size=10&starting_after=a0fca44ab50fa1583469d966de9ea81a7163d42bfc57949716311c1634cb9f07'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 10)
        self.assertEqual(response.json()['page']['starting_after'],
                         'dbd926ad7be59feab0442dc51ad271f019dd751d06caa285ccfdb5521f836053')
        self.assertEqual(response.json()['page']['ending_before'],
                         '926e032d113716cbd529d93c4a56aeb4e1a7f155168b5dfb83883bee895247d4')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=926e032d113716cbd529d93c4a56aeb4e1a7f155168b5dfb83883bee895247d4&since=1511409125&until=1511409202&page_size=10')

        # second page
        url = response.json()['page']['next_uri']
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 3)
        self.assertEqual(response.json()['page']['starting_after'],
                         '5682c517e323974048508c94db2feecac90db030a9539acf1075482ac3bf9171')
        self.assertEqual(response.json()['page']['ending_before'],
                         '895c4a509728eee7cc39fcf71cc93cc2543405cb20a14c54586b4019a764354d')
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_address_without_tx(self):
        # address 1KeauFs1g7v7R2BCKBJWM4GacAjNaaaaaa
        base_url = '/explorer/v1/transactions/address/1KeauFs1g7v7R2BCKBJWM4GacAjNaaaaaa'
        response = self.client.get(base_url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 0)
        self.assertEqual(response.json()['page']['starting_after'], None)
        self.assertEqual(response.json()['page']['ending_before'], None)
        self.assertEqual(response.json()['page']['next_uri'], None)

        url = base_url + '?starting_after=926e032d113716cbd529d93c4a56aeb4e1a7f155168b5dfb83883bee895247d4'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 0)
        self.assertEqual(response.json()['page']['starting_after'], None)
        self.assertEqual(response.json()['page']['ending_before'], None)
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_tx_not_found(self):
        url = '/explorer/v1/transactions/address/1Brqrjvj9UojrojRvd6diGYxEk3Laaaaaa?starting_after=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'tx not exist'})


class TxPaginationTest(TestCase):

    def test_address_txs(self):
        base_url = '/explorer/v1/transactions/address/1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK'
        url = base_url + '?page_size=10'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 10)
        self.assertEqual(response.json()['page']['starting_after'],
                         '601848ca618407de701bafce16a699e64177caa52769bdf90f404a3da7a9e3f3')
        self.assertEqual(response.json()['page']['ending_before'],
                         '2770dfea902387608ef3f967d0df9ac6dbf84a25fe9d96b934debbd6fb83f61f')
        self.assertEqual(response.json()['page']['next_uri'],
                         base_url + '?starting_after=2770dfea902387608ef3f967d0df9ac6dbf84a25fe9d96b934debbd6fb83f61f&page_size=10')


class GetAddressUtxoTest(TestCase):

    def test_get_address_utxo(self):
        url = '/explorer/v1/addresses/1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK/utxos'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['utxo']), 11)

    def test_address_no_ntux(self):
        url = '/explorer/v1/addresses/1KeauFs1g7v7R2BCKBJWM4GacAaaaaaaaa/utxos'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['utxo']), 0)


class GetAddressBalanceTest(TestCase):

    def test_get_address_balance(self):
        url = '/explorer/v1/addresses/1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK/balances'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(int(response.json().get('balance')), 77100000000)

    def test_address_no_balance(self):
        url = '/explorer/v1/addresses/1FPWFMPvYNTBx3fJYVmbFyhKtfi4aaaaaa/balances'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json().get('balance'), 0)


class CreateRawTxTest(TestCase):

    def setUp(self):
        self.url = '/explorer/v1/transaction/prepare'
        self.from_address = '1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK'
        self.to_address = '1MnwbemNqG4d41iGy6CeQGCPgigzLX3vyL'

    def test_create_raw_tx_using(self):
        response = self.client.get(self.url, {'from_address': self.from_address,
                                              'to_address': self.to_address,
                                              'amount': 770})
        self.assertEqual(response.status_code, httplib.OK)
        self.assertIn('raw_tx', response.json())

    # Test insufficient fund
    def test_create_raw_tx_without_sufficient_fee(self):
        response = self.client.get(self.url, {'from_address': self.from_address,
                                              'to_address': self.to_address,
                                              'amount': 772})
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
        self.assertEqual(response.json(), {'error': 'insufficient funds in address {}'.format(self.from_address)})

    def test_create_raw_tx_with_amount_exceed_8_decimal_digit(self):
        response = self.client.get(self.url, {'from_address': self.from_address,
                                              'to_address': self.to_address,
                                              'amount': 0.123456789})
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
        self.assertEqual(response.json(), {'error': '`amount` only allow up to 8 decimal digits'})

    def test_missing_form_data(self):
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)


class GeneralTxTest(TestCase):

    def setUp(self):
        self.url = '/explorer/v1/general-transaction/prepare'
        self.from_address = '1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK'
        self.to_address = '1MnwbemNqG4d41iGy6CeQGCPgigzLX3vyL'

    def test_general_tx_using(self):
        tx_in = [{
            'from_address': self.from_address,
            'amount':'770',
            'fee': '1',
        }]
        tx_out = [{
            'to_address': self.to_address,
            'amount': '770',
        }]
        data = {
            'tx_in': tx_in,
            'tx_out': tx_out,
            'op_return_data': 'abcde',
        }
        response = self.client.post(self.url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, httplib.OK)
        self.assertIn('raw_tx', response.json())

    # Test insufficient fund
    def test_general_tx_without_sufficient_fund(self):
        tx_in = [{
            'from_address': self.from_address,
            'amount': '771',
            'fee': '1',
            }]
        tx_out = [{
            'to_address': self.to_address,
            'amount': '771',
        }]
        data = {
            'tx_in': tx_in,
            'tx_out': tx_out,
        }
        response = self.client.post(self.url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
        self.assertEqual(response.json(), {'error': 'insufficient funds in address {}'.format(self.from_address)})

    def test_general_tx_with_amount_exceed_8_decimal_digit(self):
        tx_in = [{
            'from_address': self.from_address,
            'amount': '0.123456789',
            'fee': '1',
            }]
        tx_out = [{
            'to_address': self.to_address,
            'amount': '0.123456789',
        }]
        data = {
            'tx_in': tx_in,
            'tx_out': tx_out,
        }
        response = self.client.post(self.url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
        self.assertEqual(response.json(), {'error': '`amount` only allow up to 8 decimal digits'})

    def test_missing_form_data(self):
        response = self.client.post(self.url, json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
