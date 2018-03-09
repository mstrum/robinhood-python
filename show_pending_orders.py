#!/usr/bin/env python3

import argparse
from datetime import datetime
from decimal import Decimal
from math import ceil

from dateutil.parser import parse
import pytz

from robinhood.exceptions import NotFound
from robinhood.RobinhoodCachedClient import RobinhoodCachedClient
from robinhood.util import get_instrument_id_from_url


client = RobinhoodCachedClient()
client.login()


def display_pending_orders():
  account_number = client.get_account()['account_number']
  orders = client.get_orders(force_live=True)
  pending_orders = [order for order in orders if order['state'] in ['queued', 'confirmed']]
  if len(pending_orders) == 0:
    print('\tNo pending orders')
    exit()

  for order in pending_orders:
    instrument = client.get_instrument_by_id(get_instrument_id_from_url(order['instrument']))
    order_state = order['state']
    order_type = order['type']
    order_side = order['side']
    order_quantity = int(float(order['quantity']))
    order_price = Decimal(order['price'])

    print('{} ({})'.format(instrument['symbol'], instrument['simple_name'] or instrument['name']))

    try:
      position = client.get_position_by_instrument_id(account_number, instrument['id'])
    except NotFound:
      print('\tNo current position (or ever)')
    else:
      position_quantity = int(float(position['quantity']))
      if not position_quantity:
        print('\tNo current position (sold off)')
      else:
        position_average_buy_price = Decimal(position['average_buy_price'])
        position_equity_cost = position_quantity * position_average_buy_price
        print('\tcurrent position\t\t{} @ ${:.2f}'.format(
          position_quantity, position_average_buy_price, position_equity_cost))

    print('\t{}\t{} {}\t{} @ ${:.2f}'.format(
      order_state, order_type, order_side, order_quantity, order_price))


if __name__ == '__main__':
  display_pending_orders()

