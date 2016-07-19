import binascii
import httplib
import random

from django.test import TestCase

from ..models import *


class GetLatestBlocksTest(TestCase):
    def setUp(self):
        self.url = '/explorer/v1/blocks'
        block = Block.objects.create(hash=str(0), time=0, tx_count=1)
        # choose three random block to fork
        random_number_list = random.sample(range(1, 55), 3)
        for i in range(1, 55):
            if i in random_number_list:
                Block.objects.create(hash=str(i), time=i, prev_block=block, tx_count=1, in_longest=0)
            else:
                block = Block.objects.create(hash=str(i), time=i, prev_block=block, tx_count=1, in_longest=1)

    def test_get_latest_blocks(self):
        response = self.client.get(self.url)
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
        block1 = Block.objects.create(hash='000004e0223a146664188edebf7efbce82c3a421ce70f30b71c156368c21caaf',
                                      tx_count=1)
        block2 = Block.objects.create(hash='00000319eb1fbe75c75e6ad3970855ac67f8687febd230b3c26c074474889d3b',
                                      prev_block=block1, tx_count=1)
        block3 = Block.objects.create(hash='0000020897789853ddfa697e3c5b729c34ba10cb722f10147e13e6a0249038dd',
                                      prev_block=block2, tx_count=1)

    def test_get_block_by_hash(self):
        url = '/explorer/v1/blocks/00000319eb1fbe75c75e6ad3970855ac67f8687febd230b3c26c074474889d3b'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['block']['hash'],
                         '00000319eb1fbe75c75e6ad3970855ac67f8687febd230b3c26c074474889d3b')

    def test_block_not_found(self):
        url = '/explorer/v1/blocks/00000319eb1fbe75c75e6ad3970855ac67f8687febd230b3c26c074474889d3c'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'block not exist'})


class GetBlockByHeightTest(TestCase):
    def setUp(self):
        block1 = Block.objects.create(hash='000004e0223a146664188edebf7efbce82c3a421ce70f30b71c156368c21caaf', height=0,
                                      tx_count=1, in_longest=1)
        block2 = Block.objects.create(hash='00000319eb1fbe75c75e6ad3970855ac67f8687febd230b3c26c074474889d3b', height=1,
                                      prev_block=block1, tx_count=1, in_longest=1)
        block3 = Block.objects.create(hash='0000020897789853ddfa697e3c5b729c34ba10cb722f10147e13e6a0249038dd', height=2,
                                      prev_block=block2, tx_count=1, in_longest=1)
        block4 = Block.objects.create(hash='00000808ca8cb51a1c380a972ed2394b66cb9fe814fa898374858291c525d399', height=2,
                                      prev_block=block2, tx_count=1, in_longest=0)

    def test_get_block_by_height(self):
        url = '/explorer/v1/blocks/2'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(int(response.json()['block']['height']), 2)
        self.assertEqual(response.json()['block']['branch'], 'main')

    def test_block_not_found(self):
        url = '/explorer/v1/blocks/4'
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
                value: 100
            tx4:
                type: normal tx from address1 to address2
                addr: address1, address2
                value: 89, 10
        """
        self.address1 = Address.objects.create(address='126fiiHJY4PCba1NXoPpSSo3kHpZmGYiHB')
        self.baseScriptPubKey = '21036bbb2d3974e203d6f89c30ab17f05e7bd3580954c5198875f235d292e00fdbeaac'
        self.mintScriptPubKey = '76a9140c0a86d78bc3f71db1f969353da4769e2084bc5988ac'
        self.address2 = Address.objects.create(address='13JGvpZTEm8iUvpjavj3k9SmnwdrhFfcBx')
        self.block1 = Block.objects.create(hash='000004e0223a146664188edebf7efbce82c3a421ce70f30b71c156368c21caaf',
                                           height=0, tx_count=1, in_longest=1)
        self.block2 = Block.objects.create(hash='00000319eb1fbe75c75e6ad3970855ac67f8687febd230b3c26c074474889d3b',
                                           height=1, prev_block=self.block1, tx_count=1, in_longest=1)
        self.tx1 = self.createCoinbaseTx('7e336fb514f829b57b5147f1d81abb35f7f08ebd97ef8e8063f2cfdf3ed2ca07',
                                         self.block1)
        self.tx2 = self.createCoinbaseTx('c0daefcf66be12f4e3f426c8b08babf437d7945e70bacee492df2c4a04b801e1',
                                         self.block2)
        self.tx3 = self.createMintTx('d562f957f68be51e11f7ffd1964df48dc55fdfed1357e51034990b8504fddccb', self.block2,
                                     10000000000)
        self.tx4 = self.createNormalTx('2e75d6117852fb0f3a42951a683cf9ab52f2b7d7578f5ac0487c2256aa301769', self.block2,
                                       1000000000, '76a91419349e6f4108e9a387cbd0c090e445610e1449ec88ac', 8900000000)

    def createCoinbaseTx(self, hash, block):
        tx = Tx.objects.create(hash=hash, block=block, version=1, type=0)
        TxIn.objects.create(tx=tx, position=0)
        TxOut.objects.create(tx=tx, value=0, position=0, scriptpubkey=binascii.unhexlify(self.baseScriptPubKey),
                             address=self.address1, spent=0, color=0)
        return tx

    def createMintTx(self, hash, block, value):
        tx = Tx.objects.create(hash=hash, block=block, version=1, type=1)
        TxIn.objects.create(tx=tx, position=0)
        # `spent = 1` because tx4 would spend this txout
        TxOut.objects.create(tx=tx, value=value, position=0, scriptpubkey=binascii.unhexlify(self.mintScriptPubKey),
                             address=self.address1, spent=1, color=1)
        return tx

    def createNormalTx(self, hash, block, value, scripPubKey, change):
        tx = Tx.objects.create(hash=hash, block=block, version=1, type=0)
        TxIn.objects.create(tx=tx, txout=self.tx3.tx_outs.all()[0], position=0)
        TxOut.objects.create(tx=tx, value=value, position=0, scriptpubkey=binascii.unhexlify(scripPubKey),
                             address=self.address2, spent=0, color=1)
        TxOut.objects.create(tx=tx, value=change, position=1, scriptpubkey=binascii.unhexlify(self.baseScriptPubKey),
                             address=self.address1, spent=0, color=1)
        return tx

    def test_get_tx_by_hash(self):
        # mint tx
        url = '/explorer/v1/transactions/d562f957f68be51e11f7ffd1964df48dc55fdfed1357e51034990b8504fddccb'
        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['tx']['hash'],
                         'd562f957f68be51e11f7ffd1964df48dc55fdfed1357e51034990b8504fddccb')
        self.assertEqual(response.json()['tx']['block_hash'], self.block2.hash)
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
