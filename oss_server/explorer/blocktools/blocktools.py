import binascii
import hashlib
import struct
import re

import base58

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
    time = uint4(stream)
    return time

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

def pubkeyToAddress(pubkey):
    pubkey = pubkey.lower()
    # pay to pubkey hash
    if re.match(r'^76a914[a-f0-9]{40}88ac$', pubkey):
        pubkey = pubkey[6:-4]
        pubkeyHash = binascii.unhexlify(pubkey)
    # pay to pubkey
    elif re.match(r'^21[a-f0-9]{66}ac$', pubkey):
        pubkey = pubkey[2:-2]
        hash1 = hashlib.sha256(binascii.unhexlify(pubkey))
        pubkeyHash = hashlib.new('ripemd160', hash1.digest()).digest()
    else:
        return ''

    padded = (b'\x00') + pubkeyHash
    hash2 = hashlib.sha256(padded)
    hash3 = hashlib.sha256(hash2.digest())
    padded += hash3.digest()[:4]
    return base58.b58encode(padded)
