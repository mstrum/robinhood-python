#!/usr/bin/env python3

import argparse
from datetime import datetime
from decimal import Decimal
from math import ceil

from dateutil.parser import parse
import pytz

from robinhood.exceptions import NotFound
from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, CACHE_FIRST, FORCE_LIVE

def display_quote(client, symbol, cache_mode):
  now = datetime.now(pytz.UTC)
  # Get instrument parts
  try:
    instrument = client.get_instrument_by_symbol(symbol)
  except NotFound:
    print('symbol {} was not found'.format(symbol))
    exit()
  else:
    instrument_id = instrument['id']
    listed_since = parse(instrument['list_date']).date()
    tradable = instrument['tradeable']
    simple_name = instrument['simple_name']

  # Get fundamentals
  fundamental = client.get_fundamental(instrument_id, cache_mode=cache_mode)
  founded_year = fundamental['year_founded']
  high_52 = Decimal(fundamental['high_52_weeks']) if fundamental['high_52_weeks'] else None
  low_52 = Decimal(fundamental['low_52_weeks']) if fundamental['low_52_weeks'] else None
  last_open = Decimal(fundamental['open'])
  last_high = Decimal(fundamental['high'])
  last_low = Decimal(fundamental['low'])
  pe_ratio = Decimal(fundamental['pe_ratio']) if fundamental['pe_ratio'] else 0.0
  dividend_yield = Decimal(fundamental['dividend_yield']) if fundamental['dividend_yield'] else 0.0

  num_open_positions = client.get_popularity(instrument_id, cache_mode=cache_mode)['num_open_positions']
  ratings = client.get_rating(instrument_id, cache_mode=cache_mode)['summary']
  num_ratings = sum(v for _, v in ratings.items()) if ratings else None
  if num_ratings:
    percent_buy = ratings['num_buy_ratings'] * 100 / num_ratings
    percent_sell = ratings['num_sell_ratings']  * 100 / num_ratings

  print('==================== {} ({}) ===================='.format(symbol, simple_name))
  if not tradable:
    print('!!!!!!!!!!!!! NOT TRADEABLE !!!!!!!!!!!!!')
  print('founded {} ... listed {}'.format(founded_year, listed_since.year))

  print('---------------- sentiment ----------------')
  print('# ratings:\t{}'.format(num_ratings))
  if num_ratings:
    print('Buy:\t{:.2f}%'.format(percent_buy))
    print('Sell:\t{:.2f}%'.format(percent_sell))
  print('RH holders:\t{}'.format(num_open_positions))

  print('')
  print('---------------- recents ----------------')
  print('dy:\t{:.2f}%'.format(dividend_yield))
  print('pe:\t{:.2f}x'.format(pe_ratio))
  if high_52:
    year_spread = high_52 - low_52
    print('52w:\t${:.2f} <-> ${:.2f} (spread is ${:.2f} / {:.2f}%)'.format(low_52, high_52, year_spread, (year_spread) * 100 / high_52))
  day_spread = last_high - last_low
  print('1d:\topen ${:.2f} ... ${:.2f} <-> ${:.2f} (spread is ${:.2f} / ${:.2f}%) '.format(last_open, last_low, last_high, day_spread, (day_spread) * 100 / last_high))

  print('')
  print('---------------- position ----------------')

  # Get position
  try:
    position = client.get_position_by_instrument_id(instrument_id, cache_mode=cache_mode)
  except NotFound:
    position_average_buy_price = 0
    position_quantity = 0
    position_equity_cost = 0
    print('None')
  else:
    position_quantity = int(float(position['quantity']))
    if not position_quantity:
      print('None anymore')
    else:
      position_average_buy_price = Decimal(position['average_buy_price'])
      position_equity_cost = position_quantity * position_average_buy_price
      print('{} @ ${:.2f} = ${:.2f}'.format(position_quantity, position_average_buy_price, position_equity_cost))

  # Get order history, put as a subdisplay of position
  print('')
  print('\t-------------- orders --------------')
  orders = client.get_orders(instrument_id=instrument_id, cache_mode=cache_mode)
  if len(orders) == 0:
    print('\tNone')
  else:
    for order in orders:
      order_state = order['state']
      order_type = order['type']
      order_side = order['side']
      order_quantity = int(float(order['quantity']))
      order_price = Decimal(order['average_price']) if order['average_price'] else Decimal(order['price'])
      order_last_executed_at = parse(order['last_transaction_at']).date()
      print('\t{:%m/%d/%Y}\t{}\t{} {}\t{} @ ${:.2f}'.format(order_last_executed_at, order_state, order_type, order_side, order_quantity, order_price))

  # Get quote
  quote = client.get_quote(instrument_id, cache_mode=cache_mode)
  updated_at = parse(quote['updated_at'])
  updated_minutes_ago = ceil((now - updated_at).total_seconds() / 60)
  has_traded = quote['has_traded']
  trading_halted = quote['trading_halted']
  last_close_price = Decimal(quote['previous_close'])
  last_close_date = parse(quote['previous_close_date']).date()
  last_extended_hours_trade_price = Decimal(quote['last_extended_hours_trade_price']) if quote['last_extended_hours_trade_price'] else last_close_price
  last_trade_price = Decimal(quote['last_trade_price'])
  bid_price = Decimal(quote['bid_price'])
  bid_size = int(quote['bid_size'])
  ask_price = Decimal(quote['ask_price'])
  ask_size = int(quote['ask_size'])

  print('')
  print('---------------- quote ----------------')
  if trading_halted:
    print('!!!!!!!!!!!!! HALTED !!!!!!!!!!!!!')
  if not has_traded:
    print('!!!!!!!!!!!!! HAS NOT TRADED !!!!!!!!!!!!!')
  print('close\t${:.2f} on {:%b %d}'.format(last_close_price, last_close_date))
  extended_hours_spread = last_extended_hours_trade_price - last_close_price
  print('extnd:\t${:.2f} (${:.2f} / {:.2f}% spread)'.format(last_extended_hours_trade_price, extended_hours_spread, (last_extended_hours_trade_price - last_close_price) * 100 / last_close_price))
  print('spread:\t${:.2f} ({}) <-> ${:.2f} ({})'.format(bid_price, bid_size, ask_price, ask_size))
  bid_spread = ask_price - bid_price
  print('\t${:.2f} ({:.2f}%)'.format(bid_spread, bid_spread * 100 / last_trade_price))
  print('last:\t${:.2f} ({:.2f}% within spread)'.format(last_trade_price, (bid_spread - (ask_price - last_trade_price)) * 100 / bid_spread))
  print('age:\t{}m ago @ {:%I:%M%p}'.format(updated_minutes_ago, updated_at.astimezone(pytz.timezone('US/Pacific'))))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Get a quote for a symbol')
  parser.add_argument('symbol', type=str.upper, help='A symbol to get a quote on')
  parser.add_argument(
      '--live',
      action='store_true',
      help='Force to not use cache for APIs where values change'
  )
  args = parser.parse_args()

  client = RobinhoodCachedClient()
  client.login()
  display_quote(client, args.symbol, FORCE_LIVE if args.live else CACHE_FIRST)
