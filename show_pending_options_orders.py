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
from robinhood.util import get_last_id_from_url, DIRECTION_TO_ORDER_SIDE


client = RobinhoodCachedClient()
client.login()


def display_pending_options_orders():
  orders = client.get_options_orders()
  pending_orders = [order for order in orders if order['state'] in ['queued', 'confirmed']]
  if len(pending_orders) == 0:
    print('\tNo pending orders')
    exit()

  chain_ids = [order['chain_id'] for order in pending_orders]
  chains = client.get_options_chains(chain_ids=chain_ids)
  chain_by_id = {
      chain['id']: chain for chain in chains
  }

  instrument_id_by_chain_id = {
      chain['id']: get_last_id_from_url(chain['underlying_instruments'][0]['instrument']) for chain in chains
  }
  instruments = client.get_instruments(list(instrument_id_by_chain_id.values()))
  instrument_by_id = {i['id']: i for i in instruments}

  options_instrument_id_by_order_id = {
      order['id']: get_last_id_from_url(order['legs'][0]['option']) for order in pending_orders
  }
  options_instruments = client.get_options_instruments(options_instrument_ids=list(set(options_instrument_id_by_order_id.values())))
  option_instruments_by_id = {
      options_instrument['id']: options_instrument for options_instrument in options_instruments
  }

  instrument_id_to_orders = defaultdict(list)
  for order in pending_orders:
    instrument_id_to_orders[instrument_id_by_chain_id[order['chain_id']]].append(order)


  for instrument_id, instrument_orders in instrument_id_to_orders.items():
    instrument = instrument_by_id[instrument_id]

    print('{} ({})'.format(instrument['symbol'], instrument['simple_name'] or instrument['name']))

    for order in instrument_orders:
      order_id = order['id']
      order_state = order['state']
      order_type = order['type']
      order_side = DIRECTION_TO_ORDER_SIDE[order['direction']]
      order_quantity = int(float(order['quantity']))
      order_price = Decimal(order['price'])
      order_premium = Decimal(order['premium'])
      order_options_instrument = option_instruments_by_id[options_instrument_id_by_order_id[order_id]]
      order_option_type = order_options_instrument['type']
      order_option_expires = order_options_instrument['expiration_date']
      order_option_strike = Decimal(order_options_instrument['strike_price'])

      print('\t{}\t{} {}\t{} @ ${:.2f} (${:.2f} per share)\t({})'.format(
        order_state, order_type, order_side, order_quantity, order_premium, order_price, order_id))
      print('\t\t${:.2f} {} expiring {}'.format(order_option_strike, order_option_type, order_option_expires))


if __name__ == '__main__':
  display_pending_options_orders()
