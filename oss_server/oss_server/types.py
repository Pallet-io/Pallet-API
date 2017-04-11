class TransactionType:
    TX_TYPE = {
        'NORMAL' : 0x00,
        'MINT' : 0x01,
        'CONTRACT' : 0x05,
        'VOTE' : 0x20,
        'LICENSE' : 0x30,
        'MINER' : 0x40,
        'DEMINER' : 0x41
    }

    @staticmethod
    def toType(tx_type_number):
        for k, v in TransactionType.TX_TYPE.iteritems():
            if v == tx_type_number:
                return k

    @staticmethod
    def toNumber(tx_string):
        return TransactionType.TX_TYPE[tx_string]
