#!/usr/bin/env python3

from decimal import Decimal
import argparse
import csv

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient
from robinhood.util import get_instrument_id_from_url

# Set up the client
client = RobinhoodCachedClient()
client.login()


def generate_portfolio(live):
  with open('portfolio.csv', 'w', newline='') as csv_file:
    fieldnames = [
      'symbol', 'short_name', 'full_name', 'quantity', 'average_buy_price',
      'equity_cost', 'last_price', 'day_price_change', 'day_percentage_change',
      'total_price_change', 'total_percentage_change', 'equity_worth',
      'equity_percentage', 'equity_idx'
    ]
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    positions = client.get_positions(force_live=live)
    position_by_instrument_id = {}
    for position in positions:
      quantity = int(float(position['quantity']))
      average_buy_price = Decimal(position['average_buy_price'])
      instrument_id = get_instrument_id_from_url(position['instrument'])
      instrument = client.get_instrument_by_id(instrument_id)
      fundamental = client.get_fundamental(instrument['symbol'], force_live=live)
      
      position_by_instrument_id[instrument_id] = {
        'quantity': quantity,
        'average_buy_price': average_buy_price,
        'equity_cost': quantity * average_buy_price,
        'symbol': instrument['symbol'],
        'simple_name': instrument['simple_name'],
        'full_name': instrument['name'],
        'last_open': Decimal(fundamental['open']),
      }

    position_quotes = client.get_quotes(symbols=[p['symbol'] for p in position_by_instrument_id.values()])
    for quote in position_quotes:
      instrument_id = get_instrument_id_from_url(quote['instrument'])
      position = position_by_instrument_id[instrument_id]

      position['last_price'] = Decimal(quote['last_trade_price'])
      position['equity_worth'] = position['quantity'] * position['last_price']

    total_equity = sum(position['equity_worth'] for position in position_by_instrument_id.values())

    positions_by_equity_worth = sorted(
      position_by_instrument_id.values(),
      key=lambda p: p['equity_worth'],
      reverse=True)

    for idx, position in enumerate(positions_by_equity_worth):
      total_price_change = position['last_price'] - position['average_buy_price']
      day_price_change = position['last_price'] - position['last_open']
      day_percentage_change = day_price_change * 100 / position['last_open']
      total_percentage_change = total_price_change * 100 / position['average_buy_price'] if position['average_buy_price'] else 100
      csv_writer.writerow({
        'symbol': position['symbol'],
        'short_name': position['simple_name'],
        'full_name': position['full_name'],
        'quantity': position['quantity'],
        'average_buy_price': round(position['average_buy_price'], 2),
        'equity_cost': round(position['equity_cost'], 2),
        'last_price': round(position['last_price'], 2),
        'day_price_change': round(day_price_change, 2),
        'day_percentage_change': round(day_percentage_change, 2),
        'total_price_change': round(total_price_change, 2),
        'total_percentage_change': round(total_percentage_change, 2),
        'equity_worth': round(position['equity_worth'], 2),
        'equity_percentage': round(position['equity_worth'] * 100 / total_equity, 2),
        'equity_idx': idx + 1,
      })


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Download a snapshot of your portfolio')
  parser.add_argument('--live', action='store_true', help='Force to not use cache for APIs where values change')
  args = parser.parse_args()
  generate_portfolio(args.live)
