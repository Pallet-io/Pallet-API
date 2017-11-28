def select_utxo(utxos, sum):
    """Return a list of utxo sum up to the specified amount.

    Args:
        utxos: A list of dict with following format.
                   [{
                       txid: ''
                       value: 0,
                       vout: 0,
                       scriptPubKey: '',
                    },
                    {
                       txid: ''
                       value: 0,
                       vout: 0,
                       scriptPubKey: '',
                    }]
        sum: The sum of the returned utxos' total value.

    Returns: A list of utxo with value add up to `sum`. If the given utxo can't add up to `sum`,
             an empty list is returned. This function returns as many utxo as possible, that is,
             utxo with small value will get picked first.
    """
    if not utxos:
        return []

    utxos = sorted(utxos, key=lambda utxo: utxo['value'])

    value = 0
    for i, utxo in enumerate(utxos):
        value += utxo['value']
        if value >= sum:
            return utxos[:i + 1]
    return []


def balance_from_utxos(utxos):
    """Return balance of a list of utxo.

    Args:
        utxos: A list of utxo with following format.
                   [{
                       txid: ''
                       value: 0,
                       vout: 0,
                       scriptPubKey: '',
                    }]

    Returns: A balance sum of value
             value.
    """
    balance = 0
    if utxos:
        balance = sum(utxo['value'] for utxo in utxos)
    return balance


def utxo_to_txin(utxo):
    """Return a dict of transaction input build from an utxo.

    Args:
    utxo: an utxo dict.
    {
      txid: ''
      value: 0,
      vout: 0,
      scriptPubKey: ''
    }
    """

    return {
        'tx_id': utxo['txid'],
        'index': utxo['vout'],
        'script': utxo['scriptPubKey']
    }
