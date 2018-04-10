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
from robinhood.util import get_last_id_from_url, OPTIONS_TYPES


def display_options_quote(client, options_type, symbol, dates, strike, cache_mode):
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
  multiplier = Decimal(options_chain['trade_value_multiplier'])

  kwargs = {}
  if dates:
    kwargs['expiration_dates'] = dates
  if options_type:
    kwargs['options_type'] = options_type
  potential_options_instruments = client.get_options_instruments(chain_id=chain_id, tradability='tradable', state='active', **kwargs)
  if not potential_options_instruments:
    raise Exception('No options found')

  options_instruments = []
  for potential_options_instrument in potential_options_instruments:
    if strike is None or strike == float(potential_options_instrument['strike_price']):
      options_instruments.append(potential_options_instrument)
  if not options_instruments:
    raise Exception('No options found')

  options_instrument_by_id = {
    options_instrument['id']: options_instrument for options_instrument in options_instruments
  }

  options_quotes = client.get_options_marketdatas([options_instrument['id'] for options_instrument in options_instruments])

  for options_quote in options_quotes:
    break_even_price = Decimal(options_quote['break_even_price'])
    ask_size = options_quote['ask_size']
    ask_price = Decimal(options_quote['ask_price'])
    bid_size = options_quote['bid_size']
    bid_price = Decimal(options_quote['bid_price'])
    adjusted_mark_price = Decimal(options_quote['adjusted_mark_price'])
    mark_price = Decimal(options_quote['mark_price'])
    max_loss = multiplier * adjusted_mark_price
    bid_spread = ask_price - bid_price
    implied_volatility = Decimal(options_quote['implied_volatility'] or 1) * 100
    high_price = Decimal(options_quote['high_price'] or 0)
    low_price = Decimal(options_quote['low_price'] or 0)
    hl_spread = high_price - low_price
    last_trade_size = options_quote['last_trade_size']
    last_trade_price = Decimal(options_quote['last_trade_price'] or 0)
    open_interest = options_quote['open_interest']
    volume = options_quote['volume']
    options_instrument_id = get_last_id_from_url(options_quote['instrument'])
    options_instrument = options_instrument_by_id[options_instrument_id]
    expiration_date = options_instrument['expiration_date']
    option_strike = Decimal(options_instrument['strike_price'])

    print('')
    print('${:.2f} {} ({}) {}'.format(option_strike, symbol, name, options_type[0].upper() + options_type[1:]))
    print('Break even\t ${:.2f}'.format(break_even_price))
    print('Expires\t\t {}'.format(expiration_date))
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
  parser.add_argument('symbol', type=str.upper, help='A symbol to get an options quote on')
  parser.add_argument('-t', '--type', choices=OPTIONS_TYPES)
  parser.add_argument('-d', '--date', nargs='+', type=str, dest='dates', default=[], help='Date for the options to expire')
  parser.add_argument('-s', '--strike', type=float, help='Amount the strike price should be')
  parser.add_argument(
      '--live',
      action='store_true',
      help='Force to not use cache for APIs where values change'
  )
  args = parser.parse_args()

  if not args.dates and not args.strike:
    raise Exception('You need to pass in --date and/or --strike')

  client = RobinhoodCachedClient()
  client.login()
  display_options_quote(
      client,
      args.type,
      args.symbol,
      args.dates,
      args.strike,
      FORCE_LIVE if args.live else CACHE_FIRST
  )
