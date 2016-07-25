import httplib
import random

from django.test import TestCase

from ..models import *


class TestSetUp(object):
    def __init__(self):
        self.address1, created = Address.objects.get_or_create(address='126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB')
        self.address2, created = Address.objects.get_or_create(address='13JGvpZTEm8iUvpjavj3k9SmnwdrhFfcBx')

    def create_block(self, hash, time, height, prev_block, tx_count, in_longest):
        if prev_block:
            return Block.objects.create(hash=hash, time=time, height=prev_block.height + 1, prev_block=prev_block,
                                        tx_count=tx_count, in_longest=in_longest)
        else:
            return Block.objects.create(hash=hash, time=time, height=height, tx_count=tx_count, in_longest=in_longest)

    def create_coinbase_tx(self, hash, block, time=0):
        tx = Tx.objects.create(hash=hash, block=block, version=1, type=0, time=time)
        TxIn.objects.create(tx=tx, position=0)
        TxOut.objects.create(tx=tx, value=0, position=0, scriptpubkey=binascii.unhexlify('aaaa'), address=self.address1,
                             spent=0, color=0)
        return tx

    def create_mint_tx(self, hash, block, color, time=0):
        tx = Tx.objects.create(hash=hash, block=block, version=1, type=1, time=time)
        TxIn.objects.create(tx=tx, position=0)
        TxOut.objects.create(tx=tx, value=100, position=0, scriptpubkey=binascii.unhexlify('aaaa'),
                             address=self.address1, spent=0, color=color)
        return tx

    def create_normal_tx(self, hash, block, txout, color, time=0):
        tx = Tx.objects.create(hash=hash, block=block, version=1, type=0, time=time)
        TxIn.objects.create(tx=tx, txout=txout, position=0)
        TxOut.objects.create(tx=tx, value=10, position=1, scriptpubkey=binascii.unhexlify('aaaa'),
                             address=self.address2, spent=0, color=color)
        TxOut.objects.create(tx=tx, value=90, position=0, scriptpubkey=binascii.unhexlify('bbbb'),
                             address=self.address1, spent=0, color=color)
        txout.spent = 1
        txout.save()
        return tx

    def create_other_type_tx(self, hash, block, type, color, time=0):
        tx = Tx.objects.create(hash=hash, block=block, version=1, type=type, time=time)
        TxIn.objects.create(tx=tx, position=0)
        TxOut.objects.create(tx=tx, value=0, position=0, scriptpubkey=binascii.unhexlify('aaaa'),
                             address=self.address1, spent=0, color=color)


class GetLatestBlocksTest(TestCase):
    def setUp(self):
        test_sample = TestSetUp()
        block = test_sample.create_block(str(0), 0, 1, None, 1, 1)
        # choose three random block to fork
        random_number_list = random.sample(range(1, 55), 3)
        for i in range(1, 55):
            if i in random_number_list:
                test_sample.create_block(str(i), i, i + 1, block, 1, 0)
            else:
                block = test_sample.create_block(str(i), i, i + 1, block, 1, 1)

    def tearDown(self):
        Address.objects.all().delete()
        Block.objects.all().delete()

    def test_get_latest_blocks(self):
        url = '/explorer/v1/blocks'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['blocks']), 50)
        # get the latest block
        block = response.json()['blocks'][0]
        self.assertEqual(block['hash'], Block.objects.filter(in_longest=1)[0].hash)
        for i in range(1, 50):
            next_block = response.json()['blocks'][i]
            self.assertEqual(next_block['branch'], 'main')
            self.assertLessEqual(int(next_block['time']), int(block['time']))
            block = next_block


class GetBlockByHashTest(TestCase):
    def setUp(self):
        test_sample = TestSetUp()
        test_sample.create_block('000004e0223a146664188edebf7efbce82c3a421ce70f30b71c156368c21caaf', 0, 1, None, 1, 1)

    def tearDown(self):
        Address.objects.all().delete()
        Block.objects.all().delete()

    def test_get_block_by_hash(self):
        url = '/explorer/v1/blocks/000004e0223a146664188edebf7efbce82c3a421ce70f30b71c156368c21caaf'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['block']['hash'],
                         '000004e0223a146664188edebf7efbce82c3a421ce70f30b71c156368c21caaf')

    def test_block_not_found(self):
        url = '/explorer/v1/blocks/000004e0223a146664188edebf7efbce82c3a421ce70f30b71c156368c21caaa'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'block not exist'})


