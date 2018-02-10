from urllib2 import urlopen as uo  ### ToDo:  SWITCH TO REQUEST MODULE
import json
import csv
import logging
from settings import BASE_URL_BNC, LOG_FORMAT

logging.basicConfig(filename='binance.log',
                    level=logging.INFO,
                    format=LOG_FORMAT)
logger = logging.getLogger()

base_url = BASE_URL_BNC + 'ticker/allPrices'
FILENAME = 'bincoins.csv'


def getResponse():
    """Returns a dictionary of coins from Binance"""

    request = uo(base_url)
    data = json.load(request)
    request.close()

    return data


def getCoinList():
    """Make a csv file with real-time coins from Binance"""

    coins = []

    for item in getResponse():
        if ('USDT' or '123456') in item['symbol']:
            pass
        elif 'BTC' not in item['symbol']:
            pass
        else:
            coins.append(item['symbol'])

    coins.sort()

    with open(FILENAME, 'w') as f:
        writer = csv.writer(f)
        for coin in coins:
            writer.writerow([coin[:-3]])

    logger.info('New "{}" has been created.'.format(FILENAME))



def checkList():
    """
        Checks real-time data against list in database
        Returns list of new entries.
    """

    ## Check if file exists, if not, create it
    while True:
        try:
            f = open(FILENAME)
            break
        except IOError:
            logger.info('File does not exit. Creating new file')
            getCoinList()


    reader = csv.reader(f)
    coins_prev = [row[0] for row in reader]     # Load data from stored list
    f.close()

    coins_now = []

    ## Get real-time data from Binance
    for item in getResponse():
        if ('USDT' or '123456') in item['symbol']:
            pass
        elif 'BTC' not in item['symbol']:
            pass
        else:
            coins_now.append(item['symbol'][:-3])

    coins_now.sort()


    coin_delta = list(set(coins_now) - set(coins_prev))

    if len(coin_delta) == 0:
        return None
    else:       # Rewrite the old file with new list containing any new entries
        with open(FILENAME, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['BTC'])
            for coin in coins_now:
                writer.writerow([coin])

            logger.info("{} has been added to \"{}\"".format(
                coin_delta, FILENAME))

        return coin_delta
