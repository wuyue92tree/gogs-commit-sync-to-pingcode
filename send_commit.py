#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: IntelliJ IDEA
@file: send_commit.py
@create at: 2022-09-11 20:09
"""
import json
import os
import requests
import tempfile


class SendCommit(object):
    def __init__(self):
        self.base_url = 'https://open.pingcode.com'
        self.product_name = os.environ['PING_CODE_PRODUCT_NAME']
        self.client_id = os.environ['PING_CODE_CLIENT_ID']
        self.client_secret = os.environ['PING_CODE_CLIENT_SECRET']
        self.cache_file = os.path.join(tempfile.gettempdir(),
                                       f'ping_code_{self.product_name}_cache')

    def auth(self):
        """ 确保access_token有效 """
        if self.ping():
            return
        url = self.base_url + '/v1/auth/token'
        params = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        res = requests.get(url, params=params)
        if res.status_code == 200:
            cache = self.get_cache()
            cache['access_token'] = res.json().get('access_token')
            self.save_cache(cache)
        else:
            raise Exception(f"auth failed, {res.text}")

    def get_cache(self) -> dict:
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.loads(f.read())
        return {}

    def save_cache(self, cache: dict):
        with open(self.cache_file, 'w') as f:
            f.write(json.dumps(cache))

    def get_access_token(self):
        return self.get_cache().get('access_token', 'invalid')

    def ping(self) -> bool:
        url = self.base_url + '/v1/auth/ping'
        params = {
            'access_token': self.get_access_token()
        }
        res = requests.get(url, params=params)
        if res.status_code == 401:
            return False
        return True

    def get_headers(self) -> dict:
        return {'Content-Type': 'application/json',
                'authorization': 'Bearer ' + self.get_access_token()}

    def create_product(self) -> dict:
        url = self.base_url + '/v1/scm/products'
        data = {
            "name": self.product_name,
            "type": "gogs"
        }
        res = requests.post(url, data=json.dumps(data),
                            headers=self.get_headers())
        return res.json()

    def get_product(self) -> dict:
        url = self.base_url + '/v1/scm/products'
        params = {
            'access_token': self.get_access_token(),
            'name': self.product_name
        }
        res = requests.get(url, params=params)
        if len(res.json().get('values')) > 0:
            return res.json().get('values')[0]
        return {}

    def get_product_id(self) -> str:
        return self.get_product().get('id', '')

    def run(self):
        self.auth()
        print(self.get_product_id())


def main():
    executor = SendCommit()
    executor.run()


if __name__ == '__main__':
    main()
