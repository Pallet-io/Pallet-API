import binascii
import hashlib
import struct
import re

from django.conf import settings

import base58
from gcoin import ripemd

pubkey_hash_re = re.compile(r'^76a914[a-f0-9]{40}88ac$')
pubkey_re = re.compile(r'^21[a-f0-9]{66}ac$')
script_hash_re = re.compile(r'^a914[a-f0-9]{40}87$')

BLK_PATH = {
    'MAINNET': 'blocks',
    'TESTNET': 'testnet3/blocks'
}

MAGIC_NUMBER = {
    'MAINNET': 3652501241,      #0xD9B4BEF9
    'TESTNET': 118034699        #0x0709110B
}

P2PKH_ADDRESS_PREFIX = {
    'MAINNET': b'\x00',
    'TESTNET': b'\x6F'
}

P2SH_ADDRESS_PREFIX = {
    'MAINNET': b'\x05',
    'MAINNET': b'\xC4'
}

def uint1(stream):
    return ord(stream.read(1))


def uint2(stream):
    return struct.unpack('H', stream.read(2))[0]


def uint4(stream):
    return struct.unpack('I', stream.read(4))[0]


def uint8(stream):
    return struct.unpack('Q', stream.read(8))[0]


def hash32(stream):
    return stream.read(32)[::-1]


def time(stream):
    return uint4(stream)


def varint(stream):
    size = uint1(stream)

    if size < 0xfd:
        return size
    if size == 0xfd:
        return uint2(stream)
    if size == 0xfe:
        return uint4(stream)
    if size == 0xff:
        return uint8(stream)

    return -1


def hashStr(bytebuffer):
    return ''.join(('%02x'%ord(a)) for a in bytebuffer)


def hashStrLE(bytebuffer):
    return ''.join([('%02x'%ord(a)) for a in bytebuffer][::-1])


def intLE(num):
    return struct.pack("<i", (num) % 2**32).encode('hex')


def addressFromScriptPubKey(script_pub_key):
    script_pub_key = script_pub_key.lower()
    version_prefix = P2PKH_ADDRESS_PREFIX[settings.NET]
    # pay to pubkey hash
    if pubkey_hash_re.match(script_pub_key):
        pubkey_hash = binascii.unhexlify(script_pub_key[6:-4])
    # pay to pubkey
    elif pubkey_re.match(script_pub_key):
        hash1 = hashlib.sha256(binascii.unhexlify(script_pub_key[2:-2]))
        pubkey_hash = ripemd.RIPEMD160(hash1.digest()).digest()
    # pay to script hash
    elif script_hash_re.match(script_pub_key):
        pubkey_hash = binascii.unhexlify(script_pub_key[4:-2])
        version_prefix = P2SH_ADDRESS_PREFIX[settings.NET]
    else:
        return ''

    padded = version_prefix + pubkey_hash
    hash2 = hashlib.sha256(padded)
    hash3 = hashlib.sha256(hash2.digest())
    padded += hash3.digest()[:4]
    return base58.b58encode(padded)
