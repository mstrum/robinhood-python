#!/usr/bin/env python3

from decimal import Decimal
import argparse
import json

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, FORCE_LIVE
from robinhood.util import ORDER_TYPES, ORDER_SIDES

# Set up the client
client = RobinhoodCachedClient()
client.login()


def place_order(order_type, order_side, symbol, quantity, price):
  quote = client.get_crypto_quote(symbol)
  currency_pair_id = quote['id']
  currency_pair = client.get_crypto_currency_pair(currency_pair_id)

  order = client.order_crypto(
      currency_pair_id, order_type, order_side, quantity, price)
  print(json.dumps(order, indent=4))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Place an order')
  parser.add_argument('order_type', choices=ORDER_TYPES)
  parser.add_argument('order_side', choices=ORDER_SIDES)
  parser.add_argument('symbol', type=str.upper, help='The cryptocurrency + currency ticker')
  parser.add_argument('quantity', type=float)
  parser.add_argument('price', type=float)
  args = parser.parse_args()
  place_order(
      args.order_type,
      args.order_side,
      args.symbol,
      args.quantity,
      args.price
  )

