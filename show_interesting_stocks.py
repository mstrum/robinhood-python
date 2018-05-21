#!/usr/bin/env python3

from decimal import Decimal

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, FORCE_LIVE
from robinhood.util import get_last_id_from_url

client = RobinhoodCachedClient()
client.login()


def display_popular_stocks():
  popular_stocks = client.get_popular_stocks()['data']

  print('')
  print('----------------- Popular S&P 500 Stocks With Robinhood Traders -----------------')
  for popular_stock in popular_stocks:
    print('{}\t({})'.format(popular_stock['symbol'], popular_stock['subtitle']))


def display_sp500_movers():
  print('')
  print('----------------- Top S&P 500 Movers -----------------')
  for direction in ['up', 'down']:
    extra_percentage_symbol = '+' if direction == 'up' else ''
    movers = client.get_sp500_movers(direction, cache_mode=FORCE_LIVE)
    if direction == 'down':
      movers.reverse()

    
    instruments = client.get_instruments([get_last_id_from_url(mover['instrument_url']) for mover in movers])
    instruments_by_id = {i['id']: i for i in instruments}

    for mover in movers:
      last_price = Decimal(mover['price_movement']['market_hours_last_price'])
      movement_pct = Decimal(mover['price_movement']['market_hours_last_movement_pct'])
      instrument = instruments_by_id[get_last_id_from_url(mover['instrument_url'])]

      print('${:.2f}\t({}{}%)\t{}\t({})'.format(
        last_price, extra_percentage_symbol, movement_pct, instrument['symbol'], instrument['simple_name'] or instrument['name']))


def display_for_you():
  print('')
  print('----------------- Stocks For You -----------------')
  reasons =  client.get_instrument_reasons_for_personal_tag('for-you')
  for reason in reasons:
    print('{}\t{}'.format(reason['symbol'], reason['reason']))

def display_top_movers():
  print('')
  print('----------------- Top Movers -----------------')
  instrument_ids =  client.get_instrument_ids_for_tag('top-movers', cache_mode=FORCE_LIVE)
  instruments = client.get_instruments(instrument_ids)
  for instrument in instruments:
    print('{}\t{}'.format(instrument['symbol'], instrument['simple_name'] or instrument['name']))

def display_100_most_popular():
  print('')
  print('----------------- 100 Most Popular Stocks With Robinhood Users -----------------')
  instrument_ids =  client.get_instrument_ids_for_tag('100-most-popular', cache_mode=FORCE_LIVE)
  instruments = client.get_instruments(instrument_ids)
  for instrument in instruments:
    print('{}\t{}'.format(instrument['symbol'], instrument['simple_name'] or instrument['name']))


if __name__ == '__main__':
  display_popular_stocks()
  display_sp500_movers()
  display_top_movers()
  display_for_you()
  display_100_most_popular()
  print('')
