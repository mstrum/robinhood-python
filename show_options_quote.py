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

  break_even_price = Decimal(options_quote['break_even_price'])
  ask_size = options_quote['ask_size']
  ask_price = Decimal(options_quote['ask_price'])
  bid_size = options_quote['bid_size']
  bid_price = Decimal(options_quote['bid_price'])
  adjusted_mark_price = Decimal(options_quote['adjusted_mark_price'])
  mark_price = Decimal(options_quote['mark_price'])
  max_loss = 100 * adjusted_mark_price
  bid_spread = ask_price - bid_price
  implied_volatility = Decimal(options_quote['implied_volatility']) * 100
  high_price = Decimal(options_quote['high_price'])
  low_price = Decimal(options_quote['low_price'])
  hl_spread = high_price - low_price
  last_trade_size = options_quote['last_trade_size']
  last_trade_price = Decimal(options_quote['last_trade_price'])
  open_interest = options_quote['open_interest']
  volume = options_quote['volume']

  print('${:.2f} {} ({}) {}'.format(strike, symbol, name, options_type[0].upper() + options_type[1:]))
  print('Break even\t ${:.2f}'.format(break_even_price))
  print('Expires\t\t {}'.format(date))
  print('Spread\t\t ${:.2f} ({}) <-> ${:.2f} ({})'.format(bid_price, bid_size, ask_price, ask_size))
  print('\t\t\t${:.2f} ({:.2f}%)'.format(bid_spread, bid_spread * 100 / adjusted_mark_price))
  print('Low/High\t ${:.2f} <-> ${:.2f}'.format(low_price, high_price))
  print('\t\t\t${:.2f} ({:.2f}%)'.format(hl_spread, hl_spread * 100 / adjusted_mark_price))
  print('Max loss\t ${:.2f}'.format(max_loss))
  print('Impl Volatil\t {:.2f}%'.format(implied_volatility))
  print('Last\t\t {} @ ${:.2f}'.format(last_trade_size, last_trade_price))
  print('Open Int\t {}'.format(open_interest))
  print('Volume\t\t {}'.format(volume))


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
