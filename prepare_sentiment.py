#!/usr/bin/env python3

from decimal import Decimal
import argparse
import json
import os
import shutil

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, CACHE_FIRST, FORCE_LIVE
from robinhood.util import get_last_id_from_url

# Set up the client
client = RobinhoodCachedClient()
client.login()


def show_potentials(decay_priority, cache_mode):
  # Load the portfolio.
  positions = client.get_positions(cache_mode=cache_mode)

  position_by_instrument_id = {}
  for position in positions:
    quantity = int(float(position['quantity']))
    average_buy_price = Decimal(position['average_buy_price'])
    instrument_id = get_last_id_from_url(position['instrument'])

    position_by_instrument_id[instrument_id] = {
        'quantity': quantity,
        'average_buy_price': average_buy_price,
        'equity_cost': quantity * average_buy_price,
        'instrument_id': instrument_id,
    }

  instrument_ids = list(position_by_instrument_id.keys())
  instruments = client.get_instruments(instrument_ids)
  position_symbol_to_instrument_id = {}
  for instrument in instruments:
    instrument_id = instrument['id']
    position_by_instrument_id[instrument_id]['symbol'] = instrument['symbol']
    position_by_instrument_id[instrument_id]['simple_name'] = instrument['simple_name']
    position_by_instrument_id[instrument_id]['full_name'] = instrument['name']
    position_symbol_to_instrument_id[instrument['symbol']] = instrument_id

  position_quotes = client.get_quotes(instrument_ids, cache_mode=cache_mode)
  for quote in position_quotes:
    instrument_id = get_last_id_from_url(quote['instrument'])
    position = position_by_instrument_id[instrument_id]

    position['last_price'] = Decimal(quote['last_trade_price'])
    position['equity_worth'] = position['quantity'] * position['last_price']

  # Load sentiment if available.
  if os.path.exists('sentiment.json'):
    with open('sentiment.json', 'r') as sentiment_file:
      sentiment_json = json.load(sentiment_file)
    shutil.copyfile('sentiment.json', 'sentiment.old.json')
  else:
    sentiment_json = {}

  # Delete any equities that were sold off.
  sentiment_symbols = sentiment_json.keys()
  for symbol in sentiment_symbols:
    if symbol not in position_symbol_to_instrument_id:
      del sentiment_json[symbol]

  # Add any new ones.
  for symbol in position_symbol_to_instrument_id.keys():
    if symbol not in sentiment_json:
      sentiment_json[symbol] = {}

  # Bump up priority if there are any p0
  if decay_priority:
    for position in sentiment_json.values():
      position_pority = position.get('priority')
      if position_pority is not None:
        position['priority'] += 1

  with open('sentiment.json', 'w') as sentiment_file:
    json.dump(sentiment_json, sentiment_file, indent=4)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Show various position potentials to buy into')
  parser.add_argument(
      '--live',
      action='store_true',
      help='Force to not use cache for APIs where values change'
  )
  parser.add_argument(
      '--decay-priority',
      action='store_true',
      help='Lower the priority of everything'
  )
  args = parser.parse_args()
  show_potentials(args.decay_priority, FORCE_LIVE if args.live else CACHE_FIRST)
