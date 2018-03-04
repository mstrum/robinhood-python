#!/usr/bin/env python3

import argparse
import csv

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient
from robinhood.util import KNOWN_TAGS

# Set up the client
client = RobinhoodCachedClient()
client.login()

def generate_tag_list(tag):
  with open('{}.csv'.format(tag), 'w', newline='') as csv_file:
    fieldnames = ['instrument_id']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    for instrument_id in client.get_instrument_ids_for_tag(tag):
      csv_writer.writerow({
        'instrument_id': instrument_id,
      })

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Get a list that Robinhood provides')
  parser.add_argument('tag', choices=KNOWN_TAGS, help='The tag to get a list for')
  args = parser.parse_args()
  generate_tag_list(args.tag)
