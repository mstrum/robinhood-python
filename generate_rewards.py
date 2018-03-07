#!/usr/bin/env python3

from decimal import Decimal
import argparse
import csv

from dateutil.parser import parse
import pytz

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient
from robinhood.util import get_last_id_from_url

# Set up the client
client = RobinhoodCachedClient()
client.login()


def generate_rewards(live):
  with open('rewards.csv', 'w', newline='') as csv_file:
    fieldnames = ['symbol', 'short_name', 'full_name', 'state', 'quantity', 'cost_basis', 'date', 'direction', 'other_user']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()
    for referral in client.get_referrals(force_live=live):
      direction = referral['direction']
      referral_id = referral['id']
      instrument_id = get_last_id_from_url(referral['reward']['stocks'][0]['instrument_url'])
      cost_basis = Decimal(referral['reward']['stocks'][0]['cost_basis'])
      state = referral['reward']['stocks'][0]['state']
      quantity = int(referral['reward']['stocks'][0]['quantity'])
      updated_at = parse(referral['updated_at']).astimezone(pytz.timezone('US/Pacific')).date()
      other_user = '{} {}'.format(referral['other_user']['first_name'], referral['other_user']['last_initial'])

      instrument = client.get_instrument_by_id(instrument_id)
      simple_name = instrument['simple_name']
      full_name = instrument['name']
      symbol = instrument['symbol']

      csv_writer.writerow({
        'symbol': symbol,
        'short_name': simple_name,
        'full_name': full_name,
        'state': state,
        'quantity': quantity,
        'cost_basis': cost_basis,
        'date': updated_at.isoformat(),
        'direction': direction,
        'other_user': other_user,
      })


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Download a list of your rewards')
  parser.add_argument('--live', action='store_true', help='Force to not use cache for APIs where values change')
  args = parser.parse_args()
  generate_rewards(args.live)
