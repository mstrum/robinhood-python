#!/usr/bin/env python3

import argparse
import json

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, FORCE_LIVE
from robinhood.util import ORDER_TYPES, ORDER_SIDES

# Set up the client
client = RobinhoodCachedClient()
client.login()

from show_quote import display_quote


def place_order(order_type, order_side, symbol, quantity, price, no_cancel):
  account_url = client.get_account()['url']
  instrument = client.get_instrument_by_symbol(symbol)

  display_quote(client, symbol, True)

  # We could be more smart and allow canceling individual orders,
  # but for now just do complete cancelling
  orders = client.get_orders(instrument_id=instrument['id'], cache_mode=FORCE_LIVE)
  pending_same_side_orders = [
    order for order in orders
    if order['state'] in ['queued', 'confirmed'] and order['side'] == order_side
  ]
  if pending_same_side_orders and no_cancel is not True:
    print('')
    print('!!!!!!!!!!!!!!!!!! CAUTION !!!!!!!!!!!!!!!!!!')
    confirm = input('There appear to be pending orders, continuing will cancel them prior to placing the new order. Continue? [N/y] ')
    if confirm not in ['y', 'yes']:
      print('Bailed out!')
      exit()

  print('')
  print('!!!!!!!!!!!!!!!!!! CAUTION !!!!!!!!!!!!!!!!!!')
  confirm = input('Are you sure that you want to {} {} {} shares of {} ({}) for ${:.2f} each? [N/y]? '.format(
    order_type, order_side, quantity, symbol, instrument['simple_name'] or instrument['name'], price)).lower()
  if confirm not in ['y', 'yes']:
    print('Bailed out!')
    exit()

  if no_cancel is not True and pending_same_side_orders:
    for pending_order in pending_same_side_orders:
      cancelled_order = client.cancel_order(pending_order['id'])
      print('Cancelled order {}'.format(pending_order['id']))

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
  parser.add_argument('symbol', type=str.upper, help='The stock ticker')
  parser.add_argument('quantity', type=int)
  parser.add_argument('price', type=float)
  parser.add_argument('--no-cancel', action='store_true', help='Dont cancel any pending orders')
  args = parser.parse_args()
  place_order(
      args.order_type,
      args.order_side,
      args.symbol,
      args.quantity,
      args.price,
      args.no_cancel,
  )