class GetBlockByHeightTest(TestCase):
    def setUp(self):
        test_sample = TestSetUp()
        # block in main chain
        test_sample.create_block('000004e0223a146664188edebf7efbce82c3a421ce70f30b71c156368c21caaf', 0, 1, None, 1, 1)
        # block in fork chain
        test_sample.create_block('00000319eb1fbe75c75e6ad3970855ac67f8687febd230b3c26c074474889d3b', 1, 2, None, 1, 0)

    def tearDown(self):
        Address.objects.all().delete()
        Block.objects.all().delete()

    def test_get_block_by_height(self):
        url = '/explorer/v1/blocks/1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(int(response.json()['block']['height']), 1)
        self.assertEqual(response.json()['block']['hash'],
                         '000004e0223a146664188edebf7efbce82c3a421ce70f30b71c156368c21caaf')
        self.assertEqual(response.json()['block']['branch'], 'main')

    def test_block_not_found(self):
        url = '/explorer/v1/blocks/2'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'block not exist'})


class GetTxByHashTest(TestCase):
    def setUp(self):
        """
        block1:
            tx1:
                type: coinbase tx
                addr: address1
        block2:
            tx2:
                type: coinbase tx
                addr: address1
            tx3:
                type: mint tx
                addr: address1
            tx4:
                type: normal tx from address1 to address2
                addr: address1, address2
        """
        test_sample = TestSetUp()
        self.address1 = test_sample.address1
        self.address2 = test_sample.address2
        self.block1 = test_sample.create_block('000004e0223a146664188edebf7efbce82c3a421ce70f30b71c156368c21caaf', 0, 1,
                                               None, 1, 1)
        self.block2 = test_sample.create_block('00000319eb1fbe75c75e6ad3970855ac67f8687febd230b3c26c074474889d3b', 1, 2,
                                               self.block1, 1, 1)
        self.tx1 = test_sample.create_coinbase_tx('7e336fb514f829b57b5147f1d81abb35f7f08ebd97ef8e8063f2cfdf3ed2ca07',
                                                  self.block1)
        self.tx2 = test_sample.create_coinbase_tx('c0daefcf66be12f4e3f426c8b08babf437d7945e70bacee492df2c4a04b801e1',
                                                  self.block2)
        self.tx3 = test_sample.create_mint_tx('d562f957f68be51e11f7ffd1964df48dc55fdfed1357e51034990b8504fddccb',
                                              self.block2, 1)
        self.tx4 = test_sample.create_normal_tx('2e75d6117852fb0f3a42951a683cf9ab52f2b7d7578f5ac0487c2256aa301769',
                                                self.block2, self.tx3.tx_outs.all()[0], 1)

    def tearDown(self):
        Address.objects.all().delete()
        Block.objects.all().delete()

    def test_get_tx_by_hash(self):
        # coinbase tx
        url = '/explorer/v1/transactions/7e336fb514f829b57b5147f1d81abb35f7f08ebd97ef8e8063f2cfdf3ed2ca07'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['tx']['hash'],
                         '7e336fb514f829b57b5147f1d81abb35f7f08ebd97ef8e8063f2cfdf3ed2ca07')
        self.assertEqual(response.json()['tx']['block_hash'], self.block1.hash)
        self.assertEqual(response.json()['tx']['vins'][0]['tx_id'], None)
        self.assertEqual(response.json()['tx']['type'], 'NORMAL')

        # mint tx
        url = '/explorer/v1/transactions/d562f957f68be51e11f7ffd1964df48dc55fdfed1357e51034990b8504fddccb'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['tx']['hash'],
                         'd562f957f68be51e11f7ffd1964df48dc55fdfed1357e51034990b8504fddccb')
        self.assertEqual(response.json()['tx']['block_hash'], self.block2.hash)
        self.assertEqual(response.json()['tx']['vins'][0]['tx_id'], None)
        self.assertEqual(response.json()['tx']['type'], 'MINT')

        # normal tx
        url = '/explorer/v1/transactions/2e75d6117852fb0f3a42951a683cf9ab52f2b7d7578f5ac0487c2256aa301769'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['tx']['hash'],
                         '2e75d6117852fb0f3a42951a683cf9ab52f2b7d7578f5ac0487c2256aa301769')
        self.assertEqual(response.json()['tx']['block_hash'], self.block2.hash)
        self.assertEqual(len(response.json()['tx']['vouts']), 2)

    def test_tx_not_found(self):
        url = '/explorer/v1/transactions/d562f957f68be51e11f7ffd1964df48dc55fdfed1357e51034990b8504fddc00'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'tx not exist'})


