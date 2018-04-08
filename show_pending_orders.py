#!/usr/bin/env python3

import argparse
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from math import ceil

from dateutil.parser import parse
import pytz

from robinhood.exceptions import NotFound
from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, FORCE_LIVE
from robinhood.util import get_last_id_from_url


client = RobinhoodCachedClient()
client.login()


def display_pending_orders():
  orders = client.get_orders(cache_mode=FORCE_LIVE)
  pending_orders = [order for order in orders if order['state'] in ['queued', 'confirmed']]
  if len(pending_orders) == 0:
    print('\tNo pending orders')
    exit()

  instrument_ids = [get_last_id_from_url(o['instrument']) for o in pending_orders]
  instruments = client.get_instruments(instrument_ids)
  instrument_by_id = { i['id']: i for i in instruments }

  pending_orders_by_instrument = defaultdict(list)
  for order in pending_orders:
    instrument_id = get_last_id_from_url(order['instrument'])
    pending_orders_by_instrument[instrument_id].append(order)

  for instrument_id, instrument_orders in pending_orders_by_instrument.items():
    instrument = instrument_by_id[instrument_id]

    print('{} ({})'.format(instrument['symbol'], instrument['simple_name'] or instrument['name']))

    try:
      position = client.get_position_by_instrument_id(instrument['id'])
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

    for order in instrument_orders:
      order_id = order['id']
      order_state = order['state']
      order_type = order['type']
      order_side = order['side']
      order_quantity = int(float(order['quantity']))
      order_price = Decimal(order['price'])

      print('\t{}\t{} {}\t{} @ ${:.2f}\t({})'.format(
        order_state, order_type, order_side, order_quantity, order_price, order_id))

if __name__ == '__main__':
  display_pending_orders()
