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
import re
import sys
import requests
import tempfile

# auth
PING_CODE_CLIENT_ID = os.environ['PING_CODE_CLIENT_ID']
PING_CODE_CLIENT_SECRET = os.environ['PING_CODE_CLIENT_SECRET']

# product
PING_CODE_PRODUCT_NAME = os.environ['PING_CODE_PRODUCT_NAME']
PING_CODE_PRODUCT_SERVER = os.environ['PING_CODE_PRODUCT_SERVER']

# repo
PING_CODE_REPO_NAME = os.environ['PING_CODE_REPO_NAME']
PING_CODE_REPO_FULL_NAME = os.environ['PING_CODE_REPO_FULL_NAME']
PING_CODE_REPO_OWNER_NAME = os.environ['PING_CODE_REPO_OWNER_NAME']
PING_CODE_REPO_IS_FORK = os.environ['PING_CODE_REPO_IS_FORK']
PING_CODE_REPO_IS_PRIVATE = os.environ['PING_CODE_REPO_IS_PRIVATE']
PING_CODE_REPO_HTML_URL = f'{PING_CODE_PRODUCT_SERVER}/{PING_CODE_REPO_FULL_NAME}'
PING_CODE_REPO_BRANCHES_URL = f'{PING_CODE_REPO_HTML_URL}/src/' + '{branch}'
PING_CODE_REPO_COMMITS_URL = f'{PING_CODE_REPO_HTML_URL}/commit/' + '{sha}'
PING_CODE_REPO_PULLS_URL = f'{PING_CODE_REPO_HTML_URL}/pulls/' + '{number}'

REPO_PATH = os.environ['REPO_PATH']


class SendCommit(object):
    def __init__(self):
        self.base_url = 'https://open.pingcode.com'
        self.product_name = PING_CODE_PRODUCT_NAME
        self.product_server = PING_CODE_PRODUCT_SERVER
        self.repo_name = PING_CODE_REPO_NAME
        self.repo_full_name = PING_CODE_REPO_FULL_NAME
        self.repo_owner_name = PING_CODE_REPO_OWNER_NAME
        self.client_id = PING_CODE_CLIENT_ID
        self.client_secret = PING_CODE_CLIENT_SECRET
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
            "name": PING_CODE_REPO_NAME,
            "full_name": PING_CODE_REPO_FULL_NAME,
            "is_fork": eval(PING_CODE_REPO_IS_FORK),
            "is_private": eval(PING_CODE_REPO_IS_PRIVATE),
            "owner_name": PING_CODE_REPO_OWNER_NAME,
            "html_url": PING_CODE_REPO_HTML_URL,
            "branches_url": PING_CODE_REPO_BRANCHES_URL,
            "commits_url": PING_CODE_REPO_COMMITS_URL,
            "pulls_url": PING_CODE_REPO_PULLS_URL
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

    def create_branch(self, product_id: str, repo_id: str, branch_name: str):
        url = self.base_url + '/v1/scm/products/' \
              + product_id + '/repositories/' + repo_id + '/branches'
        data = {
            'name': branch_name,
            'sender_name': 'system',
            'work_item_identifiers': self.resolve_identifiers(branch_name)
        }
        res = requests.post(url, data=json.dumps(data),
                            headers=self.get_headers())
        return res.json()

    def get_branch(self, product_id: str, repo_id: str, branch_name: str):
        url = self.base_url + '/v1/scm/products/' \
              + product_id + '/repositories/' + repo_id + '/branches'
        params = {
            'access_token': self.get_access_token(),
            'product_id': product_id,
            'repository_id': repo_id,
            'name': branch_name
        }
        res = requests.get(url, params=params)
        if len(res.json().get('values')) > 0:
            return res.json().get('values')[0]
        return {}

    def get_branch_id(self, product_id: str, repo_id: str, branch_name: str):
        return self.get_branch(product_id, repo_id, branch_name).get('id', '')

    def create_commits(self, commit: dict) -> dict:
        url = self.base_url + '/v1/scm/commits'
        res = requests.post(url, data=json.dumps(commit),
                            headers=self.get_headers())
        return res.json()

    def create_refs(self, product_id: str, repo_id: str, branch_id: str,
                    commit_sha: str):
        url = self.base_url + \
              f'/v1/scm/products/{product_id}/repositories/{repo_id}/refs'
        data = {
            "sha": commit_sha,
            "meta_type": "branch",
            "meta_id": branch_id
        }
        res = requests.post(url, data=json.dumps(data),
                            headers=self.get_headers())
        return res.json()

    def forward_commits(self, product_id: str, repo_id: str, branch_id: str):
        commits = self.get_commits()
        for commit in commits:
            try:
                self.create_commits(commit)
                self.create_refs(product_id, repo_id, branch_id, commit['sha'])
            except Exception as e:
                print(e)

    @staticmethod
    def resolve_identifiers(string: str) -> list:
        matches = re.findall('#[a-zA-Z0-9]+-[0-9]+', string, re.M)
        identifiers = []
        for match in matches:
            identifiers.append(match[1:])
        return identifiers

    @staticmethod
    def get_branch_name() -> str:
        refs = sys.argv[1].split('/')
        if refs[0] == 'refs' and refs[1] == 'heads':
            return '/'.join(refs[2:])
        else:
            return ''

    def get_commits(self):
        if sys.argv[2] == '0000000000000000000000000000000000000000':
            return []
        else:
            cmd = 'git log --pretty=format:"%H+++++%T+++++%cn+++++%at+++++%s" ' + \
                  sys.argv[2] + '..' + sys.argv[3]
            output = os.popen(cmd).read()
            infos = output.split('\n')
            commits = []
            for info in infos:
                commit = info.split('+++++')
                commits.append(
                    {'sha': commit[0], 'tree_id': commit[1],
                     'committer_name': commit[2],
                     'committed_at': int(commit[3]),
                     'message': commit[4],
                     'work_item_identifiers': self.resolve_identifiers(
                         commit[4]), 'files_added': [],
                     'files_removed': [], 'files_modified': []})
            return commits

    def run(self):
        branch_name = self.get_branch_name()
        if branch_name != '':
            self.auth()
            product_id = self.get_product_id()
            print(product_id)
            self.create_repo(product_id)
            repo_id = self.get_repo_id(product_id)
            print(repo_id)
            self.create_branch(product_id, repo_id, branch_name)
            branch_id = self.get_branch_id(product_id, repo_id, branch_name)
            print(branch_id)
            self.forward_commits(product_id, repo_id, branch_id)


def main():
    # sys.argv $ref $oldrev $newrev
    os.chdir(REPO_PATH)
    executor = SendCommit()
    executor.run()


if __name__ == '__main__':
    main()
