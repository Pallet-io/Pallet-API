import os

from django.core.exceptions import MultipleObjectsReturned
from django.db import transaction

from blocktools.block import Block
from blocktools.blocktools import *

from .configs import BLK_DIR
from .models import Block as BlockDb
from .models import Address, Datadir, Tx, TxIn, TxOut


class BlockDbException(Exception):
    """Exception for block db contents."""


class BlockDBUpdater(object):

    def __init__(self, blk_dir=BLK_DIR, batch_num=50):
        self.blk_dir = blk_dir
        self.batch_num = batch_num
        self.blocks_hash_cache = []

    def update(self):
        # Read the blk file (possibly from last read position) as many as possible, and check if
        # there's a following blk file to read. If so, continue to parse the file.
        while True:
            file_path, file_offset = self._get_blk_file_info()
            self._parse_raw_block_to_db(file_path, file_offset)

            file_path, file_offset = self._get_next_blk_file_info(), 0
            if not file_path:
                break

    def _update_chain_related_info(self):
        self.blocks_hash_cache = []
        self._update_block_in_longest()
        self._update_txout_spent()

    def _update_block_in_longest(self):
        # Get the block with biggest chain_work.
        current_block = BlockDb.objects.latest('chain_work')
        main_branch_next_block = None

        # From `current_block`, move backward and set `in_longest` of previous blocks
        # to 1 until we meet the fork point.
        while current_block and not current_block.in_longest:
            self.blocks_hash_cache.append(current_block.hash)
            current_block.in_longest = 1
            current_block.save()
            main_branch_next_block = current_block
            current_block = current_block.prev_block

        # From the fork point, set `in_longest` of blocks in the other fork to 0.
        while current_block and main_branch_next_block:
            self.blocks_hash_cache.append(current_block.hash)

            next_blocks = (current_block.next_blocks
                           .filter(in_longest=1).exclude(hash=main_branch_next_block.hash))

            if next_blocks.count() > 1:
                raise BlockDbException('Discovered more than one fork with `in_longest=1`.')
            elif next_blocks.count() == 0:
                next_block = None
            else:
                next_block = next_blocks[0]
                next_block.in_longest = 0
                next_block.save()
            current_block = next_block

    def _update_txout_spent(self):
        txouts_to_update = TxOut.objects.filter(tx__block__hash__in=self.blocks_hash_cache)
        txouts_to_update.filter(tx__block__in_longest=0).update(spent=None)

        main_chain_txouts = txouts_to_update.filter(tx__block__in_longest=1)

        # reset every `spent` of `txout` to 0 first
        main_chain_txouts.update(spent=0)

        # update whichever `txout` has a `tx_in` in mainchain
        main_chain_txouts.filter(
            tx_in__isnull=False,
            tx_in__tx__block__in_longest=1
        ).update(spent=1)

    def _parse_raw_block_to_db(self, file_path, file_offset):
        with open(file_path, 'rb') as blockchain:
            blockchain.seek(file_offset)

            blocks = []
            for raw_block in self._parse_raw_block(blockchain):
                blocks.append(raw_block)
                # Use atomic transaction for every `batch_num` blocks.
                if len(blocks) == self.batch_num:
                    self._batch_update_blocks(blockchain, blocks)
                    blocks = []

            self._batch_update_blocks(blockchain, blocks)

    def _batch_update_blocks(self, blockchain, block_batch):
        with transaction.atomic('explorer_db'):
            self._store_blocks(blockchain, block_batch)
            self._update_chain_related_info()

    def _parse_raw_block(self, blockchain_file):
        continue_parsing = True
        while continue_parsing:
            # Keep current file offset.
            file_offset = blockchain_file.tell()
            block = Block(blockchain_file)
            continue_parsing = block.continueParsing

            if continue_parsing:
                yield block
            else:
                # Revert to previous file offset if we didn't parse anything.
                blockchain_file.seek(file_offset)

    def _store_blocks(self, blockchain, blocks):
        # Write blocks and update blk file offset in the database. Blk file offset is retrieved
        # by calling tell() on `blockchain`. Transaction is used to ensure data integrity.
        for block in blocks:
            self._raw_block_to_db(block)
        datadir = self._get_or_create_datadir()
        datadir.blkfile_offset = blockchain.tell()
        datadir.save()

    def _raw_block_to_db(self, block):
        blockheader = block.blockHeader
        block_db = BlockDb(
            hash=blockheader.blockHash,
            merkle_root=hashStr(blockheader.merkleHash),
            time=blockheader.time,
            bits=blockheader.bits,
            nonce=blockheader.nonce,
            version=blockheader.version,
            size=block.blocksize,
            in_longest=0,  # `in_longest` set to 0 first and update later
            tx_count=len(block.Txs)
        )

        try:
            prev_block = BlockDb.objects.get(hash=hashStr(blockheader.previousHash))
            block_db.prev_block = prev_block
            block_db.chain_work = prev_block.chain_work + blockheader.blockWork
            block_db.height = prev_block.height + 1
        except BlockDb.DoesNotExist:
            block_db.chain_work = blockheader.blockWork
            block_db.height = 0

        block_db.save()

        for tx in block.Txs:
            self._raw_tx_to_db(tx, block_db)

    def _raw_tx_to_db(self, tx, block_db):
        tx_db = Tx(
            hash=tx.txHash,
            block=block_db,
            version=tx.version,
            locktime=tx.lockTime,
            type=tx.txType,
            size=tx.size,
            time=block_db.time
        )
        tx_db.save()

        for txin in tx.inputs:
            self._raw_txin_to_db(txin, tx_db)
        for i in range(tx.outCount):
            self._raw_txout_to_db(tx.outputs[i], i, tx_db)

    def _raw_txin_to_db(self, txin, tx_db):
        txin_db = TxIn(
            tx=tx_db,
            scriptsig=txin.scriptSig,
            sequence=txin.seqNo
        )
        try:
            prev_tx = Tx.objects.get(hash=hashStr(txin.prevhash))
            txin_db.txout = prev_tx.tx_outs.get(position=txin.txOutId)
        except Tx.DoesNotExist:
            txin_db.txout = None
        except MultipleObjectsReturned:
            block = tx_db.block
            while block:
                try:
                    prev_tx = Tx.objects.get(hash=hashStr(txin.prevhash), block=block)
                    txin_db.txout = prev_tx.tx_outs.get(position=txin.txOutId)
                    break
                except Tx.DoesNotExist:
                    block = block.prev_block
            
        txin_db.save()

    def _raw_txout_to_db(self, txout, position, tx_db):
        TxOut(tx=tx_db,
              value=txout.value,
              position=position,
              scriptpubkey=txout.pubkey,
              address=Address.objects.get_or_create(address=txout.address)[0],
              color=txout.color
              ).save()

    def _get_or_create_datadir(self):
        """
        Get the last created Datadir object from self.blk_dir, or create one if no Datadir exists.
        We get the last created Datadir to make sure we are updating with latest blk file.
        """
        datadir_all = Datadir.objects.filter(dirname=self.blk_dir).order_by('-create_time')

        if datadir_all.count() == 0:
            datadir = Datadir(dirname=self.blk_dir, blkfile_number=0, blkfile_offset=0)
            datadir.save()
            return datadir
        else:
            return datadir_all[0]

    def _get_blk_file_info(self):
        datadir = self._get_or_create_datadir()

        file_name = 'blk{:05d}.dat'.format(datadir.blkfile_number)
        file_path = os.path.join(datadir.dirname, file_name)
        file_offset = datadir.blkfile_offset
        return file_path, file_offset

    def _get_next_blk_file_info(self):
        """Return next blk file path according to the latest Datadir or None if next blk file does not exist."""
        datadir = self._get_or_create_datadir()
        file_name = 'blk{:05d}.dat'.format(datadir.blkfile_number + 1)
        file_path = os.path.join(datadir.dirname, file_name)
        if os.path.exists(file_path):
            Datadir(dirname=self.blk_dir,
                    blkfile_number=(datadir.blkfile_number+1),
                    blkfile_offset=0).save()
            return file_path
        else:
            return None
