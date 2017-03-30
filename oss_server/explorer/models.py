from __future__ import unicode_literals

import binascii
from collections import OrderedDict

from django.db import models

from gcoin import decode_op_return_script


class Address(models.Model):
    address = models.CharField(unique=True, max_length=40)

    def __str__(self):
        return '%s' % self.address


class Block(models.Model):
    hash = models.CharField(unique=True, max_length=64)
    height = models.DecimalField(max_digits=14, decimal_places=0, blank=True, null=True)
    prev_block = models.ForeignKey('self', blank=True, null=True,
                                   related_name='next_blocks', related_query_name='next_block')
    merkle_root = models.CharField(max_length=64, blank=True, null=True)
    time = models.DecimalField(max_digits=20, decimal_places=0, blank=True, null=True)
    bits = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    nonce = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    version = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    in_longest = models.DecimalField(max_digits=1, decimal_places=0, blank=True, null=True)
    size = models.DecimalField(max_digits=14, decimal_places=0, blank=True, null=True)
    chain_work = models.DecimalField(max_digits=20, decimal_places=0, blank=True, null=True)
    tx_count = models.DecimalField(max_digits=10, decimal_places=0)

    class Meta:
        ordering = ['-time']

    def __str__(self):
        return '%s' % self.hash

    @property
    def confirmation(self):
        # orphan
        if not self.in_longest:
            return 0
        # main branch
        else:
            max_height = Block.objects.filter(in_longest=1).count()
            return int(max_height - self.height)

    @property
    def difficulty(self):
        # from bits to difficulty reference: https://en.bitcoin.it/wiki/Difficulty
        difficulty_1_target = 0x00ffff * 2 ** (8 * (0x1d - 3))
        current_target = (int(self.bits) % 0x1000000) * 2 ** (8 * (int(self.bits) / 0xffffff - 3))
        return difficulty_1_target / float(current_target)

    @property
    def branch(self):
        return 'main' if self.in_longest else 'orphan'

    @property
    def prev_block_hash(self):
        return self.prev_block.hash if self.prev_block else None

    @property
    def next_block_hashes(self):
        return [block.hash for block in self.next_blocks.all()]

    @property
    def transaction_hashes(self):
        return [tx.hash for tx in self.txs.all()]

    def as_dict(self):
        return OrderedDict([
            ('hash', self.hash),
            ('height', self.height),
            ('previous_block_hash', self.prev_block_hash),
            ('next_blocks', self.next_block_hashes),
            ('merkle_root', self.merkle_root),
            ('time', self.time),
            ('bits', self.bits),
            ('nonce', self.nonce),
            ('version', self.version),
            ('branch', self.branch),
            ('size', self.size),
            ('chain_work', self.chain_work),
            ('confirmation', self.confirmation),
            ('difficulty', self.difficulty),
            ('transaction_count', self.tx_count),
            ('transaction_hashes', self.transaction_hashes),
        ])


class Datadir(models.Model):
    dirname = models.CharField(max_length=2000)
    blkfile_number = models.IntegerField(blank=True, null=True)
    blkfile_offset = models.IntegerField(blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)


class Tx(models.Model):
    TX_TYPE = {
        0: 'NORMAL',
        1: 'MINT',
        5: 'CONTRACT',
        32: 'VOTE',
        48: 'LICENSE',
        64: 'MINER',
        65: 'DEMINER'
    }

    hash = models.CharField(max_length=64)
    block = models.ForeignKey(Block, related_name='txs', related_query_name='tx')
    version = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    locktime = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    type = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    size = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    time = models.DecimalField(max_digits=20, decimal_places=0, blank=True, null=True, db_index=True)

    def as_dict(self):
        return OrderedDict([
            ('hash', self.hash),
            ('block_hash', self.block.hash),
            ('version', self.version),
            ('locktime', self.locktime),
            ('type', self.TX_TYPE[int(self.type)]),
            ('time', self.time),
            ('confirmation', self.block.confirmation),
            ('vins', [vin.as_dict() for vin in self.tx_ins.all()]),
            ('vouts', [vout.as_dict() for vout in self.tx_outs.all()]),
        ])

    def __str__(self):
        return '%s' % self.hash


class TxOut(models.Model):
    tx = models.ForeignKey(Tx, related_name='tx_outs', related_query_name='tx_out')
    value = models.DecimalField(max_digits=30, decimal_places=0)
    position = models.DecimalField(max_digits=10, decimal_places=0)
    scriptpubkey = models.BinaryField(blank=True, null=True)
    address = models.ForeignKey(Address, related_name='tx_outs', related_query_name='tx_out')
    spent = models.DecimalField(max_digits=1, decimal_places=0, default=0)
    color = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    @property
    def is_op_return(self):
        # check if script has prefix OP_RETURN
        return binascii.hexlify(self.scriptpubkey)[:2] == '6a'

    def as_dict(self):
        return OrderedDict([
            ('n', self.position),
            ('address', self.address.address),
            ('scriptPubKey', binascii.hexlify(self.scriptpubkey)),
            ('color', self.color),
            ('amount', self.value),
        ])

    def utxo_dict(self):
        return OrderedDict([
            ('tx', self.tx.hash),
            ('n', self.position),
            ('color', self.color),
            ('value', self.value)
        ])

    def op_return_dict(self):
        return OrderedDict([
            ('tx', self.tx.hash),
            ('n', self.position),
            ('op_return_data', decode_op_return_script(binascii.hexlify(self.scriptpubkey))),
        ])


class TxIn(models.Model):
    tx = models.ForeignKey(Tx, related_name='tx_ins', related_query_name='tx_in')
    txout = models.ForeignKey(TxOut, related_name='tx_ins', related_query_name='tx_in', blank=True, null=True)
    scriptsig = models.BinaryField(blank=True, null=True)
    sequence = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    def as_dict(self):
        return OrderedDict([
            ('tx_id', self.txout.tx.hash if self.txout else None),
            ('vout', self.txout.position if self.txout else 0),
            ('address', self.txout.address.address if self.txout else None),
            ('color', int(self.txout.color) if self.txout else None),
            ('amount', self.txout.value if self.txout else None),
            ('scriptSig', binascii.hexlify(self.scriptsig) if self.scriptsig else None),
            ('sequence', self.sequence),
        ])
