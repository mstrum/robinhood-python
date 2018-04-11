#!/usr/bin/env python3

import argparse
from datetime import datetime
from decimal import Decimal
from math import ceil

from dateutil.parser import parse
import pytz

from robinhood.exceptions import NotFound
from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, CACHE_FIRST, FORCE_LIVE


def display_crypto_quote(client, symbols, cache_mode):
  currency_pairs = client.get_crypto_currency_pairs()
  currency_pair_by_id = {
      currency_pair['id']: currency_pair for currency_pair in currency_pairs
  }

  if symbols:
    quotes = client.get_crypto_quotes(symbols=symbols)
  else:
    quotes = client.get_crypto_quotes(currency_pair_ids=list(currency_pair_by_id.keys()))

  for quote in quotes:
    currency_pair = currency_pair_by_id[quote['id']]
    ask = Decimal(quote['ask_price'])
    bid = Decimal(quote['bid_price'])
    low = Decimal(quote['low_price'])
    high = Decimal(quote['high_price'])
    mark = Decimal(quote['mark_price'])

    print('')
    print('Crypto:\t{} ({})'.format(quote['symbol'], currency_pair['name']))
    print('L/H:\t${:.2f} <-> ${:.2f}'.format(low, high))
    if bid != ask:
      print('Spread:\t${:.2f} <-> ${:.2f}'.format(bid, ask))
    print('Mark:\t${:.2f}'.format(mark))
    print('Vol:\t{}'.format(int(round(float(quote['volume'])))))

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Get a quote for a cryptocurrency')
  parser.add_argument('-s', '--symbol', nargs='*', type=str.upper, dest='symbols', default=[], help='A symbol to get a quote on')
  parser.add_argument(
      '--live',
      action='store_true',
      help='Force to not use cache for APIs where values change'
  )
  args = parser.parse_args()

  client = RobinhoodCachedClient()
  client.login()
  display_crypto_quote(client, args.symbols, FORCE_LIVE if args.live else CACHE_FIRST)
