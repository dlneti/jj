# -*- coding: utf-8 -*-

import requests
import requests_cache


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
        except Exception as e:
            return e

        return request_raw.json()

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
