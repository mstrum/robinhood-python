"""
This expects a credentials file at .creds, make sure to run login.py and then
logout.py when you are done.
"""

from datetime import datetime
from decimal import Decimal
from math import ceil
from urllib.parse import urlparse
import csv
import json

from dateutil.parser import parse
import pytz

from robinhood.exceptions import NotFound
from robinhood.RobinhoodCachedClient import RobinhoodCachedClient

# Set up the client
client = RobinhoodCachedClient()
client.login()
account_number = client.get_account()['account_number']

def generate_portfolio():
  with open('portfolio.csv', 'w', newline='') as portfolio_csv_file:
    fieldnames = ['symbol', 'short_name', 'full_name', 'quantity', 'average_buy_price', 'equity_cost']
    portfolio_csv_writer = csv.DictWriter(portfolio_csv_file, fieldnames=fieldnames)
    portfolio_csv_writer.writeheader()
    for position in client.get_positions():
      quantity = int(float(position['quantity']))
      average_buy_price = Decimal(position['average_buy_price'])
      equity_cost = quantity * average_buy_price

      instrument_id = urlparse(position['instrument']).path.split('/')[-2]
      # Make sure this is in the expected format
      assert len(instrument_id) == 36  # UUID v4 length
      assert instrument_id[14] == '4'  # UUID v4 marker
      instrument = client.get_instrument_by_id(instrument_id)
      simple_name = instrument['simple_name']
      full_name = instrument['name']
      symbol = instrument['symbol']

      portfolio_csv_writer.writerow({
        'symbol': symbol,
        'short_name': simple_name,
        'full_name': full_name,
        'quantity': quantity,
        'average_buy_price': average_buy_price,
        'equity_cost': equity_cost
      })

if __name__ == '__main__':
  generate_portfolio()
