import sys

from django.db.models import Max

from blocktools.block import Block
from blocktools.blocktools import *
from .models import Block as BlockDb
from .models import Address, Datadir, Tx, TxOut, TxIn


class BlockDBUpdater:

    def update(self):
        self._parse_raw_block_to_db()
        self._update_chain_related_info()

    def set_datadir(self, dirname, blkfile_number=0, blkfile_offset=0):
        datadir = self._get_datadir()
        if not datadir:
            datadir = Datadir()
        datadir.dirname = dirname
        datadir.blkfile_number = blkfile_number
        datadir.blkfile_offset = blkfile_offset
        datadir.save()

    def clean_block_db(self):
        BlockDb.objects.all().delete()
        datadir = self._get_datadir()
        self.set_datadir(datadir.dirname, 0, 0)

    def _update_chain_related_info(self):
        self._update_block_in_longest()
        self._update_txout_spent()

    def _update_block_in_longest(self):
        end_block = self._get_main_chain_end_block()
        current_block = end_block
        main_branch_next_block = None

        print "backward update `in_longest`"
        while current_block and not current_block.in_longest:
            print_dot()
            current_block.in_longest = 1
            current_block.save()
            main_branch_next_block = current_block
            current_block = current_block.prev_block

        print ""
        print "forward update `in_longest`"
        while current_block and main_branch_next_block:
            print_dot()
            next_blocks = current_block.next_blocks.filter(
                in_longest=1).exclude(hash=main_branch_next_block.hash)
            if next_blocks.count() > 1:
                raise BlockDbException('There might be forks on `in_longest` blocks')
            elif next_blocks.count() == 0:
                next_block = None
            else:
                next_block = next_blocks[0]
                next_block.in_longest = 0
                next_block.save()
            current_block = next_block
        print ""

    def _update_txout_spent(self):
        TxOut.objects.filter(tx__block__in_longest=0).update(spent=None)
        TxOut.objects.filter(tx_in__isnull=False, tx__block__in_longest=1).update(spent=1)
        TxOut.objects.filter(tx_in__isnull=True, tx__block__in_longest=1).update(spent=0)

    def _get_main_chain_end_block(self):
        return BlockDb.objects.latest('chain_work')

    def _parse_raw_block_to_db(self):
        file_path, file_offset = self._get_file_info()
        blockchain = open(file_path, 'rb')
        blockchain.seek(file_offset, 0)

        while blockchain:
            for raw_block in self._parse_raw_block(blockchain):
                print_dot()
                self._raw_block_to_db(raw_block)

            datadir = self._get_datadir()
            self.set_datadir(datadir.dirname, datadir.blkfile_number, blockchain.tell())
            blockchain.close()
            blockchain = self._try_open_next_blk_file()

        print ""

    def _raw_block_to_db(self, block):
        block_db = BlockDb()
        blockheader = block.blockHeader
        block_db.hash = blockheader.blockHash
        block_db.merkle_root = hashStr(blockheader.merkleHash)
        block_db.time = blockheader.time
        block_db.bits = blockheader.bits
        block_db.nonce = blockheader.nonce
        block_db.version = blockheader.version
        block_db.size = block.blocksize
        block_db.in_longest = 0  # `in_longest` set to 0 first and update later
        block_db.tx_count = len(block.Txs)

        prev_block = self._get_db_block_by_hash(hashStr(blockheader.previousHash))
        block_db.prev_block = prev_block
        if prev_block:
            block_db.chain_work = prev_block.chain_work + blockheader.blockWork
            block_db.height = prev_block.height + 1
        else:
            block_db.chain_work = blockheader.blockWork
            block_db.height = 0

        block_db.save()

        for tx in block.Txs:
            self._raw_tx_to_db(tx, block_db)

    def _raw_tx_to_db(self, tx, block_db):
        tx_db = Tx()
        tx_db.hash = tx.txHash
        tx_db.block = block_db
        tx_db.version = tx.version
        tx_db.locktime = tx.lockTime
        tx_db.type = tx.txType
        tx_db.size = tx.size
        tx_db.time = block_db.time
        tx_db.save()

        for i in range(tx.inCount):
            self._raw_txin_to_db(tx.inputs[i], i, tx_db)
        for i in range(tx.outCount):
            self._raw_txout_to_db(tx.outputs[i], i, tx_db)

    def _raw_txin_to_db(self, txin, position, tx_db):
        txin_db = TxIn()
        txin_db.tx = tx_db
        prev_tx = self._get_db_tx_by_hash(hashStr(txin.prevhash))
        if prev_tx:
            txin_db.txout = prev_tx.tx_outs.get(position=txin.txOutId)
        else:
            txin_db.txout = None
        txin_db.position = position
        txin_db.scriptsig = txin.scriptSig
        txin_db.sequence = txin.seqNo
        txin_db.save()

    def _raw_txout_to_db(self, txout, position, tx_db):
        txout_db = TxOut()
        txout_db.tx = tx_db
        txout_db.value = txout.value
        txout_db.position = position
        txout_db.scriptpubkey = txout.pubkey
        txout_db.address, _ = Address.objects.get_or_create(address=txout.address)
        txout_db.color = txout.color
        txout_db.save()

    def _get_db_tx_by_hash(self, tx_hash):
        try:
            return Tx.objects.get(hash=tx_hash)
        except Tx.DoesNotExist:
            return None

    def _get_db_block_by_hash(self, block_hash):
        try:
            return BlockDb.objects.get(hash=block_hash)
        except BlockDb.DoesNotExist:
            return None

    def _try_open_next_blk_file(self):
        datadir = self._get_datadir()
        datadir.blkfile_number += 1
        datadir.blkfile_offset = 0
        file_name = 'blk{:05d}.dat'.format(datadir.blkfile_number)
        file_path = datadir.dirname + file_name
        try:
            blockchain = open(file_path, 'rb')
        except IOError:
            return None
        else:
            datadir.save()
            return blockchain

    def _parse_raw_block(self, blockchain_file):
        continue_parsing = True
        while continue_parsing:
            file_offset = blockchain_file.tell()
            block = Block(blockchain_file)
            continue_parsing = block.continueParsing

            if continue_parsing:
                yield block
            else:
                blockchain_file.seek(file_offset, 0)

    def _get_datadir(self):
        datadir_all = Datadir.objects.all()

        if datadir_all.count() == 1:
            return datadir_all[0]
        elif datadir_all.count() > 1:
            raise self.BadDatadirException('More than one datadirs are in DB.')
        else:
            return None

    def _get_file_info(self):
        datadir = self._get_datadir()
        if not datadir:
            raise self.BadDatadirException('Datadir has not been set yet.')

        file_name = 'blk{:05d}.dat'.format(datadir.blkfile_number)
        file_path = datadir.dirname + file_name
        file_offset = datadir.blkfile_offset
        return file_path, file_offset

    class BadDatadirException(Exception):
        """Exception for datadir related issue"""

    class BlockDbException(Exception):
        """Exception for block db contents"""


def print_dot():
    sys.stdout.write('.')
    sys.stdout.flush()


def test():
    updater = BlockDBUpdater()
    updater.clean_block_db()
    updater.update()
