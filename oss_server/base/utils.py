def select_utxo(utxos, color, sum):
    """Return a list of utxo with specified color and sum up to the specified amount.

    Args:
        utxos: A list of dict with following format.
                   [{
                       txid: ''
                       color: 0,
                       value: 0,
                       vout: 0
                    },
                    {
                       txid: ''
                       color: 0,
                       value: 0,
                       vout: 0
                    }]
        color: The color to filter.
        sum: The sum of the returned utxos' total value.

    Returns: A list of utxo with value add up to `sum`. If the given utxo can't add up to `sum`, None is returned.
    """
    utxos = [utxo for utxo in utxos if utxo['color'] == color]
    utxos = sorted(utxos, key=lambda utxo: utxo['value'])

    value = 0
    for i, utxo in enumerate(utxos):
        value += utxo['value']
        if value >= sum:
            return utxos[:i+1]
    return None


def balance_from_utxos(utxos):
    """Return balance of a list of utxo.

    Args:
        utxos: A list of utxo with following format.
                   [{
                       txid: ''
                       color: 0,
                       value: 0,
                       vout: 0
                    }]

    Returns: A balance dictionary with color as key and sum of value of that color as dictionary
             value.
    """
    balance_dict = {}
    if utxos:
        for utxo in utxos:
            color = utxo['color']
            value = utxo['value']
            balance_dict[color] = balance_dict.get(color, 0) + value
    return balance_dict
