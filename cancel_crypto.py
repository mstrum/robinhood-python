#!/usr/bin/env python3

import argparse
import json

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, FORCE_LIVE

# Set up the client
client = RobinhoodCachedClient()
client.login()

def cancel_crypto_orders(order_ids):
    print('')
    print('!!!!!!!!!!!!!!!!!! CAUTION !!!!!!!!!!!!!!!!!!')
    confirm = input('Cancel {} order{}? [N/y] '.format(len(order_ids), 's' if len(order_ids) > 1 else ''))
    if confirm not in ['y', 'yes']:
      print('Bailed out!')
      exit()

    for order_id in order_ids:
      cancelled_order = client.cancel_crypto_order(order_id)
      print('Cancelled order {}'.format(order_id))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Cancel crypto orders')
  parser.add_argument('order_ids', nargs='*', help='The crypto order ids to cancel')
  args = parser.parse_args()

  order_ids = args.order_ids
  if not order_ids:
    orders = client.get_crypto_orders()
    order_ids = [order['id'] for order in orders if order['state'] in ['queued', 'confirmed']]

  if not order_ids:
    print('Nothing to see here... Move along.')
    exit()

  cancel_crypto_orders(order_ids)
