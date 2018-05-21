#!/usr/bin/env python3

import argparse
import csv

#import logging
#logging.basicConfig(level=logging.DEBUG)

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, CACHE_FIRST, FORCE_LIVE
from robinhood.RobinhoodPortfolio import RobinhoodPortfolio

# Set up the client
client = RobinhoodCachedClient()
client.login()


def download_portfolio(cache_mode):
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

    portfolio = RobinhoodPortfolio(client, {'cache_mode': cache_mode})

    for idx, position in enumerate(portfolio.positions_by_equity_worth):
      csv_writer.writerow({
          'symbol': position['symbol'],
          'name': position['shortest_name'],
          'quantity': position['quantity'],
          'average_buy_price': round(position['average_buy_price'], 2),
          'equity_cost': round(position['equity_cost'], 2),
          'last_price': round(position['last_price'], 2),
          'day_price_change': round(position['day_price_change'], 2),
          'day_percentage_change': round(position['day_percentage_change'], 2),
          'total_price_change': round(position['total_price_change'], 2),
          'total_percentage_change': round(position['total_percentage_change'], 2),
          'equity_worth': round(position['equity_worth'], 2),
          'equity_percentage': round(position['equity_percentage'], 2),
          'equity_idx': idx + 1,
          'buy_rating': position['buy_rating'],
          'sell_rating': position['sell_rating'],
          'robinhood_holders': position['robinhood_holders'],
      })


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Download a snapshot of your portfolio')
  parser.add_argument(
      '--live',
      action='store_true',
      help='Force to not use cache for APIs where values change'
  )
  args = parser.parse_args()
  download_portfolio(FORCE_LIVE if args.live else CACHE_FIRST)