class GetColorTxsTest(TestCase):
    def setUp(self):
        """
        block1:
            txs[0:30]:
                type: MINT
                color: 1
            txs[31:60]:
                type: MINT
                color: 2
            txs[61:90]:
                type: NORMAL
                color: 1
        block2:
            txs[91:120]:
                type: NORMAL
                color: 2
            txs[121:150]:
                type: LICENSE (non-standard type for color txs)
                color: 1
            tx3[151:180]:
                type: LICENSE (non-standard type for color txs)
                color: 2
        block3: (fork)
            txs[181:210]:
                type: NORMAL
                color: 1
        """
        test_sample = TestSetUp()
        self.address1 = test_sample.address1
        self.address2 = test_sample.address2
        self.block1 = test_sample.create_block('000004e0223a146664188edebf7efbce82c3a421ce70f30b71c156368c21caaf', 0, 1,
                                               None, 90, 1)
        self.block2 = test_sample.create_block('00000319eb1fbe75c75e6ad3970855ac67f8687febd230b3c26c074474889d3b', 1, 2,
                                               self.block1, 90, 1)
        self.block3 = test_sample.create_block('0000020897789853ddfa697e3c5b729c34ba10cb722f10147e13e6a0249038dd', 2, 3,
                                               self.block2, 30, 0)
        txs = []
        for i in range(30):
            txs.append(test_sample.create_mint_tx(str(i), self.block1, 1, i))
        for i in range(30, 60):
            txs.append(test_sample.create_mint_tx(str(i), self.block1, 2, i))
        for i in range(60, 90):
            txs.append(test_sample.create_normal_tx(str(i), self.block1, txs[i - 60].tx_outs.all()[0], 1, i))
        for i in range(90, 120):
            txs.append(test_sample.create_normal_tx(str(i), self.block2, txs[i - 60].tx_outs.all()[0], 2, i))
        for i in range(120, 150):
            txs.append(test_sample.create_other_type_tx(str(i), self.block2, 2, 1, i))
        for i in range(150, 180):
            txs.append(test_sample.create_other_type_tx(str(i), self.block2, 2, 2, i))
        for i in range(180, 210):
            txs.append(test_sample.create_normal_tx(str(i), self.block3, txs[i - 120].tx_outs.all()[0], 1, i))

    def tearDown(self):
        Address.objects.all().delete()
        Block.objects.all().delete()

    def test_get_color_txs(self):
        # default page
        url = '/explorer/v1/transactions/color/1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'], '89')
        self.assertEqual(response.json()['page']['ending_before'], '10')
        self.assertEqual(response.json()['page']['next_uri'], '/explorer/v1/transactions/color/1?starting_after=10')
        for i in range(50):
            self.assertEqual(int(response.json()['txs'][i]['vouts'][0]['color']), 1)
            self.assertTrue(response.json()['txs'][i]['type'] == 'NORMAL' or
                            response.json()['txs'][i]['type'] == 'MINT')

        # a new tx should not affect the next page query
        tx = Tx.objects.create(hash='1234', block=self.block1, version=1, type=1)
        TxIn.objects.create(tx=tx, position=0)
        TxOut.objects.create(tx=tx, value=100, position=0, scriptpubkey=binascii.unhexlify('aaaa'),
                             address=self.address1, spent=0, color=1)

        # second page
        url = response.json()['page']['next_uri']
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 10)
        self.assertEqual(response.json()['page']['starting_after'], '9')
        self.assertEqual(response.json()['page']['ending_before'], '0')
        self.assertEqual(response.json()['page']['next_uri'], None)
        for i in range(10):
            self.assertEqual(int(response.json()['txs'][i]['vouts'][0]['color']), 1)
            self.assertTrue(response.json()['txs'][i]['type'] == 'NORMAL' or
                            response.json()['txs'][i]['type'] == 'MINT')

    def test_page_with_param(self):
        # page with param
        url = '/explorer/v1/transactions/color/1?starting_after=20'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 20)
        self.assertEqual(response.json()['page']['starting_after'], '19')
        self.assertEqual(response.json()['page']['ending_before'], '0')
        self.assertEqual(response.json()['page']['next_uri'], None)
        for i in range(10):
            self.assertEqual(int(response.json()['txs'][i]['vouts'][0]['color']), 1)
            self.assertTrue(response.json()['txs'][i]['type'] == 'NORMAL' or
                            response.json()['txs'][i]['type'] == 'MINT')

        # empty page
        url = '/explorer/v1/transactions/color/1?starting_after=0'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 0)
        self.assertEqual(response.json()['page']['starting_after'], None)
        self.assertEqual(response.json()['page']['ending_before'], None)
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_color_without_tx(self):
        url = '/explorer/v1/transactions/color/3'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 0)
        self.assertEqual(response.json()['page']['starting_after'], None)
        self.assertEqual(response.json()['page']['ending_before'], None)
        self.assertEqual(response.json()['page']['next_uri'], None)

        url = '/explorer/v1/transactions/color/3?starting_after=10'
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
    def setUp(self):
        """
        block1:
            txs[0:30]:
                address: 126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB
                type: MINT
                color: 1
            txs[31:60]:
                address: 126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB
                type: MINT
                color: 2
            txs[61:90]:
                address: 126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB, 13JGvpZTEm8iUvpjavj3k9SmnwdrhFfcBx
                type: NORMAL
                color: 1
        block2:
            txs[91:120]:
                address: 126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB, 13JGvpZTEm8iUvpjavj3k9SmnwdrhFfcBx
                type: NORMAL
                color: 2
        """
        test_sample = TestSetUp()
        self.address1 = test_sample.address1
        self.address2 = test_sample.address2
        self.block1 = test_sample.create_block('000004e0223a146664188edebf7efbce82c3a421ce70f30b71c156368c21caaf', 0, 1,
                                               None, 90, 1)
        self.block2 = test_sample.create_block('00000319eb1fbe75c75e6ad3970855ac67f8687febd230b3c26c074474889d3b', 1, 2,
                                               self.block1, 90, 1)

        txs = []
        for i in range(30):
            txs.append(test_sample.create_mint_tx(str(i), self.block1, 1, i))
        for i in range(30, 60):
            txs.append(test_sample.create_mint_tx(str(i), self.block1, 2, i))
        for i in range(60, 90):
            txs.append(test_sample.create_normal_tx(str(i), self.block1, txs[i - 60].tx_outs.all()[0], 1, i))
        for i in range(90, 120):
            txs.append(test_sample.create_normal_tx(str(i), self.block2, txs[i - 60].tx_outs.all()[0], 2, i))

    def tearDown(self):
        Address.objects.all().delete()
        Block.objects.all().delete()

    def test_get_address_txs(self):
        # address: 13JGvpZTEm8iUvpjavj3k9SmnwdrhFfcBx
        # default page
        url = '/explorer/v1/transactions/address/13JGvpZTEm8iUvpjavj3k9SmnwdrhFfcBx'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'], '119')
        self.assertEqual(response.json()['page']['ending_before'], '70')
        self.assertEqual(response.json()['page']['next_uri'],
                         '/explorer/v1/transactions/address/13JGvpZTEm8iUvpjavj3k9SmnwdrhFfcBx?starting_after=70')
        for i in range(50):
            self.assertEqual(response.json()['txs'][i]['vouts'][0]['address'], '13JGvpZTEm8iUvpjavj3k9SmnwdrhFfcBx')

        # a new tx should not affect the next page query
        tx = Tx.objects.create(hash='1234', block=self.block1, version=1, type=1)
        TxIn.objects.create(tx=tx, position=0)
        TxOut.objects.create(tx=tx, value=100, position=0, scriptpubkey=binascii.unhexlify('aaaa'),
                             address=self.address1, spent=0, color=1)

        # second page
        url = response.json()['page']['next_uri']
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 10)
        self.assertEqual(response.json()['page']['starting_after'], '69')
        self.assertEqual(response.json()['page']['ending_before'], '60')
        self.assertEqual(response.json()['page']['next_uri'], None)
        for i in range(10):
            self.assertEqual(response.json()['txs'][i]['vouts'][0]['address'], '13JGvpZTEm8iUvpjavj3k9SmnwdrhFfcBx')

        # address: 126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB
        # default page
        url = '/explorer/v1/transactions/address/126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'], '119')
        self.assertEqual(response.json()['page']['ending_before'], '70')
        self.assertEqual(response.json()['page']['next_uri'],
                         '/explorer/v1/transactions/address/126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB?starting_after=70')
        for i in range(50):
            self.assertEqual(response.json()['txs'][i]['vouts'][1]['address'], '126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB')

        # a new tx should not affect the next page query
        tx = Tx.objects.create(hash='4321', block=self.block1, version=1, type=1)
        TxIn.objects.create(tx=tx, position=0)
        TxOut.objects.create(tx=tx, value=100, position=0, scriptpubkey=binascii.unhexlify('aaaa'),
                             address=self.address1, spent=0, color=1)

        # second page
        url = response.json()['page']['next_uri']
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'], '69')
        self.assertEqual(response.json()['page']['ending_before'], '20')
        self.assertEqual(response.json()['page']['next_uri'],
                         '/explorer/v1/transactions/address/126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB?starting_after=20')
        for i in range(10):
            self.assertEqual(response.json()['txs'][i]['vouts'][1]['address'], '126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB')
        for i in range(10, 50):
            self.assertEqual(response.json()['txs'][i]['vouts'][0]['address'], '126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB')

    def test_page_with_param(self):
        # page with param
        url = '/explorer/v1/transactions/address/13JGvpZTEm8iUvpjavj3k9SmnwdrhFfcBx?starting_after=80'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 20)
        self.assertEqual(response.json()['page']['starting_after'], '79')
        self.assertEqual(response.json()['page']['ending_before'], '60')
        self.assertEqual(response.json()['page']['next_uri'], None)
        for i in range(20):
            self.assertEqual(response.json()['txs'][i]['vouts'][0]['address'], '13JGvpZTEm8iUvpjavj3k9SmnwdrhFfcBx')

        url = '/explorer/v1/transactions/address/126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB?starting_after=80'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 50)
        self.assertEqual(response.json()['page']['starting_after'], '79')
        self.assertEqual(response.json()['page']['ending_before'], '30')
        self.assertEqual(response.json()['page']['next_uri'],
                         '/explorer/v1/transactions/address/126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB?starting_after=30')
        for i in range(20):
            self.assertEqual(response.json()['txs'][i]['vouts'][1]['address'], '126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB')
        for i in range(20, 50):
            self.assertEqual(response.json()['txs'][i]['vouts'][0]['address'], '126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB')

        # empty page
        url = '/explorer/v1/transactions/address/13JGvpZTEm8iUvpjavj3k9SmnwdrhFfcBx?starting_after=0'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 0)
        self.assertEqual(response.json()['page']['starting_after'], None)
        self.assertEqual(response.json()['page']['ending_before'], None)
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_address_without_tx(self):
        url = '/explorer/v1/transactions/address/13JGvpZTEm8iUvpjavj3k9SmnwdrhFfcaa'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 0)
        self.assertEqual(response.json()['page']['starting_after'], None)
        self.assertEqual(response.json()['page']['ending_before'], None)
        self.assertEqual(response.json()['page']['next_uri'], None)

        url = '/explorer/v1/transactions/address/13JGvpZTEm8iUvpjavj3k9SmnwdrhFfcaa?starting_after=10'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(response.json()['txs']), 0)
        self.assertEqual(response.json()['page']['starting_after'], None)
        self.assertEqual(response.json()['page']['ending_before'], None)
        self.assertEqual(response.json()['page']['next_uri'], None)

    def test_tx_not_found(self):
        url = '/explorer/v1/transactions/address/13JGvpZTEm8iUvpjavj3k9SmnwdrhFfcBx?starting_after=abc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'tx not exist'})

        url = '/explorer/v1/transactions/address/126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB?starting_after=abc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'tx not exist'})
