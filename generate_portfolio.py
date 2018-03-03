#!/usr/bin/env python3

from decimal import Decimal
import csv

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient
from robinhood.util import get_instrument_id_from_url

# Set up the client
client = RobinhoodCachedClient()
client.login()

def generate_portfolio():
  with open('portfolio.csv', 'w', newline='') as portfolio_csv_file:
    fieldnames = ['symbol', 'short_name', 'full_name', 'quantity', 'average_buy_price', 'equity_cost']
    portfolio_csv_writer = csv.DictWriter(portfolio_csv_file, fieldnames=fieldnames)
    portfolio_csv_writer.writeheader()
    for position in client.get_positions():
      quantity = int(float(position['quantity']))
      average_buy_price = Decimal(position['average_buy_price'])
      equity_cost = quantity * average_buy_price
      instrument_id = get_instrument_id_from_url(position['instrument'])

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
