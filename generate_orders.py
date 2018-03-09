#!/usr/bin/env python3

from decimal import Decimal
import argparse
import csv

from dateutil.parser import parse
import pytz

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient
from robinhood.util import get_instrument_id_from_url

# Set up the client
client = RobinhoodCachedClient()
client.login()


def generate_orders(live):
  with open('orders.csv', 'w', newline='') as csv_file:
    fieldnames = ['symbol', 'short_name', 'full_name', 'state', 'side', 'quantity', 'average_price', 'amount', 'last_transaction_at', 'fees']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()
    for order in client.get_orders(force_live=live):
      order_id = order['id']
      state = order['state']

      # TODO: Handle any others?
      if state != 'filled':
        if state not in ['queued', 'confirmed', 'cancelled']:
          print('Skipping order {} with state {} that may need to be handled...'.format(order_id, state))
        continue

      order_type = order['type']
      cumulative_quantity = int(float(order['cumulative_quantity']))
      average_price = Decimal(order['average_price'])
      amount = cumulative_quantity * average_price
      last_transaction_at = parse(order['last_transaction_at']).astimezone(pytz.timezone('US/Pacific'))
      fees = Decimal(order['fees'])
      side = order['side']
      instrument_id = get_instrument_id_from_url(order['instrument'])

      instrument = client.get_instrument_by_id(instrument_id)
      simple_name = instrument['simple_name']
      full_name = instrument['name']
      symbol = instrument['symbol']

      csv_writer.writerow({
        'symbol': symbol,
        'short_name': simple_name,
        'full_name': full_name,
        'state': state,
        'side': side,
        'quantity': cumulative_quantity,
        'average_price': average_price,
        'amount': amount,
        'last_transaction_at': last_transaction_at.isoformat(),
        'fees': fees,
      })


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Download a list of your completed orders')
  parser.add_argument('--live', action='store_true', help='Force to not use cache for APIs where values change')
  args = parser.parse_args()
  generate_orders(args.live)
