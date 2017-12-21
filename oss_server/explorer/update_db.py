import logging
import os
from time import sleep

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from django.db import transaction
from django.db import connections

from blocktools.block import Block
from blocktools.blocktools import *

from .models import Address, Datadir, Tx, TxIn, TxOut, Orphan
from .models import Block as BlockDb

logger = logging.getLogger(__name__)
BLK_DIR = settings.BTC_DIR + '/' + BLK_PATH[settings.NET]

# Orpahn block
# { hash_of_parent_block : list_of_orphan_block_object }
orphan_block = {}

def close_old_connections():
    for conn in connections.all():
        conn.close_if_unusable_or_obsolete()

class BlockDbException(Exception):
    """Exception for block db contents."""

class BlockUpdateDaemon(object):

    def __init__(self, sleep_time=1, blk_dir=BLK_DIR, batch_num=50):
        self.blk_dir = blk_dir
        self.batch_num = batch_num
        self.sleep_time = sleep_time
        self.updater = BlockDBUpdater(self.blk_dir, self.batch_num)

    def run_forever(self):
        self._load_orphan_state()
        while True:
            try:
                self.updater.update()
            except Exception as e:
                logger.exception('Error when updater.update(): {}'.format(e))

            close_old_connections()
            sleep(self.sleep_time)

    def _load_orphan_state(self):
        """ To ensure data integrity. """
        for orphan in Orphan.objects.all():
            orphan_list = orphan_block.setdefault(orphan.hash, [])
            try:
                orphan_db = BlockDb.objects.get(hash=orphan.orphan_hash)
                if orphan_db.prev_block or orphan_db.height or orphan_db.chain_work:
                    # Because of atomic. Orphan DB must be updated when BlockDb of orpahan block are updated.
                    logger.error('Error, it must be None.')
                orphan_list.append(orphan_db)
            except Exception as e:
                logger.exception('Error when load orphan state: {}'.format(e))

class BlockDBUpdater(object):

    def __init__(self, blk_dir=BLK_DIR, batch_num=50):
        self.blk_dir = blk_dir
        self.batch_num = batch_num
        self.blocks_hash_cache = []

    def update(self):
        # Read the blk file (possibly from last read position) as many as possible, and check if
        # there's a following blk file to read. If so, continue to parse the file.
        file_path, file_offset = self._get_blk_file_info()
        self._parse_raw_block_to_db(file_path, file_offset)
        self._get_next_blk_file_info()

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
        txout_with_txin = TxOut.objects.filter(tx_in__tx__block__hash__in=self.blocks_hash_cache)
        txout_with_txin.filter(tx_in__tx__block__in_longest=0).update(spent=0)
        txout_with_txin.filter(tx_in__tx__block__in_longest=1).update(spent=1)

    def _parse_raw_block_to_db(self, file_path, file_offset):
        try:
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
        except Exception, e:
            logger.error('Failed to read blk files: ' + file_path)

    def _batch_update_blocks(self, blockchain, block_batch):
        try:
            with transaction.atomic():
                self._store_blocks(blockchain, block_batch)
                self._update_chain_related_info()
        except Exception, e:
            logger.error('Failed to store blocks: ' + str(e) + '\n' +
                         str(blockchain) + '\n' +
                         str(block_batch))

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
        self._store_orphan_state()

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

        prev_hash = hashStr(blockheader.previousHash)
        prev_block_list = BlockDb.objects.filter(hash=prev_hash)

        if len(prev_block_list) > 1:
            logger.error("More than 1 parent block. {}".format(block_db.hash))

        elif len(prev_block_list) == 1 and (prev_block_list[0].prev_block or prev_block_list[0].height == 0):
            prev_block = prev_block_list[0]
            block_db.prev_block = prev_block
            block_db.chain_work = prev_block.chain_work + blockheader.blockWork
            block_db.height = prev_block.height + 1

        else:
            if prev_hash == '0000000000000000000000000000000000000000000000000000000000000000':
                # Genesis block
                block_db.chain_work = blockheader.blockWork
                block_db.height = 0

            else:
                # Orpahn block
                orphan_list = orphan_block.setdefault(prev_hash, [])
                orphan_list.append(block_db)
                logger.info("Orphan!! Miss parent block: {}".format(prev_hash))

        block_db.save()
        logger.info("Block saved: {}".format(block_db.hash))

        if block_db.prev_block:
            # Try to update orphan block
            self._orphan_to_db(block_db)

        for tx in block.Txs:
            self._raw_tx_to_db(tx, block_db)


    # Try to save orphan block.
    def _orphan_to_db(self, parent_db):
        orphan_list = orphan_block.get(parent_db.hash, {})
        for orphan_db in orphan_list:
            try:
                orphan_db.prev_block = parent_db
                orphan_db.height = parent_db.height + 1
                orphan_db.chain_work = parent_db.chain_work + 1
                orphan_db.save()
                logger.info("Orphan block update: {}".format(orphan_db.hash))

                tx_list = Tx.objects.filter(block=orphan_db)
                tx_list.update(valid=1)
                for tx_db in tx_list:
                    TxOut.objects.filter(tx=tx_db).update(valid=1)

                orphan_block[parent_db.hash].remove(orphan_db)
                if not orphan_block[parent_db.hash]:
                    del orphan_block[parent_db.hash]

                # Recursive store orphan to db
                self._orphan_to_db(orphan_db)

            except Exception as e:
                logger.error("Fail to fetch orphan block.")

    def _raw_tx_to_db(self, tx, block_db):
        tx_db = Tx.objects.create(hash=tx.txHash,
                                  block=block_db,
                                  version=tx.version,
                                  locktime=tx.lockTime,
                                  size=tx.size,
                                  time=block_db.time,
                                  valid=1 if block_db.prev_block else 0
                                  )

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
        TxOut.objects.create(tx=tx_db,
                             value=txout.value,
                             position=position,
                             scriptpubkey=txout.pubkey,
                             address=Address.objects.get_or_create(address=txout.address)[0],
                             valid=tx_db.valid
                             )

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
                    blkfile_number=(datadir.blkfile_number + 1),
                    blkfile_offset=0).save()
            return file_path
        else:
            return None

    def _store_orphan_state(self):
        """ To ensure data integrity. """
        # Clean
        Orphan.objects.all().delete()
        # Store
        for parent, orphan_list in orphan_block.iteritems():
            for orphan in orphan_list:
                Orphan.objects.create(hash=parent,
                                      orphan_hash=orphan.hash
                                      )
