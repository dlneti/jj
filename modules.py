# -*- coding: utf-8 -*-
from wrappers import *

logger = logging.getLogger(__name__)
formatter = logging.Formatter(config["log_format"])

file_handler = logging.FileHandler('main.log')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


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
            self.fiat = self.coin.upper() in config["supported_fiat"]
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
            elif row[0] in config["binance_special"].keys():
                row.append(config["binance_special"][row[0]])
                writer.writerow(row)
                bincoins.pop(bincoins.index(config["binance_special"][row[0]]))
            else:
                row.append(0)
                writer.writerow(row)


def thousandify(x):
    """Takes price (float, int or string) as argument and inserts commas to separate thousands"""

    try:
        float(x)
    except ValueError:
        raise ValueError("Requires a number or a string of number")
    else:
        price = str(x)

        #if float, only parse left side of the dot
        if '.' in price:
            pl = [a for a in price.split('.')[0]]
            def parsed(f): return ''.join(f) + price.split('.')[1]
        else:
            pl = [a for a in price]
            def parsed(f): return ''.join(f)[:-1]

        l = float(len(pl))

        if l <= 3:
            return str(x)
        else:
            times = l / 3
            mod_zero = l % times == 0
            if not mod_zero:
                times += 1
            index = [i*-3 for i in range(1, int(times))[::-1]]

            for i in index:
                pl.insert(i, ',')
            pl.append('.')

            pd_l = pl if pl[0] != ',' else pl[1:]

            return parsed(pd_l)


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
        b_price = None if not check.binance else Binance()

        data = {'name': response['name'],
                'rank': response['rank'],
                'symbol': response['symbol'],
                'price_usd': response['price_usd'],
                'price_btc': response['price_btc'],
                'percent_change_24h': response['percent_change_24h'],
                'volume_24_usd': response['24h_volume_usd'],
                'market_cap_usd': response['market_cap_usd'],
                'binance_price': b_price.coin_price(
                    coin=check.binance)['price'] if b_price else None
                }
        return data


def convertToken(token_1, token_2, amount):
    req = Coinmarketcap()

    try:
        fiat_1 = token_1.upper() in config["supported_fiat"]
        fiat_2 = token_2.upper() in config["supported_fiat"]
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
