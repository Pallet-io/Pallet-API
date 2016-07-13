import binascii
import hashlib
import struct

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

def publicKeyDecode(pub):
    pub = pub[2: -2]
    hash1 = hashlib.sha256(binascii.unhexlify(pub))
    hash2 = hashlib.new('ripemd160', hash1.digest())
    padded = (b'\x00') + hash2.digest()
    hash3 = hashlib.sha256(padded)
    hash4 = hashlib.sha256(hash3.digest())
    padded += hash4.digest()[:4]
    return base58.b58encode(padded)
