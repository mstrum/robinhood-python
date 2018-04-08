#!/usr/bin/env python3

from decimal import Decimal
import argparse
import json

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, CACHE_FIRST, FORCE_LIVE
from robinhood.util import get_last_id_from_url

client = RobinhoodCachedClient()
client.login()


def display_options_discoveries(symbol, cache_mode):
  try:
    instrument = client.get_instrument_by_symbol(symbol)
  except NotFound:
    print('symbol {} was not found'.format(symbol))
    exit()
  else:
    instrument_id = instrument['id']
    name = instrument['simple_name'] or instrument['name']

  options_chains = [c for c in client.get_options_chains(instrument_ids=[instrument_id]) if c['can_open_position']]
  if len(options_chains) != 1:
    raise Exception('Expected exactly one options chains listing, but got: {}'.format(json.dumps(options_chains, indent=4)))
  options_chain = options_chains[0]

  if len(options_chain['underlying_instruments']) != 1:
    raise Exception('Expected exactly one underlying instrument, but got: {}'.format(json.dumps(options_chain, indent=4)))
  if not options_chain['can_open_position']:
    raise Exception("Can't open position: {}".format(json.dumps(options_chain, indent=4)))
  chain_id = options_chain['id']
  options_instrument_id = options_chain['underlying_instruments'][0]['id']
  multiplier = Decimal(options_chain['trade_value_multiplier'])

  discoveries = client.get_options_discoveries(chain_id)
  option_instrument_ids = [discovery['legs'][0]['option_id'] for discovery in discoveries]
  options_instruments = client.get_options_instruments(options_instrument_ids=option_instrument_ids)
  options_instruments_by_id = {
    options_instrument['id']: options_instrument for options_instrument in options_instruments
  }

  options_quotes = client.get_options_marketdatas(option_instrument_ids)
  options_quote_by_id = {
    get_last_id_from_url(options_quote['instrument']): options_quote for options_quote in options_quotes
  }

  for discovery in discoveries:
    print('')
    print('----------------------------------------------')
    print(discovery['description'])
    print(discovery['strategy_type'])
    print(discovery['strategy_category'])
    print(', '.join(discovery['tags']))
    print(discovery['legs'][0]['side'])
    option_instrument_id = discovery['legs'][0]['option_id']
    option_instrument = options_instruments_by_id[option_instrument_id]
    print('Option')
    print('\tType\t{}'.format(option_instrument['type']))
    print('\tExpires\t{}'.format(option_instrument['expiration_date']))
    print('\tStrike\t{}'.format(Decimal(option_instrument['strike_price'])))
    options_quote = options_quote_by_id[option_instrument_id]
    adjusted_mark_price = Decimal(options_quote['adjusted_mark_price'])
    print('\tPrice\t${:.2f}'.format(adjusted_mark_price))
    print('\tCost\t${:.2f}'.format(adjusted_mark_price * 100))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Discover options for a symbol')
  parser.add_argument('symbol', type=str.upper, help='A symbol to discover options for')
  parser.add_argument(
      '--live',
      action='store_true',
      help='Force to not use cache for APIs where values change'
  )
  args = parser.parse_args()
  display_options_discoveries(
      args.symbol,
      FORCE_LIVE if args.live else CACHE_FIRST
  )
