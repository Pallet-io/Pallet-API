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
        self.assertEqual(146, blocks.count())

    def test_block_hash(self):
        blocks = Block.objects.all()
        self.assertEqual('000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f', blocks.get(height=0).hash)
        self.assertEqual('0000067cca8825041846b582e285f8e1623525e5033ea0cd3c18ce358ef5b5ae', blocks.get(height=10).hash)
        self.assertEqual('00000848d8e02b01fead9eac33bcfbdee23d564fdf7e2c2f8931a0433c4617d4', blocks.get(height=60).hash)
        self.assertEqual('00000ca6f1c7039d0ea66e8154aeee6ad8672aee2d47a73b61303e34a6f11eab', blocks.get(height=100).hash)
        self.assertEqual('000005f5e6fc2eea47e63b8fad47698450e496771a64cdd1d89c4bebadb8cae4', blocks.get(height=119).hash)

    def test_tx_count(self):
        blocks = Block.objects.all()
        self.assertEqual(1, blocks.get(height=0).txs.count())
        self.assertEqual(1, blocks.get(height=10).txs.count())
        self.assertEqual(3, blocks.get(height=106).txs.count())
        self.assertEqual(6, blocks.get(height=119).txs.count())

    def test_block_tx(self):
        """Check if certain transactions exist in some blocks."""
        blocks = Block.objects.all()
        txs = Tx.objects.all()
        self.assertEqual(txs.get(hash='4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b').block,
                         blocks.get(height=0))
        self.assertEqual(txs.get(hash='e39ad76576450e3b75b3373d6d8731351dfc1377b760002b998b7bf9dfe03399').block,
                         blocks.get(height=69))
        self.assertEqual(txs.get(hash='5b1cb755bc3d4d85e5b70e77724e67f0831b5913ed56061672f6482ac791c503').block,
                         blocks.get(height=106))
        self.assertEqual(txs.get(hash='588484fd1177fb66a831e2fb5dad36744e262787646e2b30af345946bb2f5801').block,
                         blocks.get(height=119))

    def test_block_height(self):
        blocks = Block.objects.all()
        self.assertEqual(blocks.get(hash='000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f').height, 0)
        self.assertEqual(blocks.get(hash='0000067cca8825041846b582e285f8e1623525e5033ea0cd3c18ce358ef5b5ae').height, 10)
        self.assertEqual(blocks.get(hash='00000b3f3d75ccb18f9e9dbbbd1613a5354b60e94ef6ede99eb2fc23c532cd60').height, 69)
        self.assertEqual(blocks.get(hash='000001177de14a9db230f84034dcc6bca3bb5b21cf7dde935209c9b92bed3946').height, 106)
        self.assertEqual(blocks.get(hash='000005f5e6fc2eea47e63b8fad47698450e496771a64cdd1d89c4bebadb8cae4').height, 119)

    def test_in_longest(self):
        """Block file only contains a linear blockchain, so every block should have `in_longest` equals to 1."""
        blocks = Block.objects.all()
        for b in blocks:
            self.assertEqual(b.in_longest, 1)

    def test_prev_block(self):
        blocks = Block.objects.all()
        b = blocks.get(hash='000005f5e6fc2eea47e63b8fad47698450e496771a64cdd1d89c4bebadb8cae4')
        self.assertEqual(b.prev_block.hash, '0000024925616863c23a5100fe383611647659c610bd6588e0987fbe4dba0fd4')

        b = blocks.get(hash='00000b3f3d75ccb18f9e9dbbbd1613a5354b60e94ef6ede99eb2fc23c532cd60')
        self.assertEqual(b.prev_block.hash, '0000006ea24db4014f49295fc177b04be8fdeb63d7e440d17c0790c52b378835')

        b = blocks.get(hash='000001177de14a9db230f84034dcc6bca3bb5b21cf7dde935209c9b92bed3946')
        self.assertEqual(b.prev_block.hash, '0000088a506c85c8cc09d758cd76a33016e028884bdc1d725f37a8c5e83d82fa')

        b = blocks.get(hash='000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f')
        self.assertFalse(b.prev_block)

    def test_next_block(self):
        blocks = Block.objects.all()
        b = blocks.get(hash='0000024925616863c23a5100fe383611647659c610bd6588e0987fbe4dba0fd4')
        self.assertEqual(b.next_blocks.all().first().hash,
                         '000005f5e6fc2eea47e63b8fad47698450e496771a64cdd1d89c4bebadb8cae4')

        b = blocks.get(hash='0000006ea24db4014f49295fc177b04be8fdeb63d7e440d17c0790c52b378835')
        self.assertEqual(b.next_blocks.all().first().hash,
                         '00000b3f3d75ccb18f9e9dbbbd1613a5354b60e94ef6ede99eb2fc23c532cd60')

        b = blocks.get(hash='0000082a0a1e5ad7cd4c2ec356f69e5969241c130f8e4e3021b6b7281d4132db')
        self.assertEqual(b.next_blocks.all().first().hash,
                         '00000b23c2517ec911f89562162ff5864582418f76a5f261ff87370b5b400e86')

        b = blocks.get(hash='00000f6326e6b87fb5197acfcdf1b99a7e04650ad9db5c2a7759025330a5f068')
        self.assertFalse(b.next_blocks.all())

    def test_block_time(self):
        blocks = Block.objects.all()
        self.assertEqual(blocks.get(height=0).time, 1231006505)
        self.assertEqual(blocks.get(height=10).time, 1511409144)
        self.assertEqual(blocks.get(height=100).time, 1511409705)
        self.assertEqual(blocks.get(height=119).time, 1511412555)

    def test_block_nonce(self):
        blocks = Block.objects.all()
        self.assertEqual(blocks.get(height=0).nonce, 2083236893)
        self.assertEqual(blocks.get(height=10).nonce, 43883)
        self.assertEqual(blocks.get(height=100).nonce, 52296)
        self.assertEqual(blocks.get(height=119).nonce, 60144)

    def test_address(self):
        addresses = Address.objects.all()
        self.assertTrue(addresses.get(address='1MwwRgJQPnBzdrJXw4HBgB1uS37iC5NFHt'))
        self.assertTrue(addresses.get(address='1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK'))

    def test_tx(self):
        tx = Tx.objects.get(hash='4a4314b399b56cc3562f00d036d29d7eb850eb48f8b352d834f1e3d7a4ad0c96')
        self.assertEqual(tx.tx_ins.all().count(), 1)
        self.assertIsNone(tx.tx_ins.all().first().txout)
        self.assertEqual(tx.tx_outs.all().count(), 2)
        self.assertEqual(tx.tx_outs.get(position=0).address.address, '1AjtXyz4mvoQysqo9VqhAeS8MdZNhhfHHt')
        self.assertEqual(tx.tx_outs.get(position=0).value, 5000012240)
        self.assertEqual(tx.tx_outs.get(position=1).address.address, '')
        self.assertEqual(tx.tx_outs.get(position=1).value, 0)

        tx = Tx.objects.get(hash='5b1cb755bc3d4d85e5b70e77724e67f0831b5913ed56061672f6482ac791c503')
        self.assertEqual(tx.tx_ins.all().count(), 1)
        self.assertEqual(tx.tx_ins.all().first().txout.tx.hash,
                         '95154e178256b2ac222666bce7556f9e22b0efa165b7792e2e01b93d8c2b4f86')
        self.assertEqual(tx.tx_outs.all().count(), 2)
        self.assertEqual(tx.tx_outs.get(position=0).address.address, '1KeauFs1g7v7R2BCKBJWM4GacAjNn8SiRK')
        self.assertEqual(tx.tx_outs.get(position=0).value, 3000000000)
        self.assertEqual(tx.tx_outs.get(position=1).address.address, '16AvsjkVXWhFfuw9AKsWXeQqQ7o7fbwb6L')
        self.assertEqual(tx.tx_outs.get(position=1).value, 1999996160)
