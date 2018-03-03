from __future__ import print_function

import argparse
from datetime import datetime
from decimal import Decimal
from math import ceil
import configparser
import getpass
import json
import os

from dateutil.parser import parse
import pytz

from .RobinhoodClient import RobinhoodClient

cache_path = '.robinhood'
if not os.path.exists(cache_path):
  os.makedirs(cache_path)

class RobinhoodCachedClient(RobinhoodClient):
  def __init__(self):
    super(RobinhoodCachedClient, self).__init__()

  def login(self, force_login=False):
    auth_token_path = os.path.join(cache_path, 'auth_token')
    if os.path.exists(auth_token_path) and not force_login:
      with open(auth_token_path, 'r') as auth_token_file:
        self.set_auth_token(auth_token_file.read())
    else:
      # Get a new auth token
      username = input('Username: ')
      password = getpass.getpass()
      auth_token = self.set_auth_token_with_credentials(username, password)
      with open(auth_token_path, 'w') as auth_token_file:
        auth_token_file.write(auth_token)

  def logout(self):
    auth_token_path = os.path.join(cache_path, 'auth_token')
    if os.path.exists(auth_token_path):
      os.remove(auth_token_path)

  def get_account(self, force_cache=True):
    account_path = os.path.join(cache_path, 'account')
    if os.path.exists(account_path):
      with open(account_path, 'r') as account_file:
        return json.load(account_file)
    else:
      account_json = super(RobinhoodCachedClient, self).get_account()
      with open(account_path, 'w') as account_file:
        json.dump(account_json, account_file)
      return account_json
