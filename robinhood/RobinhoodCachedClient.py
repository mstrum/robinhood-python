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

cache_root_path = '.robinhood'
if not os.path.exists(cache_root_path):
  os.makedirs(cache_root_path)

class RobinhoodCachedClient(RobinhoodClient):
  def __init__(self):
    super(RobinhoodCachedClient, self).__init__()

  def login(self, force_login=False):
    cache_path = os.path.join(cache_root_path, 'auth_token')
    if os.path.exists(cache_path) and not force_login:
      with open(cache_path, 'r') as cache_file:
        self.set_auth_token(cache_file.read())
    else:
      # Get a new auth token
      username = input('Username: ')
      password = getpass.getpass()
      auth_token = self.set_auth_token_with_credentials(username, password)
      with open(cache_path, 'w') as cache_file:
        cache_file.write(auth_token)

  def logout(self):
    cache_path = os.path.join(cache_root_path, 'auth_token')
    if os.path.exists(cache_path):
      os.remove(cache_path)

  def get_account(self, force_cache=True):
    cache_path = os.path.join(cache_root_path, 'account')
    if os.path.exists(cache_path):
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_account()
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def get_positions(self, force_cache=True):
    cache_path = os.path.join(cache_root_path, 'positions')
    if os.path.exists(cache_path):
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_positions()
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def get_instrument_by_id(self, instrument_id, force_cache=True):
    cache_path = os.path.join(cache_root_path, 'instrument_{}'.format(instrument_id))
    if os.path.exists(cache_path):
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_instrument_by_id(instrument_id)
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def get_instrument_by_symbol(self, symbol, force_cache=True):
    symbol_instrument_id_cache_path = os.path.join(cache_root_path, 'symbol_instrument_id_{}'.format(symbol))
    if os.path.exists(symbol_instrument_id_cache_path):
      with open(symbol_instrument_id_cache_path, 'r') as symbol_instrument_id_cache_file:
        instrument_id = symbol_instrument_id_cache_file.read()
      return self.get_instrument_by_id(instrument_id, force_cache)
    else:
      instrument_json = super(RobinhoodCachedClient, self).get_instrument_by_symbol(symbol)
      instrument_id = instrument_json['id']
      with open(symbol_instrument_id_cache_path, 'w') as symbol_instrument_id_cache_file:
        symbol_instrument_id_cache_file.write(instrument_id)
      with open(os.path.join(cache_root_path, 'instrument_{}'.format(instrument_id)), 'w') as instrument_cache_file:
        json.dump(instrument_json, instrument_cache_file)
      return instrument_json
