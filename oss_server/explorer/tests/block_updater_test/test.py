import os

from django.test import TestCase

from explorer.models import Address, Block, Datadir, Tx
from explorer.update_db import BlockDBUpdater


class BlkTest(TestCase):
    """
    This test tests a single linear (no fork) blockchain. Every block should be in the main chain.
    """
    @classmethod
    def setUpClass(cls):
        updater = BlockDBUpdater(os.path.dirname(os.path.realpath(__file__)))
        updater.update()

    @classmethod
    def tearDownClass(cls):
        Block.objects.all().delete()
        Datadir.objects.all().delete()

    def test_block_count(self):
        blocks = Block.objects.all()
        self.assertEqual(140, blocks.count())

    def test_block_hash(self):
        blocks = Block.objects.all()
        self.assertEqual('00000dd9a598e6f1e47c41a9d56153897650b73c05ddfe9d6dfc3ae3ee251781', blocks.get(height=0).hash)
        self.assertEqual('00000a17f10d3098ec342315a99c8442bc2d03413ef493207c7fef25f06740cd', blocks.get(height=16).hash)
        self.assertEqual('0000009fc93b77da91e6b773b7d9ba598372f55f57a609e3e668f7a703aa2b70', blocks.get(height=64).hash)
        self.assertEqual('0000057cfd51b979c63e5133805eca85868c0d60095486c161ebdd2f2f150a0b', blocks.get(height=128).hash)
        self.assertEqual('00000d0d2416c45515590f4b6d872bfb9763ce8555dcdcbea5f49ab41b872cf7', blocks.get(height=139).hash)

    def test_tx_count(self):
        blocks = Block.objects.all()
        self.assertEqual(1, blocks.get(height=0).txs.count())
        self.assertEqual(2, blocks.get(height=2).txs.count())
        self.assertEqual(2, blocks.get(height=35).txs.count())
        self.assertEqual(2, blocks.get(height=69).txs.count())
        self.assertEqual(5, blocks.get(height=129).txs.count())
        self.assertEqual(1, blocks.get(height=139).txs.count())

    def test_block_tx(self):
        """Check if certain transactions exist in some blocks."""
        blocks = Block.objects.all()
        txs = Tx.objects.all()
        self.assertEqual(txs.get(hash='e6c46939e54cba94097ab1d2d456c59dfd38eaa1cf1b6f7b2caf021dbd5b7178').block,
                         blocks.get(height=0))
        self.assertEqual(txs.get(hash='9bf439701e6d467734d24cb217ff88d1c174ebaa9ad2964e3b86784cc057c367').block,
                         blocks.get(height=69))
        self.assertEqual(txs.get(hash='ffeeaac74d23bb24f7dda74541685896331c7057cb39ca2144823ede88d2c079').block,
                         blocks.get(height=69))
        self.assertEqual(txs.get(hash='bfe9acd8be6754639bc3f538e538f42579c87bf10583b0551bcfbe0dce9f9587').block,
                         blocks.get(height=139))

    def test_block_height(self):
        blocks = Block.objects.all()
        self.assertEqual(blocks.get(hash='00000dd9a598e6f1e47c41a9d56153897650b73c05ddfe9d6dfc3ae3ee251781').height, 0)
        self.assertEqual(blocks.get(hash='00000b63b64496a44a55d89c27d1602656e4883b81af24f85199548e1c04f6c9').height, 10)
        self.assertEqual(blocks.get(hash='00000701c1f94b778f89b157c0e2022d329ffc728c5f5f3df2372b6d8d293e34').height, 50)
        self.assertEqual(blocks.get(hash='00000864b5c034c640cce261db907d2e687287a888d7dd06a64b2b86fc5f44f6').height, 90)
        self.assertEqual(blocks.get(hash='00000d0d2416c45515590f4b6d872bfb9763ce8555dcdcbea5f49ab41b872cf7').height, 139)

    def test_in_longest(self):
        """Block file only contains a linear blockchain, so every block should have `in_longest` equals to 1."""
        blocks = Block.objects.all()
        for b in blocks:
            self.assertEqual(b.in_longest, 1)

    def test_prev_block(self):
        blocks = Block.objects.all()
        b = blocks.get(hash='00000d0d2416c45515590f4b6d872bfb9763ce8555dcdcbea5f49ab41b872cf7')
        self.assertEqual(b.prev_block.hash, '00000cbb5a711a851e0bffe7460365e4691b0e3c155e479d0ca21ce4e31efd17')

        b = blocks.get(hash='00000cbb5a711a851e0bffe7460365e4691b0e3c155e479d0ca21ce4e31efd17')
        self.assertEqual(b.prev_block.hash, '0000019bd428327d9b436ad35228be82b6fe817c7d7f39849589c48b3e505a2c')

        b = blocks.get(hash='0000019bd428327d9b436ad35228be82b6fe817c7d7f39849589c48b3e505a2c')
        self.assertEqual(b.prev_block.hash, '000009a6da0df977b1269c8403347a4ec59ed56adf1cff3bcc4b85846b674f6c')

        b = blocks.get(hash='00000dd9a598e6f1e47c41a9d56153897650b73c05ddfe9d6dfc3ae3ee251781')
        self.assertFalse(b.prev_block)

    def test_next_block(self):
        blocks = Block.objects.all()
        b = blocks.get(hash='00000dd9a598e6f1e47c41a9d56153897650b73c05ddfe9d6dfc3ae3ee251781')
        self.assertEqual(b.next_blocks.all().first().hash,
                         '000000d3b5d70f6cf172802a9d084bb2d98885e6600ee37199f2c0c43c8abd55')

        b = blocks.get(hash='000000d3b5d70f6cf172802a9d084bb2d98885e6600ee37199f2c0c43c8abd55')
        self.assertEqual(b.next_blocks.all().first().hash,
                         '00000150037c6a21797fded5124b0f9e6f2166f8f570f08d74d24b4eabf16ba1')

        b = blocks.get(hash='00000150037c6a21797fded5124b0f9e6f2166f8f570f08d74d24b4eabf16ba1')
        self.assertEqual(b.next_blocks.all().first().hash,
                         '0000012c5b86d2eaea897317a8941debed3d37ae07cf78ced10a5f138dec7c34')

        b = blocks.get(hash='00000d0d2416c45515590f4b6d872bfb9763ce8555dcdcbea5f49ab41b872cf7')
        self.assertFalse(b.next_blocks.all())

    def test_block_time(self):
        blocks = Block.objects.all()
        self.assertEqual(blocks.get(height=0).time, 1421909240)
        self.assertEqual(blocks.get(height=16).time, 1469608003)
        self.assertEqual(blocks.get(height=64).time, 1469676045)
        self.assertEqual(blocks.get(height=128).time, 1469676423)
        self.assertEqual(blocks.get(height=139).time, 1469698351)

    def test_block_nonce(self):
        blocks = Block.objects.all()
        self.assertEqual(blocks.get(height=0).nonce, 1035503)
        self.assertEqual(blocks.get(height=16).nonce, 155279)
        self.assertEqual(blocks.get(height=64).nonce, 715255)
        self.assertEqual(blocks.get(height=128).nonce, 11861)
        self.assertEqual(blocks.get(height=139).nonce, 153976)

    def test_address(self):
        addresses = Address.objects.all()
        self.assertTrue(addresses.get(address='12Ef23un7RLY4DRZSejoSM1zqLuwrMX6gw'))
        self.assertTrue(addresses.get(address='1H2jo3AQLoNhKXjDUhYTPHE986iBzggfQJ'))

    def test_tx(self):
        tx = Tx.objects.get(hash='64f15550e4c7a1640769f8d55a5c261c6578ad4205ba4b854fbdb2907ac12ac0')
        self.assertEqual(tx.type, 0)
        self.assertEqual(tx.tx_ins.all().count(), 1)
        self.assertIsNone(tx.tx_ins.all().first().txout)
        self.assertEqual(tx.tx_outs.all().count(), 2)
        self.assertEqual(tx.tx_outs.get(position=0).address.address, '1H2jo3AQLoNhKXjDUhYTPHE986iBzggfQJ')
        self.assertEqual(tx.tx_outs.get(position=0).value, 0)
        self.assertEqual(tx.tx_outs.get(position=0).color, 0)
        self.assertEqual(tx.tx_outs.get(position=1).address.address, '1H2jo3AQLoNhKXjDUhYTPHE986iBzggfQJ')
        self.assertEqual(tx.tx_outs.get(position=1).value, 400000000)
        self.assertEqual(tx.tx_outs.get(position=1).color, 1)

        tx = Tx.objects.get(hash='5f9b8d8ed9418d061b450f7572fa428c273104d033341737ae45cd738d70964b')
        self.assertEqual(tx.type, 0)
        self.assertEqual(tx.tx_ins.all().count(), 1)
        self.assertEqual(tx.tx_ins.all().first().txout.tx.hash,
                         '4606367894e8ef71a49de69622700680a68bc45e6a219006763c6b243b46ffbf')
        self.assertEqual(tx.tx_outs.all().count(), 2)
        self.assertEqual(tx.tx_outs.get(position=0).address.address, '1H2jo3AQLoNhKXjDUhYTPHE986iBzggfQJ')
        self.assertEqual(tx.tx_outs.get(position=0).value, 100000000)
        self.assertEqual(tx.tx_outs.get(position=0).color, 1)
        self.assertEqual(tx.tx_outs.get(position=1).address.address, '1H2jo3AQLoNhKXjDUhYTPHE986iBzggfQJ')
        self.assertEqual(tx.tx_outs.get(position=1).value, 89600000000)
        self.assertEqual(tx.tx_outs.get(position=1).color, 1)
