#!/usr/bin/env python3

from datetime import datetime
from decimal import Decimal
from math import ceil
import argparse
import json

from dateutil.parser import parse
import pytz

from robinhood.exceptions import NotFound
from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, CACHE_FIRST, FORCE_LIVE
from robinhood.util import OPTIONS_TYPES


def display_options_quote(client, options_type, symbol, date, strike, cache_mode):
  try:
    instrument = client.get_instrument_by_symbol(symbol)
  except NotFound:
    print('symbol {} was not found'.format(symbol))
    exit()
  else:
    instrument_id = instrument['id']

  options_chains = client.get_options_chains(instrument_ids=[instrument_id])
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
  expiration_dates = options_chain['expiration_dates']

  options_instruments = client.get_options_instruments(
      chain_id=chain_id, options_type=options_type, tradability='tradable', state='active', expiration_dates=[date])
  if not options_instruments:
    raise Exception('No options found on that date')

  options_instrument = None
  for potential_options_instrument in options_instruments:
    potential_strike = float(potential_options_instrument['strike_price'])
    if potential_strike == strike:
      options_instrument = potential_options_instrument
      break
  if not options_instrument:
    raise Exception('No options found at that strike price')

  options_quote = client.get_options_marketdata(options_instrument['id'])
  print(json.dumps(options_quote, indent=4))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Get a quote for a symbol')
  parser.add_argument('options_type', choices=OPTIONS_TYPES)
  parser.add_argument('symbol', type=str.upper, help='A symbol to get an options quote on')
  parser.add_argument('date', type=str, help='Date for the options to expire')
  parser.add_argument('strike', type=float, help='Amount the strike price should be')
  parser.add_argument(
      '--live',
      action='store_true',
      help='Force to not use cache for APIs where values change'
  )
  args = parser.parse_args()

  client = RobinhoodCachedClient()
  client.login()
  display_options_quote(
      client,
      args.options_type,
      args.symbol,
      args.date,
      args.strike,
      FORCE_LIVE if args.live else CACHE_FIRST
  )
