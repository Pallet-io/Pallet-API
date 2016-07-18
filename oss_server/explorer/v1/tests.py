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
        self.assertEqual(response.json()['block']['hash'], '00000319eb1fbe75c75e6ad3970855ac67f8687febd230b3c26c074474889d3b')

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
