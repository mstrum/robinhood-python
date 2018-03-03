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
from .util import get_instrument_id_from_url

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

  def get_position_by_instrument_id(self, account_number, instrument_id, force_cache=True):
    cache_path = os.path.join(cache_root_path, 'position_{}'.format(instrument_id))
    if os.path.exists(cache_path):
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_position_by_instrument_id(account_number, instrument_id)
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def get_fundamental(self, symbol, force_cache=True):
    cache_path = os.path.join(cache_root_path, 'fundamental_{}'.format(symbol))
    if os.path.exists(cache_path):
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_fundamental(symbol)
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

  def get_positions(self, include_old=False, force_cache=True):
    positions_list_cache_path = os.path.join(cache_root_path, 'positions_' + ('all' if include_old else  'current'))
    if os.path.exists(positions_list_cache_path):
      account_number = self.get_account()['account_number']
      positions = []
      with open(positions_list_cache_path, 'r') as positions_list_cache_file:
        positions_list = json.load(positions_list_cache_file)
        for instrument_id in positions_list:
          positions.append(self.get_position_by_instrument_id(account_number, instrument_id, force_cache))
    else:
      positions = super(RobinhoodCachedClient, self).get_positions(include_old=include_old)
      positions_list = []
      for position in positions:
        instrument_id = get_instrument_id_from_url(position['instrument'])
        positions_list.append(instrument_id)
        position_cache_path = os.path.join(cache_root_path, 'position_{}'.format(instrument_id))
        with open(position_cache_path, 'w') as position_cache_file:
          json.dump(position, position_cache_file)
      with open(positions_list_cache_path, 'w') as positions_list_cache_file:
        json.dump(positions_list, positions_list_cache_file)
    return positions

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
