# -*- coding: utf-8 -*-

import requests
import requests_cache
import hashlib
import logging
import json
import csv
import base64
import hmac
import time
from datetime import datetime

with open('config.json') as f:
    config = json.load(f)

logger = logging.getLogger(__name__)
formatter = logging.Formatter(config["log_format"])

file_handler = logging.FileHandler('main.log')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


def timer(func):
    def wrapper(*args, **kwargs):
        start_t = time.time()
        result = func(*args, **kwargs)
        end_t = time.time() - start_t
        print '{0}() ran in: {1} seconds'.format(
            func.__name__,
            end_t
        )
        return result
    return wrapper

def log_method(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception:
            logger.exception('Something went wrong executing {}'.format(
                func.__name__)
            )
        else:
            logger.debug('{} {} {}'.format(
                func.__name__,
                json.dumps(args[1:]),
                json.dumps(kwargs))
            )
            return result
    return wrapper


class Binance(object):

    url = 'https://api.binance.com/api/'

    @log_method
    def __init__(self, base_url=url):
        self.url = base_url
        self.coin = None
        self.endpoint = None
        self.status_code = None

    @log_method
    def _request(self, endpoint, params):

        try:
            request_raw = requests.request(
                'GET',
                self.url + endpoint,
                params=params
            )
        except Exception:
            logger.exception("Request failed")
        else:
            self.status_code = request_raw.status_code
            logger.debug("Request to {0} successful.".format(
                request_raw.url)
            )
            return request_raw

    @log_method
    def exchange_info(self):
        self.endpoint = "v1/exchaneInfo"
        params = {}

        data = self._request(self.endpoint, params)

        return data.json()

    @log_method
    def coin_price(self, coin=""):

        self.endpoint = 'v3/ticker/price'
        params = {}

        if coin == None:
            return None
        elif coin == "":
            pass
        else:
            symbol = "BTCUSDT" if coin.upper(
                ) == "BTC" else coin.upper() + "BTC"
            params.update({"symbol": symbol})

        data = self._request(self.endpoint, params)

        return data.json()

    @log_method
    def make_coin_file(self, data=None):

        if not data:
            data = self.get_coin_data()

        with open('bincoins.csv', 'w') as f:
            writer = csv.writer(f)
            for i in data:
                writer.writerow([i])

    @log_method
    def check_list(self):
        coins_now = self.get_coin_data()
        with open('bincoins.csv') as f:
            coins_prev = [row[0] for row in csv.reader(f)]

        if coins_prev == coins_now:
            return False
        else:
            self.make_coin_file(data=coins_now)
            new = list(set(coins_now) - set(coins_prev))
            logger.info("'{0}' += {1}".format(
                'bincoins.csv', new)
            )
            return new

    @log_method
    def get_coin_data(self):
        data = self.coin_price()
        coins = ['BTC']

        for item in data:
            if ('USDT' in item['symbol']) or (
                    'BTC' not in item['symbol']) or (
                        not item):
                pass
            else:
                coins.append(item['symbol'][:-3].upper())

        coins.sort()
        return coins

    @staticmethod
    @log_method
    def check_coin(coin):
        """Check if coin is in list of binance coins"""

        with open('bincoins.csv') as f:
            return True if coin.upper(
                ) in [row[0]for row in csv.reader(
                    f)] else False


class Coinmarketcap(object):

    __session = None
    __BASE_URL = 'https://api.coinmarketcap.com/v1/'
    __CACHE_FN = 'coins'

    @log_method
    def __init__(self, base_url=__BASE_URL, cache_name=__CACHE_FN):
        self.base_url = base_url
        self.cache_file = cache_name

    @log_method
    def session(self):

        if not self.__session:
            self.__session = requests_cache.core.CachedSession(
                cache_name=self.cache_file,
                backend='sqlite',
                expire_after=300
            )
        return self.__session

    @log_method
    def __request(self, endpoint, params):

        try:
            request_raw = self.session().get(
                self.base_url + endpoint, params=params)
            logger.debug("Request to {0} successful".format(request_raw.url))

            return request_raw.json()
        except Exception:
            logger.exception("Request to {0} with {1} params failed".format(
                self.base_url + endpoint,
                params)
            )
            return None

    @log_method
    def ticker(self, coin="", **kwargs):

        if coin == None:
            return None
        elif coin == "":
            pass
        else:
            coin += "/"

        params = {}
        params.update(kwargs)

        return self.__request('ticker/' + coin, params)

    @log_method
    def market(self, **kwargs):

        params = {}
        params.update(kwargs)

        return self.__request('global/', params)


class Ico:

    auth = config["ico_b"]
    _session = None
    _BASE_URL = auth["base_url"]
    _CACHE_FN = auth["cache_file"]

    @log_method
    def __init__(self,
                 pub_key=auth["pub_key"],
                 pr_key=auth["pr_key"],
                 base_url=_BASE_URL,
                 cache_name=_CACHE_FN
                 ):
        self.pub_key = str(pub_key)
        self.pr_key = str(pr_key)
        self.base_url = base_url
        self.cache_file = cache_name
        self.params = {}


    @log_method
    def session(self):
        if not self._session:
            self._session = requests_cache.core.CachedSession(
                cache_name=self.cache_file,
                backend='sqlite',
                expire_after=3600
            )

        return self._session


    @log_method
    def _request(self, endpoint):
        headers = self._sign_req(
            json.dumps(self.params))

        try:
            request_raw = self.session().post(
                self.base_url + endpoint,
                headers=headers,
                json=self.params
            )
            logger.debug("Request to {0} successful".format(
                request_raw.url)
            )
        except Exception:
            logger.exception("Request failed")
        else:
            return request_raw.json()


    @log_method
    def _sign_req(self, params):
        sig = hmac.new(
            self.pr_key,
            params,
            digestmod=hashlib.sha384
        )

        headers = {'X-ICObench-Key': self.pub_key}
        headers.update(
            {'X-ICObench-Sig': base64.b64encode(
                sig.digest()).strip()}
        )

        return headers


    @log_method
    def all(self, **kwargs):
        endpoint = "icos/all"
        self.params.update(kwargs)

        return self._request(endpoint)


    @log_method
    def trending(self):
        endpoint = "icos/trending"

        return self._request(endpoint)


    @log_method
    def detail(self, coin_id):
        endpoint = "/ico/{}".format(coin_id)

        return self._request(endpoint)


    @log_method
    def people(self, mode='all', **kwargs):
        if mode not in modes:
            return None
        else:
            endpoint = 'people/' + mode
            self.params.update(kwargs)

            return self._request(endpoint)

    @log_method
    def stats(self):
        endpoint = "other/stats"

        return self._request(endpoint)
