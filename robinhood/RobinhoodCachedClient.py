from __future__ import print_function

import getpass
import json
import os

from .exceptions import MfaRequired
from .RobinhoodClient import RobinhoodClient
from .util import get_last_id_from_url

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

      try:
        auth_token = self.set_auth_token_with_credentials(username, password)
      except MfaRequired:
        mfa = input('MFA: ')
        auth_token = self.set_auth_token_with_credentials(username, password, mfa)

      with open(cache_path, 'w') as cache_file:
        cache_file.write(auth_token)

  def logout(self):
    cache_path = os.path.join(cache_root_path, 'auth_token')
    if os.path.exists(cache_path):
      os.remove(cache_path)

  def get_account(self, force_live=False):
    cache_path = os.path.join(cache_root_path, 'account')
    if os.path.exists(cache_path) and not force_live:
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_account()
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def get_referrals(self, force_live=False):
    cache_path = os.path.join(cache_root_path, 'referrals')
    if os.path.exists(cache_path) and not force_live:
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_referrals()
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def get_position_by_instrument_id(self, account_number, instrument_id, force_live=False):
    cache_path = os.path.join(cache_root_path, 'position_{}'.format(instrument_id))
    if os.path.exists(cache_path) and not force_live:
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_position_by_instrument_id(account_number, instrument_id)
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def get_sp500_movers(self, direction, force_live=False):
    cache_path = os.path.join(cache_root_path, 'sp500_movers_{}'.format(direction))
    if os.path.exists(cache_path) and not force_live:
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_sp500_movers(direction)
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def get_fundamental(self, symbol, force_live=False):
    cache_path = os.path.join(cache_root_path, 'fundamental_{}'.format(symbol))
    if os.path.exists(cache_path) and not force_live:
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_fundamental(symbol)
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def get_instrument_by_id(self, instrument_id, force_live=False):
    cache_path = os.path.join(cache_root_path, 'instrument_{}'.format(instrument_id))
    if os.path.exists(cache_path) and not force_live:
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_instrument_by_id(instrument_id)
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def get_ach_relationship_by_id(self, relationship_id, force_live=False):
    cache_path = os.path.join(cache_root_path, 'ach_relationship_{}'.format(relationship_id))
    if os.path.exists(cache_path) and not force_live:
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_ach_relationship_by_id(relationship_id)
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def get_order_by_id(self, order_id, force_live=False):
    cache_path = os.path.join(cache_root_path, 'order_{}'.format(order_id))
    if os.path.exists(cache_path) and not force_live:
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_order_by_id(order_id)
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def download_document_by_id(self, document_id, force_live=False):
    """Note that this uses binary content for the files."""
    cache_path = os.path.join(cache_root_path, 'document_pdf_{}'.format(document_id))
    if os.path.exists(cache_path) and not force_live:
      with open(cache_path, 'rb') as cache_file:
        return cache_file.read()
    else:
      cache_content = super(RobinhoodCachedClient, self).download_document_by_id(document_id)
      with open(cache_path, 'wb') as cache_file:
        cache_file.write(cache_content)
      return cache_content

  def get_ach_transfer_by_id(self, transfer_id, force_live=False):
    cache_path = os.path.join(cache_root_path, 'ach_transfer_{}'.format(transfer_id,))
    if os.path.exists(cache_path) and not force_live:
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_ach_transfer_by_id(transfer_id)
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def get_document_by_id(self, document_id, force_live=False):
    cache_path = os.path.join(cache_root_path, 'document_{}'.format(document_id))
    if os.path.exists(cache_path) and not force_live:
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_document_by_id(order_id)
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def get_dividend_by_id(self, dividend_id, force_live=False):
    cache_path = os.path.join(cache_root_path, 'dividend_{}'.format(dividend_id))
    if os.path.exists(cache_path) and not force_live:
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_dividend_by_id(dividend_id)
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def get_instrument_ids_for_tag(self, tag, force_live=False):
    cache_path = os.path.join(cache_root_path, 'tag_{}'.format(tag))
    if os.path.exists(cache_path) and not force_live:
      with open(cache_path, 'r') as cache_file:
        return json.load(cache_file)
    else:
      cache_json = super(RobinhoodCachedClient, self).get_instrument_ids_for_tag(tag)
      with open(cache_path, 'w') as cache_file:
        json.dump(cache_json, cache_file)
      return cache_json

  def get_documents(self, force_live=False):
    documents_list_cache_path = os.path.join(cache_root_path, 'documents')
    if os.path.exists(documents_list_cache_path) and not force_live:
      documents = []
      with open(documents_list_cache_path, 'r') as documents_list_cache_file:
        documents_list = json.load(documents_list_cache_file)
        for document_id in documents_list:
          documents.append(self.get_document_by_id(document_id, force_live=force_live))
    else:
      documents = super(RobinhoodCachedClient, self).get_documents()
      documents_list = []
      for document in documents:
        document_id = document['id']
        documents_list.append(document_id)
        document_cache_path = os.path.join(cache_root_path, 'document_{}'.format(document_id))
        with open(document_cache_path, 'w') as document_cache_file:
          json.dump(document, document_cache_file)
      with open(documents_list_cache_path, 'w') as documents_list_cache_file:
        json.dump(documents_list, documents_list_cache_file)
    return documents

  def get_ach_transfers(self, force_live=False):
    transfers_list_cache_path = os.path.join(cache_root_path, 'ach_transfers')
    if os.path.exists(transfers_list_cache_path) and not force_live:
      transfers = []
      with open(transfers_list_cache_path, 'r') as transfers_list_cache_file:
        transfers_list = json.load(transfers_list_cache_file)
        for transfer_id in transfers_list:
          transfers.append(self.get_ach_transfer_by_id(transfer_id, force_live=force_live))
    else:
      transfers = super(RobinhoodCachedClient, self).get_ach_transfers()
      transfers_list = []
      for transfer in transfers:
        transfer_id = transfer['id']
        transfers_list.append(transfer_id)
        transfer_cache_path = os.path.join(cache_root_path, 'ach_transfer_{}'.format(transfer_id))
        with open(transfer_cache_path, 'w') as transfer_cache_file:
          json.dump(transfer, transfer_cache_file)
      with open(transfers_list_cache_path, 'w') as transfers_list_cache_file:
        json.dump(transfers_list, transfers_list_cache_file)
    return transfers

  def get_dividends(self, force_live=False):
    dividends_list_cache_path = os.path.join(cache_root_path, 'dividends')
    if os.path.exists(dividends_list_cache_path) and not force_live:
      dividends = []
      with open(dividends_list_cache_path, 'r') as dividends_list_cache_file:
        dividends_list = json.load(dividends_list_cache_file)
        for dividend_id in dividends_list:
          dividends.append(self.get_dividend_by_id(dividend_id, force_live=force_live))
    else:
      dividends = super(RobinhoodCachedClient, self).get_dividends()
      dividends_list = []
      for dividend in dividends:
        dividend_id = dividend['id']
        dividends_list.append(dividend_id)
        dividend_cache_path = os.path.join(cache_root_path, 'dividend_{}'.format(dividend_id))
        with open(dividend_cache_path, 'w') as dividend_cache_file:
          json.dump(dividend, dividend_cache_file)
      with open(dividends_list_cache_path, 'w') as dividends_list_cache_file:
        json.dump(dividends_list, dividends_list_cache_file)
    return dividends

  def get_positions(self, include_old=False, force_live=False):
    positions_list_cache_path = os.path.join(cache_root_path, 'positions_' + ('all' if include_old else  'current'))
    if os.path.exists(positions_list_cache_path) and not force_live:
      account_number = self.get_account()['account_number']
      positions = []
      with open(positions_list_cache_path, 'r') as positions_list_cache_file:
        positions_list = json.load(positions_list_cache_file)
        for instrument_id in positions_list:
          positions.append(self.get_position_by_instrument_id(account_number, instrument_id, force_live=force_live))
    else:
      positions = super(RobinhoodCachedClient, self).get_positions(include_old=include_old)
      positions_list = []
      for position in positions:
        instrument_id = get_last_id_from_url(position['instrument'])
        positions_list.append(instrument_id)
        position_cache_path = os.path.join(cache_root_path, 'position_{}'.format(instrument_id))
        with open(position_cache_path, 'w') as position_cache_file:
          json.dump(position, position_cache_file)
      with open(positions_list_cache_path, 'w') as positions_list_cache_file:
        json.dump(positions_list, positions_list_cache_file)
    return positions

  def get_instrument_by_symbol(self, symbol, force_live=False):
    symbol_instrument_id_cache_path = os.path.join(cache_root_path, 'symbol_instrument_id_{}'.format(symbol))
    if os.path.exists(symbol_instrument_id_cache_path) and not force_live:
      with open(symbol_instrument_id_cache_path, 'r') as symbol_instrument_id_cache_file:
        instrument_id = symbol_instrument_id_cache_file.read()
      return self.get_instrument_by_id(instrument_id, force_live=force_live)
    else:
      instrument_json = super(RobinhoodCachedClient, self).get_instrument_by_symbol(symbol)
      instrument_id = instrument_json['id']
      with open(symbol_instrument_id_cache_path, 'w') as symbol_instrument_id_cache_file:
        symbol_instrument_id_cache_file.write(instrument_id)
      with open(os.path.join(cache_root_path, 'instrument_{}'.format(instrument_id)), 'w') as instrument_cache_file:
        json.dump(instrument_json, instrument_cache_file)
      return instrument_json

  def get_orders(self, instrument_id=None, force_live=False):
    """TODO: Handle orders by instrument."""
    if instrument_id:
      orders_list_cache_path = os.path.join(cache_root_path, 'instrument_orders_{}'.format(instrument_id))
    else:
      orders_list_cache_path = os.path.join(cache_root_path, 'orders')
    if os.path.exists(orders_list_cache_path) and not force_live:
      orders = []
      with open(orders_list_cache_path, 'r') as orders_list_cache_file:
        orders_list = json.load(orders_list_cache_file)
        for order_id in orders_list:
          orders.append(self.get_order_by_id(order_id, force_live=force_live))
    else:
      orders = super(RobinhoodCachedClient, self).get_orders(instrument_id=instrument_id)
      orders_list = []
      for order in orders:
        order_id = order['id']
        orders_list.append(order_id)
        order_cache_path = os.path.join(cache_root_path, 'order_{}'.format(order_id))
        with open(order_cache_path, 'w') as order_cache_file:
          json.dump(order, order_cache_file)
      with open(orders_list_cache_path, 'w') as orders_list_cache_file:
        json.dump(orders_list, orders_list_cache_file)
    return orders
