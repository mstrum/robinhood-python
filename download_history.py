#!/usr/bin/env python3

from decimal import Decimal
import argparse
import csv

#import logging
#logging.basicConfig(level=logging.DEBUG)

from dateutil.parser import parse
import pytz

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, CACHE_FIRST, FORCE_LIVE
from robinhood.util import get_last_id_from_url

# Set up the client
client = RobinhoodCachedClient()
client.login()

def add_margin(csv_writer, cache_mode):
  account = client.get_account(cache_mode=cache_mode)
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
      'price': used_margin,
      'amount': used_margin,
      'date': updated_at,
      'fees': 0,
  })
  csv_writer.writerow({
      'symbol': '',
      'name': 'Robinhood Gold',
      'type': 'margin',
      'side': 'available',
      'quantity': 1,
      'price': '{:.2f}'.format(unallocated_margin_cash),
      'amount': '{:.2f}'.format(unallocated_margin_cash),
      'date': updated_at,
      'fees': 0,
  })

def add_subscription_fees(csv_writer, cache_mode):
  for subscription_fee in client.get_subscription_fees(cache_mode=cache_mode):
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
        'price': amount,
        'amount': amount,
        'date': created_at,
        'fees': 0,
    })

def add_transfers(csv_writer, cache_mode):
  for transfer in client.get_ach_transfers(cache_mode=cache_mode):
    transfer_amount = Decimal(transfer['amount'])
    early_access_amount = Decimal(transfer['early_access_amount'])
    updated_at = parse(transfer['updated_at']).astimezone(pytz.timezone('US/Pacific')).date()
    amount = early_access_amount or transfer_amount
    direction = 'deposit_early_access' if early_access_amount else transfer['direction']

    relationship = client.get_ach_relationship_by_id(get_last_id_from_url(transfer['ach_relationship']), cache_mode=cache_mode)

    csv_writer.writerow({
        'symbol': '',
        'name': relationship['bank_account_nickname'],
        'type': 'transfer',
        'side': direction,
        'quantity': 1,
        'price': amount,
        'amount': amount,
        'date': updated_at,
        'fees': 0,
    })


def add_rewards(csv_writer, cache_mode):
  referrals = client.get_referrals(cache_mode=cache_mode)

  instrument_ids = [
    get_last_id_from_url(r['reward']['stocks'][0]['instrument_url'])
    for r in referrals if r['reward']['stocks']
  ]
  instruments = client.get_instruments(instrument_ids)
  instrument_by_id = {i['id']: i for i in instruments}

  for referral in referrals:
    direction = referral['direction']
    if direction != 'from':
      continue
    if not referral['reward']['stocks']:
      continue
    assert len(referral['reward']['stocks']) == 1
    if referral['reward']['stocks'][0]['state'] != 'granted':
      continue

    cost_basis = Decimal(referral['reward']['stocks'][0]['cost_basis'])
    quantity = int(referral['reward']['stocks'][0]['quantity'])
    updated_at = parse(referral['updated_at']).astimezone(pytz.timezone('US/Pacific')).date()

    instrument_id = get_last_id_from_url(referral['reward']['stocks'][0]['instrument_url'])
    instrument = instrument_by_id[instrument_id]
    name = instrument['simple_name'] or instrument['name']
    symbol = instrument['symbol']

    csv_writer.writerow({
        'symbol': symbol,
        'name': name,
        'type': 'reward',
        'side': 'receive',
        'quantity': quantity,
        'price': '{:.2f}'.format(cost_basis),
        'amount': '{:.2f}'.format(quantity * cost_basis),
        'date': updated_at.isoformat(),
        'fees': 0,
    })


def add_orders(csv_writer, cache_mode):
  orders = client.get_orders(cache_mode=cache_mode)

  instrument_ids = [get_last_id_from_url(o['instrument']) for o in orders]
  instruments = client.get_instruments(instrument_ids)
  instrument_by_id = {i['id']: i for i in instruments}

  for order in orders:
    order_id = order['id']
    state = order['state']

    if state != 'filled':
      if state not in ['queued', 'confirmed', 'cancelled']:
        print('Skipping order {} with state {} that may need to be handled...'.format(order_id, state))
      continue

    fees = Decimal(order['fees'])
    side = order['side']

    instrument_id = get_last_id_from_url(order['instrument'])
    instrument = instrument_by_id[instrument_id]
    name = instrument['simple_name'] or instrument['name']
    symbol = instrument['symbol']

    for execution in order['executions']:
      price = Decimal(execution['price'])
      quantity = int(float(execution['quantity']))
      amount = quantity * price
      transaction_on = parse(execution['timestamp']).astimezone(pytz.timezone('US/Pacific')).date()

      csv_writer.writerow({
          'symbol': symbol,
          'name': name,
          'type': 'order',
          'side': side,
          'quantity': quantity,
          'price': '{:.2f}'.format(price),
          'amount': '{:.2f}'.format(amount),
          'date': transaction_on.isoformat(),
          'fees': fees,
      })
      # Don't duplicate fees in multiple executions
      if fees:
        fees = Decimal(0)


def add_dividends(csv_writer, cache_mode):
  dividends = client.get_dividends(cache_mode=cache_mode)

  instrument_ids = [get_last_id_from_url(d['instrument']) for d in dividends]
  instruments = client.get_instruments(instrument_ids)
  instrument_by_id = {i['id']: i for i in instruments}

  for dividend in dividends:
    paid_at = dividend['paid_at']
    if not paid_at:
      continue
    paid_at = parse(paid_at)
    rate = Decimal(dividend['rate'])
    amount = Decimal(dividend['amount'])
    quantity = int(float(dividend['position']))

    instrument_id = get_last_id_from_url(dividend['instrument'])
    instrument = instrument_by_id[instrument_id]
    name = instrument['simple_name'] or instrument['name']
    symbol = instrument['symbol']

    csv_writer.writerow({
        'symbol': symbol,
        'name': name,
        'type': 'dividend',
        'side': 'receive',
        'quantity': quantity,
        'price': '{:.2f}'.format(rate),
        'amount': '{:.2f}'.format(amount),
        'date': paid_at.date(),
        'fees': 0,
    })


def download_history(cache_mode):
  with open('history.csv', 'w', newline='') as csv_file:
    fieldnames = [
        'symbol',
        'name',
        'side',
        'type',
        'quantity',
        'price',
        'amount',
        'date',
        'fees',
    ]
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()
    add_orders(csv_writer, cache_mode)
    add_dividends(csv_writer, cache_mode)
    add_rewards(csv_writer, cache_mode)
    add_transfers(csv_writer, cache_mode)
    add_subscription_fees(csv_writer, cache_mode)
    add_margin(csv_writer, cache_mode)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Download a list of all financial history')
  parser.add_argument(
      '--live',
      action='store_true',
      help='Force to not use cache for APIs where values change'
  )
  args = parser.parse_args()
  download_history(FORCE_LIVE if args.live else CACHE_FIRST)
