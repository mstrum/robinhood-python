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
  name = currency_pair['name']

  is_tradable = currency_pair['tradability'] == 'tradable'
  if not is_tradable:
    print("Sorry, {} ({}) isn't tradable".format(symbol, name))
    exit()

  min_order_size = Decimal(currency_pair['min_order_size'])
  max_order_size = Decimal(currency_pair['max_order_size'])
  crypto_increment = Decimal(currency_pair['asset_currency']['increment'])
  price_increment = Decimal(currency_pair['quote_currency']['increment'])

  if price % price_increment != 0:
    print("Sorry, price must be a multiple of {}".format(price_increment))
    exit()
  if quantity < min_order_size or quantity > max_order_size:
    print("Sorry, order quantity must be between {} and {}".format(min_order_size, max_order_size))
    exit()
  if quantity % crypto_increment != 0:
    print("Sorry, quantity must be a multiple of {}".format(crypto_increment))
    exit()

  print('')
  print('!!!!!!!!!!!!!!!!!! CAUTION !!!!!!!!!!!!!!!!!!')
  confirm = input('Are you sure that you want to {} {} {} {} ({}) for ${:.2f}? [N/y]? '.format(
    order_type,
    order_side,
    quantity,
    symbol,
    name,
    price)).lower()
  if confirm not in ['y', 'yes']:
    print('Bailed out!')
    exit()

  order = client.order_crypto(
      currency_pair_id, order_type, order_side, quantity, price)
  print(json.dumps(order, indent=4))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Place an order')
  parser.add_argument('order_type', choices=ORDER_TYPES)
  parser.add_argument('order_side', choices=ORDER_SIDES)
  parser.add_argument('symbol', type=str.upper, help='The cryptocurrency + currency ticker')
  parser.add_argument('quantity', type=Decimal)
  parser.add_argument('price', type=Decimal)
  args = parser.parse_args()
  place_order(
      args.order_type,
      args.order_side,
      args.symbol,
      args.quantity,
      args.price
  )

