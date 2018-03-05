#!/usr/bin/env python3

import argparse
import csv

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient
from robinhood.util import KNOWN_TAGS

# Set up the client
client = RobinhoodCachedClient()
client.login()


def generate_tag_list(tag, live):
  with open('{}.csv'.format(tag), 'w', newline='') as csv_file:
    fieldnames = ['symbol', 'short_name', 'full_name']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    for instrument_id in client.get_instrument_ids_for_tag(tag, force_live=live):
      instrument = client.get_instrument_by_id(instrument_id)
      simple_name = instrument['simple_name']
      full_name = instrument['name']
      symbol = instrument['symbol']

      csv_writer.writerow({
        'symbol': symbol,
        'short_name': simple_name,
        'full_name': full_name,
      })


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Get a list that Robinhood provides')
  parser.add_argument('tag', choices=KNOWN_TAGS, help='The tag to get a list for')
  parser.add_argument('--live', action='store_true', help='Force to not use cache for APIs where values change')
  args = parser.parse_args()
  generate_tag_list(args.tag, args.live)
