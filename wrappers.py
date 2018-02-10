# -*- coding: utf-8 -*-

import requests
import requests_cache
import logging
from settings import LOG_FORMAT, LOG_FN_MAIN

logger = logging.getLogger(__name__)

formatter = logging.Formatter(LOG_FORMAT)

file_handler = logging.FileHandler(LOG_FN_MAIN)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


class Coinmarketcap(object):

    __session = None
    __BASE_URL = 'https://api.coinmarketcap.com/v1/'
    __CACHE_FN = 'coins'

    def __init__(self, base_url=__BASE_URL, cache_name=__CACHE_FN):
        self.base_url = base_url
        self.cache_file = cache_name

    def session(self):

        if not self.__session:
            self.__session = requests_cache.core.CachedSession(cache_name=self.cache_file,
                                                               backend='sqlite',
                                                               expire_after=300)
        return self.__session

    def __request(self, endpoint, params):

        try:
            request_raw = self.session().get(self.base_url + endpoint, params=params)
            logger.info("Request to {0} successful.".format(request_raw.url))

            return request_raw.json()
        except Exception:
            logger.exception("Request to {0} with {1} params failed.".format(
                self.base_url + endpoint,
                params)
            )
            return None



    def ticker(self, coin="", **kwargs):

        if coin == None:
            return None
        else:
            coin += "/"
            params = {}
            params.update(kwargs)

            return self.__request('ticker/' + coin, params)

    def market(self, **kwargs):

        params = {}
        params.update(kwargs)

        return self.__request('global/', params)
