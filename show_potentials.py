#!/usr/bin/env python3

from decimal import Decimal
import argparse
import json

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, CACHE_FIRST, FORCE_LIVE
from robinhood.RobinhoodPortfolio import RobinhoodPortfolio

# Set up the client
client = RobinhoodCachedClient()
client.login()


def show_potentials(cache_mode):
  # Load the portfolio
  portfolio = RobinhoodPortfolio(client, {'cache_mode': cache_mode})

  # Load the sentiment
  with open('sentiment.json', 'r') as sentiment_file:
    sentiment_json = json.load(sentiment_file)

  # Augment the portfolio with sentiment
  for symbol, symbol_sentiment in sentiment_json.items():
    position = portfolio.get_position_for_symbol(symbol)
    assert 'sentiment' not in position
    position['sentiment'] = symbol_sentiment

    position['category'] = symbol_sentiment.get('category', 'N/A')
    position['priority'] = symbol_sentiment.get('priority', 99)
    if 'equity_target' in symbol_sentiment:
      equity_target = symbol_sentiment['equity_target']
      position['equity_target'] = equity_target
      equity_left = equity_target - position['equity_worth']
      if equity_left <= 0:
        position['equity_left'] = 0
        position['shares_needed'] = 0
      else:
        position['equity_left'] = equity_left
        position['shares_needed'] = equity_left / position['last_price']
    position['paused'] = symbol_sentiment.get('paused', False)

  positions_by_priority = sorted(portfolio.positions, key=lambda p: p.get('priority', 999))
  print('pri\tsym\teq_tot\tlast\twrth\ttrgt\tlft\tsh\tcat')
  for position in positions_by_priority:
    if position.get('paused'):
      continue
    print('{}\t{}\t{:.2f}\t{:.2f}\t{:.2f}\t{}\t{:.2f}\t{:.2f}\t{}'.format(
        position.get('priority', 'N/A'),
        position['symbol'],
        position['equity_cost'],
        position['last_price'],
        position['equity_worth'],
        position.get('equity_target', 'N/A'),
        position.get('equity_left', 0),
        position.get('shares_needed', 0),
        position.get('category')
    ))

  # TODO: Discounted (below buy in price)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Show various position potentials to buy into')
  parser.add_argument(
      '--live',
      action='store_true',
      help='Force to not use cache for APIs where values change'
  )
  args = parser.parse_args()
  show_potentials(FORCE_LIVE if args.live else CACHE_FIRST)
