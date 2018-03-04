#!/usr/bin/env python3

from decimal import Decimal
import csv

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient
from robinhood.util import get_instrument_id_from_url

# Set up the client
client = RobinhoodCachedClient()
client.login()


def generate_dividends():
  with open('dividends.csv', 'w', newline='') as csv_file:
    fieldnames = ['symbol', 'short_name', 'full_name', 'paid', 'paid_at', 'payable_date', 'record_date', 'quantity', 'rate', 'amount']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()
    for dividend in client.get_dividends():
      paid_at = dividend['paid_at']
      is_paid = paid_at is not None
      payable_date = dividend['payable_date'] is not None
      record_date = dividend['record_date']
      rate = Decimal(dividend['rate'])
      amount = Decimal(dividend['amount'])
      quantity = int(float(dividend['position']))
      instrument_id = get_instrument_id_from_url(dividend['instrument'])

      instrument = client.get_instrument_by_id(instrument_id)
      simple_name = instrument['simple_name']
      full_name = instrument['name']
      symbol = instrument['symbol']

      csv_writer.writerow({
        'symbol': symbol,
        'short_name': simple_name,
        'full_name': full_name,
        'paid': is_paid,
        'paid_at': paid_at,
        'payable_date': payable_date,
        'record_date': record_date,
        'quantity': quantity,
        'rate': rate,
        'amount': amount,
      })


if __name__ == '__main__':
  generate_dividends()
