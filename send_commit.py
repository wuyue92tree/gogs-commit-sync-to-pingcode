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
import config


class SendCommit(object):
    def __init__(self):
        self.base_url = 'https://open.pingcode.com'
        self.product_name = config.PING_CODE_PRODUCT_NAME
        self.product_server = config.PING_CODE_PRODUCT_SERVER
        self.repo_name = config.PING_CODE_REPO_NAME
        self.repo_full_name = config.PING_CODE_REPO_FULL_NAME
        self.repo_owner_name = config.PING_CODE_REPO_OWNER_NAME
        self.client_id = config.PING_CODE_CLIENT_ID
        self.client_secret = config.PING_CODE_CLIENT_SECRET
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

    def create_repo(self, product_id: str) -> dict:
        url = self.base_url + '/v1/scm/products/' + product_id + '/repositories'
        data = {
            "name": config.PING_CODE_REPO_NAME,
            "full_name": config.PING_CODE_REPO_FULL_NAME,
            "is_fork": eval(config.PING_CODE_REPO_IS_FORK),
            "is_private": eval(config.PING_CODE_REPO_IS_PRIVATE),
            "owner_name": config.PING_CODE_REPO_OWNER_NAME,
            "html_url": config.PING_CODE_REPO_HTML_URL,
            "branches_url": config.PING_CODE_REPO_BRANCHES_URL,
            "commits_url": config.PING_CODE_REPO_COMMITS_URL,
            "pulls_url": config.PING_CODE_REPO_PULLS_URL
        }
        res = requests.post(url, data=json.dumps(data),
                            headers=self.get_headers())
        return res.json()

    def get_repo(self, product_id: str) -> dict:
        url = self.base_url + '/v1/scm/products/' + product_id + '/repositories'
        params = {
            'access_token': self.get_access_token(),
            'full_name': self.repo_full_name
        }
        res = requests.get(url, params=params)
        if len(res.json().get('values')) > 0:
            return res.json().get('values')[0]
        return {}

    def get_repo_id(self, product_id: str) -> str:
        return self.get_repo(product_id).get('id', '')

    def run(self):
        self.auth()
        product_id = self.get_product_id()
        print(product_id)
        self.create_repo(product_id)
        repo_id = self.get_repo_id(product_id)
        print(repo_id)


def main():
    executor = SendCommit()
    executor.run()


if __name__ == '__main__':
    main()
