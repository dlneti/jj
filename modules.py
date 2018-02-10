# -*- coding: utf-8 -*-
import requests
import csv
from wrappers import Coinmarketcap
from settings import *


class CheckCoin(object):

    __FILENAME = 'coin_id.csv'
    __found = None

    def __init__(self, coin, data_file=__FILENAME):
        self.coin = str(coin)
        self.data_file = data_file


        with open(self.data_file, 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                if self.coin.lower() in row:
                    self.symbol = str(row[0]).upper()
                    self.name = str(row[1])
                    self.coin_id = str(row[2])
                    self.binance = None if row[3] == '0' else str(row[3])
                    self.__found = True

        if not self.__found:
            self.fiat = self.coin.upper() in SUPPORTED_FIAT
            self.symbol = None
            self.name = self.coin.upper() if self.fiat else None
            self.coin_id = None


def getCmc():
    req = Coinmarketcap()
    response = req.ticker(limit=0)
    row_data = [[item['symbol'].lower(),
                item['name'],
                item['id'].lower()] for item in response]
    same = []

    with open('bincoins.csv', 'r') as f:
        reader = csv.reader(f)
        bincoins = [row[0].lower() for row in reader]

    for row in row_data:
        if row[0] in bincoins:
            same.append(row[0])
            bincoins.pop(bincoins.index(row[0]))
    bincoins.append('bcc')

    with open('coin_id.csv', 'w') as f:
        writer = csv.writer(f)
        # writer.writerow(['Symbol', 'Name', 'ID', Binance Symbol])

        for row in row_data:
            if row[0] in same:
                row.append(row[0])
                writer.writerow(row)
            elif row[0] in BINANCE_SPECIAL.keys():
                row.append(BINANCE_SPECIAL[row[0]])
                writer.writerow(row)
                bincoins.pop(bincoins.index(BINANCE_SPECIAL[row[0]]))
            else:
                row.append(0)
                writer.writerow(row)


def parsePrice(x):
    """Takes price (float, int or string) as argument and inserts commas to separate thousands"""

    price = str(x)

    if '.' not in price:
        if price is None:
            return 'n/a'
        else:
            parseList = [a for a in price]
            l = len(parseList)

        def parsed(f): return ''.join(f)[:-1]

    else:
        if price is None:
            return 'n/a'
        else:
            parseList = [a for a in price.split('.')[0]]
            l = len(parseList)

        def parsed(f): return ''.join(f) + price.split('.')[1]

    if l <= 3:
        return str(x)
    elif l > 3 and l <= 6:
        parseList.insert(-3, ',')
        parseList.append('.')
        return parsed(parseList)
    elif l > 6 and l <= 9:
        parseList.insert(-6, ',')
        parseList.insert(-3, ',')
        parseList.append('.')
        return parsed(parseList)
    elif l > 9 and l <= 12:
        parseList.insert(-9, ',')
        parseList.insert(-6, ',')
        parseList.insert(-3, ',')
        parseList.append('.')
        return parsed(parseList)
    elif l > 12 and l <= 15:
        parseList.insert(-12, ',')
        parseList.insert(-9, ',')
        parseList.insert(-6, ',')
        parseList.insert(-3, ',')
        parseList.append('.')
        return parsed(parseList)
    elif l > 15 and l <= 18:
        parseList.insert(-15, ',')
        parseList.insert(-12, ',')
        parseList.insert(-9, ',')
        parseList.insert(-6, ',')
        parseList.insert(-3, ',')
        parseList.append('.')
        return parsed(parseList)


def getBinCoinPrice(coin):
    url = "https://api.binance.com/api/v3/ticker/price"

    if coin.upper() == "BTC":
        params = {"symbol": "BTCUSDT"}
    else:
        params = {"symbol": coin.upper() + "BTC"}

    data = requests.request('GET', url, params=params).json()

    try:
        return data['price']
    except KeyError:
        return None


def getCoinPrice(coin):
    check = CheckCoin(coin)

    if not check.coin_id:
        return None
    else:
        req = Coinmarketcap()
        response = req.ticker(coin=check.coin_id)[0]

        data = {'name': response['name'],
                'rank': response['rank'],
                'symbol': response['symbol'],
                'price_usd': response['price_usd'],
                'price_btc': response['price_btc'],
                'percent_change_24h': response['percent_change_24h'],
                'volume_24_usd': response['24h_volume_usd'],
                'market_cap_usd': response['market_cap_usd'],
                'binance_price': None if not check.binance else getBinCoinPrice(
                    check.binance)
                }
        return data


def convertToken(token_1, token_2, amount):
    req = Coinmarketcap()

    try:
        fiat_1 = token_1.upper() in SUPPORTED_FIAT
        fiat_2 = token_2.upper() in SUPPORTED_FIAT
    except AttributeError:
        return None

    try:
        if fiat_1 or fiat_2:
            if not fiat_1:      # convert crypto to fiat
                if token_2.upper() == 'USD':
                    response = req.ticker(token_1)
                else:
                    response = req.ticker(token_1, convert=token_2.upper())
                fiat_val = response[0]['price_{}'.format(token_2.lower())]

                return str(round(float(amount) * float(fiat_val), 2))
            else:       # convert fiat to crypto
                if token_1.upper() == 'USD':
                    response = req.ticker(token_2)
                else:
                    response = req.ticker(token_2, convert=token_1.upper())
                fiat_val = response[0]['price_{}'.format(token_1.lower())]

                return str(round(float(amount) / float(fiat_val), 6))
        else:
            to_convert = req.ticker(token_1)[0]['price_usd']
            against = req.ticker(token_2)[0]['price_usd']
            usd_val = round(float(to_convert) * float(amount), 2)
            convert = round(usd_val / float(against), 6)

            return str(convert), str(usd_val)

    except KeyError, TypeError:
        return None


def checkDigit(x):
    check = x.replace(',', '.') if ',' in x else x
    try:
        float(check)
        return str(check)
    except ValueError:
        return None
