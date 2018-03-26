#!/usr/bin/env python3

from decimal import Decimal
import argparse
import csv

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient
from robinhood.util import get_last_id_from_url

# Set up the client
client = RobinhoodCachedClient()
client.login()


def download_portfolio(live):
  with open('portfolio.csv', 'w', newline='') as csv_file:
    fieldnames = [
      'symbol',
      'name',
      'quantity',
      'average_buy_price',
      'equity_cost',
      'last_price',
      'day_price_change',
      'day_percentage_change',
      'total_price_change',
      'total_percentage_change',
      'equity_worth',
      'equity_percentage',
      'equity_idx',
      'robinhood_holders',
      'buy_rating',
      'sell_rating',
    ]
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    positions = client.get_positions(force_live=live)
    position_by_instrument_id = {}
    for position in positions:
      quantity = int(float(position['quantity']))
      average_buy_price = Decimal(position['average_buy_price'])
      instrument_id = get_last_id_from_url(position['instrument'])

      position_by_instrument_id[instrument_id] = {
        'quantity': quantity,
        'average_buy_price': average_buy_price,
        'equity_cost': quantity * average_buy_price,
      }

    instrument_ids = list(position_by_instrument_id.keys())
    instruments = client.get_instruments(instrument_ids=instrument_ids)
    for instrument in instruments['results']:
      instrument_id = instrument['id']
      position_by_instrument_id[instrument_id]['symbol'] = instrument['symbol']
      position_by_instrument_id[instrument_id]['simple_name'] = instrument['simple_name']
      position_by_instrument_id[instrument_id]['full_name'] = instrument['name']

    symbols = [p['symbol'] for p in position_by_instrument_id.values()]

    fundamentals = client.get_fundamentals(symbols)
    for fundamental in fundamentals:
      instrument_id = get_last_id_from_url(fundamental['instrument'])
      position_by_instrument_id[instrument_id]['last_open'] = Decimal(fundamental['open'])

    popularities = client.get_popularities(instrument_ids)
    for popularity in popularities:
      instrument_id = get_last_id_from_url(popularity['instrument'])
      position_by_instrument_id[instrument_id]['robinhood_holders'] = popularity['num_open_positions']

    ratings = client.get_ratings(instrument_ids)
    for rating in ratings:
      instrument_id = rating['instrument_id']
      num_ratings = sum(v for _, v in rating['summary'].items()) if rating['summary'] else None
      if num_ratings:
        percent_buy = rating['summary']['num_buy_ratings'] * 100 / num_ratings
        percent_sell = rating['summary']['num_sell_ratings']  * 100 / num_ratings
      position_by_instrument_id[instrument_id]['buy_rating'] = 'N/A' if not num_ratings else percent_buy
      position_by_instrument_id[instrument_id]['sell_rating'] = 'N/A' if not num_ratings else percent_sell

    position_quotes = client.get_quotes(symbols=symbols)
    for quote in position_quotes:
      instrument_id = get_last_id_from_url(quote['instrument'])
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
        'name': position['simple_name'] or position['full_name'],
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
        'buy_rating': position['buy_rating'],
        'sell_rating': position['sell_rating'],
        'robinhood_holders': position['robinhood_holders'],
      })


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Download a snapshot of your portfolio')
  parser.add_argument('--live', action='store_true', help='Force to not use cache for APIs where values change')
  args = parser.parse_args()
  download_portfolio(args.live)
