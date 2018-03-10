#!/usr/bin/env python3

from decimal import Decimal
import argparse
import json

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient
from robinhood.util import get_last_id_from_url

# Set up the client
client = RobinhoodCachedClient()
client.login()


def show_potentials(live):
  # First, get the portfolio
  positions = client.get_positions(force_live=live)
  position_by_instrument_id = {}
  symbol_to_instrument_id = {}
  for position in positions:
    quantity = int(float(position['quantity']))
    average_buy_price = Decimal(position['average_buy_price'])
    instrument_id = get_last_id_from_url(position['instrument'])
    instrument = client.get_instrument_by_id(instrument_id)
    fundamental = client.get_fundamental(instrument['symbol'], force_live=live)
    symbol_to_instrument_id[instrument['symbol']] = instrument_id

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
    instrument_id = get_last_id_from_url(quote['instrument'])
    position = position_by_instrument_id[instrument_id]

    position['last_price'] = Decimal(quote['last_trade_price'])
    position['equity_worth'] = position['quantity'] * position['last_price']

  # Next, augment with sentiment.
  with open('sentiment.json', 'r') as sentiment_file:
    sentiment_json = json.load(sentiment_file)
  for symbol, symbol_sentiment in sentiment_json.items():
    instrument_id = symbol_to_instrument_id[symbol]
    position = position_by_instrument_id[instrument_id]
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

      equity_needed = equity_target
      # How many needed
    position['paused'] = symbol_sentiment.get('paused', False)

  positions_by_priority = sorted(position_by_instrument_id.values(), key=lambda p: p.get('priority', 999))
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

  # Discounted (below buy in price)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Show various position potentials to buy into')
  parser.add_argument('--live', action='store_true', help='Force to not use cache for APIs where values change')
  args = parser.parse_args()
  show_potentials(args.live)
