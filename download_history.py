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

def add_margin(csv_writer, live):
  account = client.get_account(force_live=live)
  unallocated_margin_cash = Decimal(account['margin_balances']['unallocated_margin_cash'])
  margin_limit = Decimal(account['margin_balances']['margin_limit'])
  updated_at = parse(account['margin_balances']['updated_at']).astimezone(pytz.timezone('US/Pacific')).date()
  if margin_limit == 0:
    return

  used_margin = margin_limit - unallocated_margin_cash

  csv_writer.writerow({
    'symbol': '',
    'name': 'Robinhood Gold',
    'type': 'margin',
    'side': 'used',
    'quantity': 1,
    'average_price': used_margin,
    'amount': used_margin,
    'date': updated_at,
    'fees': 0,
    'num_executions': 1,
  })
  csv_writer.writerow({
    'symbol': '',
    'name': 'Robinhood Gold',
    'type': 'margin',
    'side': 'available',
    'quantity': 1,
    'average_price': '{:.2f}'.format(unallocated_margin_cash),
    'amount': '{:.2f}'.format(unallocated_margin_cash),
    'date': updated_at,
    'fees': 0,
    'num_executions': 1,
  })

def add_subscription_fees(csv_writer, live):
  for subscription_fee in client.get_subscription_fees(force_live=live):
    amount = Decimal(subscription_fee['amount'])
    created_at = parse(subscription_fee['created_at']).astimezone(pytz.timezone('US/Pacific')).date()
    assert not subscription_fee['refunds']
    assert float(subscription_fee['credit']) == 0.0
    assert float(subscription_fee['carry_forward_credit']) == 0.0

    csv_writer.writerow({
      'symbol': '',
      'name': 'Robinhood Gold',
      'type': 'subscription_fee',
      'side': 'paid',
      'quantity': 1,
      'average_price': amount,
      'amount': amount,
      'date': created_at,
      'fees': 0,
      'num_executions': 1,
    })

def add_transfers(csv_writer, live):
  for transfer in client.get_ach_transfers(force_live=live):
    transfer_amount = Decimal(transfer['amount'])
    early_access_amount = Decimal(transfer['early_access_amount'])
    updated_at = parse(transfer['updated_at']).astimezone(pytz.timezone('US/Pacific')).date()
    amount = early_access_amount or transfer_amount
    direction = 'deposit_early_access' if early_access_amount else transfer['direction']

    relationship = client.get_ach_relationship_by_id(get_last_id_from_url(transfer['ach_relationship']), force_live=live)

    csv_writer.writerow({
      'symbol': '',
      'name': relationship['bank_account_nickname'],
      'type': 'transfer',
      'side': direction,
      'quantity': 1,
      'average_price': amount,
      'amount': amount,
      'date': updated_at,
      'fees': 0,
      'num_executions': 1,
    })


def add_rewards(csv_writer, live):
  for referral in client.get_referrals(force_live=live):
    direction = referral['direction']
    if direction != 'from':
      continue
    if not referral['reward']['stocks']:
      continue
    assert len(referral['reward']['stocks']) == 1
    if referral['reward']['stocks'][0]['state'] != 'granted':
      continue

    instrument_id = get_last_id_from_url(referral['reward']['stocks'][0]['instrument_url'])
    cost_basis = Decimal(referral['reward']['stocks'][0]['cost_basis'])
    quantity = int(referral['reward']['stocks'][0]['quantity'])
    updated_at = parse(referral['updated_at']).astimezone(pytz.timezone('US/Pacific')).date()
    other_user = '{} {}'.format(referral['other_user']['first_name'], referral['other_user']['last_initial'])

    instrument = client.get_instrument_by_id(instrument_id)
    name = instrument['simple_name'] or instrument['name']
    symbol = instrument['symbol']

    csv_writer.writerow({
      'symbol': symbol,
      'name': name,
      'type': 'reward',
      'side': 'receive',
      'quantity': quantity,
      'average_price': '{:.2f}'.format(cost_basis),
      'amount': '{:.2f}'.format(quantity * cost_basis),
      'date': updated_at.isoformat(),
      'fees': 0,
      'num_executions': 1,
    })


def add_orders(csv_writer, live):
  for order in client.get_orders(force_live=live):
    order_id = order['id']
    state = order['state']

    if state != 'filled':
      if state not in ['queued', 'confirmed', 'cancelled']:
        print('Skipping order {} with state {} that may need to be handled...'.format(order_id, state))
      continue

    order_type = order['type']

    num_executions = len(order['executions'])
    cumulative_quantity = int(float(order['cumulative_quantity']))
    average_price = Decimal(order['average_price'])
    amount = cumulative_quantity * average_price
    last_transaction_at = parse(order['last_transaction_at']).astimezone(pytz.timezone('US/Pacific'))
    fees = Decimal(order['fees'])
    side = order['side']
    instrument_id = get_last_id_from_url(order['instrument'])

    instrument = client.get_instrument_by_id(instrument_id)
    name = instrument['simple_name'] or instrument['name']
    symbol = instrument['symbol']

    csv_writer.writerow({
      'symbol': symbol,
      'name': name,
      'type': 'order',
      'side': side,
      'quantity': cumulative_quantity,
      'average_price': '{:.2f}'.format(average_price),
      'amount': '{:.2f}'.format(amount),
      'date': last_transaction_at.date().isoformat(),
      'fees': fees,
      'num_executions': num_executions,
    })


def add_dividends(csv_writer, live):
  for dividend in client.get_dividends(force_live=live):
    paid_at = dividend['paid_at']
    if not paid_at:
      continue
    paid_at = parse(paid_at)
    rate = Decimal(dividend['rate'])
    amount = Decimal(dividend['amount'])
    quantity = int(float(dividend['position']))
    instrument_id = get_last_id_from_url(dividend['instrument'])

    instrument = client.get_instrument_by_id(instrument_id)
    name = instrument['simple_name'] or instrument['name']
    symbol = instrument['symbol']

    csv_writer.writerow({
      'symbol': symbol,
      'name': name,
      'type': 'dividend',
      'side': 'receive',
      'quantity': quantity,
      'average_price': '{:.2f}'.format(rate),
      'amount': '{:.2f}'.format(amount),
      'date': paid_at.date(),
      'fees': 0,
      'num_executions': 1,
    })


def download_history(live):
  with open('history.csv', 'w', newline='') as csv_file:
    fieldnames = [
      'symbol',
      'name',
      'side',
      'type',
      'quantity',
      'average_price',
      'amount',
      'date',
      'fees',
      'num_executions',
    ]
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()
    add_orders(csv_writer, live)
    add_dividends(csv_writer, live)
    add_rewards(csv_writer, live)
    add_transfers(csv_writer, live)
    add_subscription_fees(csv_writer, live)
    add_margin(csv_writer, live)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Download a list of all financial history')
  parser.add_argument('--live', action='store_true', help='Force to not use cache for APIs where values change')
  args = parser.parse_args()
  download_history(args.live)

