import hashlib

from blocktools import *
from gcoin.transaction import serialize


class BlockHeader:

    def __init__(self, blockchain):
        self.version = uint4(blockchain)
        self.previousHash = hash32(blockchain)
        self.merkleHash = hash32(blockchain)
        self.time = uint4(blockchain)
        self.bits = uint4(blockchain)
        self.nonce = uint4(blockchain)

    @property
    def difficulty(self):
        nShift = int((self.bits >> 24) & 0xFF)
        dDiff = float(0x0000FFFF) / (self.bits & 0x00FFFFFF)
        while nShift < 29:
            dDiff *= 256
            nShift += 1
        while nShift > 29:
            dDiff /= 256
            nShift -= 1
        return dDiff

    @property
    def blockHash(self):
        headerHex = (intLE(self.version) + hashStrLE(self.previousHash) + hashStrLE(self.merkleHash)
                      + intLE(self.time) + intLE(self.bits) + intLE(self.nonce))
        headerBin = headerHex.decode('hex')
        hash_ = hashlib.sha256(hashlib.sha256(headerBin).digest()).digest()
        return hash_[::-1].encode('hex_codec')

    @property
    def blockWork(self):
        lastSixBits = self.bits & 0x00FFFFFF
        firstTwoBits = (self.bits >> 24) & 0xFF
        target = lastSixBits * 2**(8 * (firstTwoBits - 3))
        return 2**256 / (target + 1)

    def toString(self):
        print "Version:\t %d" % self.version
        print "Previous Hash\t %s" % hashStr(self.previousHash)
        print "Merkle Root\t %s" % hashStr(self.merkleHash)
        print "Time\t\t %d" % self.time
        print "Bits\t\t %8x" % self.bits
        print "Difficulty\t %.8f" % self.difficulty
        print "Nonce\t\t %s" % self.nonce
        print "Hash\t\t %s" % self.blockHash
        print "Work\t\t %x" % self.blockWork


class Block:

    def __init__(self, blockchain):
        self.continueParsing = True
        self.magicNum = 0
        self.blocksize = 0
        self.blockHeader = ''
        self.txCount = 0
        self.Txs = []
        self.scriptSig = ''

        if self.hasLength(blockchain, 8):
            self.magicNum = uint4(blockchain)
            self.blocksize = uint4(blockchain)
        else:
            self.continueParsing = False
            return

        if self.blocksize > 0 and self.hasLength(blockchain, self.blocksize):
            self.setHeader(blockchain)
            self.txCount = varint(blockchain)
            self.Txs = []

            for i in range(0, self.txCount):
                tx = Tx(blockchain)
                self.Txs.append(tx)

            self.scriptLen = varint(blockchain)
            self.scriptSig = blockchain.read(self.scriptLen)
        else:
            self.continueParsing = False

    def continueParsing(self):
        return self.continueParsing

    def getBlocksize(self):
        return self.blocksize

    def hasLength(self, blockchain, size):
        curPos = blockchain.tell()
        blockchain.seek(0, 2)

        fileSize = blockchain.tell()
        blockchain.seek(curPos)

        tempBlockSize = fileSize - curPos
        
        if tempBlockSize < size:
            return False
        return True

    def setHeader(self, blockchain):
        self.blockHeader = BlockHeader(blockchain)

    def toString(self):
        print ""
        print "Magic No: \t%8x" % self.magicNum
        print "Blocksize: \t", self.blocksize
        print ""
        print "#" * 10 + " Block Header " + "#" * 10
        self.blockHeader.toString()
        print
        print "Script Sig: \t %s" % hashStr(self.scriptSig)
        print "##### Tx Count: %d" % self.txCount
        for t in self.Txs:
            t.toString()


class Tx:

    def __init__(self, blockchain):
        txStart = blockchain.tell()
        self.version = uint4(blockchain)
        self.inCount = varint(blockchain)
        self.inputs = []
        for i in range(0, self.inCount):
            input = txInput(blockchain)
            self.inputs.append(input)
        self.outCount = varint(blockchain)
        self.outputs = []
        if self.outCount > 0:
            for i in range(0, self.outCount):
                output = txOutput(blockchain)
                self.outputs.append(output)
        self.lockTime = uint4(blockchain)
        self.txType = uint4(blockchain)
        self.size = blockchain.tell() - txStart

    @property
    def txHex(self):
        return serialize(self.toDict())

    @property
    def txHash(self):
        headerBin = self.txHex.decode('hex')
        hash_ = hashlib.sha256(hashlib.sha256(headerBin).digest()).digest()
        return hash_[::-1].encode('hex_codec')

    def toString(self):
        print ""
        print "=" * 10 + " New Transaction " + "=" * 10
        print "TX Hex:\t %s" % self.txHex
        print "TX Hash:\t %s" % self.txHash
        print "Tx Version:\t %d" % self.version
        print "Inputs:\t\t %d" % self.inCount
        for i in self.inputs:
            i.toString()

        print "Outputs:\t %d" % self.outCount
        for o in self.outputs:
            o.toString()
        print "Lock Time:\t %d" % self.lockTime
        print "TX TYPE:\t %d" % self.txType
        print "TX Size:\t %d" % self.size

    def toDict(self):
        txDict = {
            'locktime': self.lockTime, 'version': self.version,
            'ins': [], 'outs': [], 'type': self.txType
        }

        for txin in self.inputs:
            txDict['ins'].append(txin.toDict())

        for txout in self.outputs:
            txDict['outs'].append(txout.toDict())
        return txDict


class txInput:

    def __init__(self, blockchain):
        self.prevhash = hash32(blockchain)
        self.txOutId = uint4(blockchain)
        self.scriptLen = varint(blockchain)
        self.scriptSig = blockchain.read(self.scriptLen)
        self.seqNo = uint4(blockchain)

    def toString(self):
        print "--------------TX IN------------------------"
        print "Tx Previous Hash:\t %s" % hashStr(self.prevhash)
        print "Tx Out Index:\t %8x" % self.txOutId
        print "Script Length:\t %d" % self.scriptLen
        print "Script Sig:\t %s" % hashStr(self.scriptSig)
        print "Sequence:\t %8x" % self.seqNo
        print "--------------------------------------------"

    def toDict(self):
        dict_ = {
            'outpoint': {
                'hash': hashStr(self.prevhash),
                'index': self.txOutId
            },
            'script': hashStr(self.scriptSig),
            'sequence': self.seqNo
        }
        return dict_


class txOutput:

    def __init__(self, blockchain):
        self.value = uint8(blockchain)
        self.scriptLen = varint(blockchain)
        self.pubkey = blockchain.read(self.scriptLen)
        self.color = uint4(blockchain)

    @property
    def address(self):
        return pubkeyToAddress(hashStr(self.pubkey))

    def toString(self):
        print "--------------TX OUT------------------------"
        print "Value:\t\t %d" % self.value
        print "Script Len:\t %d" % self.scriptLen
        print "Pubkey:\t\t %s" % hashStr(self.pubkey)
        print "Color:\t\t %d" % self.color
        print "Addr:\t\t %s" % self.address
        print "---------------------------------------------"

    def toDict(self):
        dict_ = {
            'script': hashStr(self.pubkey),
            'value': self.value,
            'color': self.color
        }
        return dict_
