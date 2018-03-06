#!/usr/bin/env python3

from decimal import Decimal
import argparse
import csv

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient
from robinhood.util import get_last_id_from_url

# Set up the client
client = RobinhoodCachedClient()
client.login()


def generate_transfers(live):
  with open('transfers.csv', 'w', newline='') as csv_file:
    fieldnames = ['id', 'amount', 'direction', 'state', 'early_access_amount', 'expected_landing_date', 'fees', 'bank']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()
    for transfer in client.get_ach_transfers(force_live=live):
      # If any of these becomes not true, probably add to the csv
      assert not transfer['pending']
      assert not transfer['status_description']
      assert not transfer['cancel']

      relationship = client.get_ach_relationship(get_last_id_from_url(transfer['ach_relationship']))

      csv_writer.writerow({
        'id': transfer['id'],
        'amount': Decimal(transfer['amount']),
        'direction': transfer['direction'],
        'state': transfer['state'],
        'early_access_amount': Decimal(transfer['early_access_amount']),
        'expected_landing_date': transfer['expected_landing_date'],
        'fees': Decimal(transfer['fees']),
        'bank': relationship['bank_account_nickname'],
      })


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Download a list of your transfers')
  parser.add_argument('--live', action='store_true', help='Force to not use cache for APIs where values change')
  args = parser.parse_args()
  generate_transfers(args.live)
