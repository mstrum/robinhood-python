#!/usr/bin/env python3

from decimal import Decimal
import argparse
import csv

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient
from robinhood.util import get_last_id_from_url

# Set up the client
client = RobinhoodCachedClient()
client.login()


def generate_sp500_movers(live):
  for direction in ['up', 'down']:
    with open('movers_sp500_{}.csv'.format(direction), 'w', newline='') as csv_file:
      fieldnames = ['symbol', 'short_name', 'full_name', 'last_price', 'movement_pct']

      csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
      csv_writer.writeheader()
      for mover in client.get_sp500_movers(direction, force_live=live):
        instrument_id = get_last_id_from_url(mover['instrument_url'])
        last_price = Decimal(mover['price_movement']['market_hours_last_price'])
        movement_pct = Decimal(mover['price_movement']['market_hours_last_movement_pct'])

        instrument = client.get_instrument_by_id(instrument_id)
        simple_name = instrument['simple_name']
        full_name = instrument['name']
        symbol = instrument['symbol']

        csv_writer.writerow({
          'symbol': symbol,
          'short_name': simple_name,
          'full_name': full_name,
          'last_price': last_price,
          'movement_pct': movement_pct,
        })


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Download a list of s&p 500 movers')
  parser.add_argument('--live', action='store_true', help='Force to not use cache for APIs where values change')
  args = parser.parse_args()
  generate_sp500_movers(args.live)
