#!/usr/bin/env python3

import argparse
import json

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient
from robinhood.util import ORDER_TYPES, ORDER_SIDES

# Set up the client
client = RobinhoodCachedClient()
client.login()

from quote import display_quote


def place_order(order_type, order_side, symbol, quantity, price):
  account_url = client.get_account()['url']
  instrument = client.get_instrument_by_symbol(symbol)

  display_quote(client, symbol, True)

  print('')
  print('!!!!!!!!!!!!!!!!!! CAUTION !!!!!!!!!!!!!!!!!!')
  confirm = input('Are you sure that you want to sell {} shares of {} ({}) for ${:.2f} each? [N/y]? '.format(
    quantity, symbol, instrument['simple_name'] or instrument['name'], price)).lower()
  if confirm not in ['y', 'yes']:
    print('Bailed out!')
    exit()

  order = client.order(
    account_url,
    instrument['url'],
    order_type,
    order_side,
    symbol,
    quantity,
    price
  )
  print(json.dumps(order, indent=4))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Place an order')
  parser.add_argument('order_type', choices=ORDER_TYPES)
  parser.add_argument('order_side', choices=ORDER_SIDES)
  parser.add_argument('symbol', help='The stock ticker')
  parser.add_argument('quantity', type=int)
  parser.add_argument('price', type=float)
  args = parser.parse_args()
  place_order(
    args.order_type,
    args.order_side,
    args.symbol,
    args.quantity,
    args.price
  )

