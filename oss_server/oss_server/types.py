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
        for type in TransactionType.TX_TYPE:
            if TransactionType.TX_TYPE[type] == tx_type_number:
                return type

    @staticmethod
    def toNumber(tx_string):
        return TransactionType.TX_TYPE[tx_string]