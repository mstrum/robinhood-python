#!/usr/bin/env python3

from decimal import Decimal
import argparse
import json

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, FORCE_LIVE
from robinhood.util import ORDER_TYPES, ORDER_SIDES, OPTIONS_TYPES, ORDER_SIDE_TO_DIRECTION

# Set up the client
client = RobinhoodCachedClient()
client.login()


def place_order(order_type, order_side, symbol, date, strike, options_type, quantity, price):
  try:
    instrument = client.get_instrument_by_symbol(symbol)
  except NotFound:
    print('symbol {} was not found'.format(symbol))
    exit()
  else:
    instrument_id = instrument['id']
    name = instrument['simple_name'] or instrument['name']
  account_url = client.get_account()['url']

  options_chains = [c for c in client.get_options_chains(instrument_ids=[instrument_id]) if c['can_open_position']]
  if len(options_chains) != 1:
    raise Exception('Expected exactly one options chains listing, but got: {}'.format(json.dumps(options_chains, indent=4)))
  options_chain = options_chains[0]

  if len(options_chain['underlying_instruments']) != 1:
    raise Exception('Expected exactly one underlying instrument, but got: {}'.format(json.dumps(options_chain, indent=4)))
  if not options_chain['can_open_position']:
    raise Exception("Can't open position: {}".format(json.dumps(options_chain, indent=4)))
  chain_id = options_chain['id']
  options_instrument_id = options_chain['underlying_instruments'][0]['id']
  multiplier = Decimal(options_chain['trade_value_multiplier'])

  options_instruments = client.get_options_instruments(
      chain_id=chain_id, options_type=options_type, tradability='tradable', state='active', expiration_dates=[date])
  if not options_instruments:
    raise Exception('No options found on that date')

  options_instrument = None
  for potential_options_instrument in options_instruments:
    potential_strike = float(potential_options_instrument['strike_price'])
    if potential_strike == strike:
      options_instrument = potential_options_instrument
      break
  if not options_instrument:
    raise Exception('No options found at that strike price')

  options_quote = client.get_options_marketdata(options_instrument['id'])

  print('')
  print('!!!!!!!!!!!!!!!!!! CAUTION !!!!!!!!!!!!!!!!!!')
  confirm = input('Are you sure that you want to {} {} {} {} ${:.2f} {} options of {} ({}) for ${:.2f} each? [N/y]? '.format(
      order_type,
      order_side,
      quantity,
      date,
      strike,
      options_type,
      symbol,
      instrument['simple_name'] or instrument['name'],
      price)).lower()
  if confirm not in ['y', 'yes']:
    print('Bailed out!')
    exit()

  order = client.order_options(
      options_instrument['id'], order_type, ORDER_SIDE_TO_DIRECTION[order_side], quantity, price, use_account_url=account_url)
  print(json.dumps(order, indent=4))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Place an order')
  parser.add_argument('order_type', choices=ORDER_TYPES)
  parser.add_argument('order_side', choices=ORDER_SIDES)
  parser.add_argument('symbol', type=str.upper, help='The stock ticker')
  parser.add_argument('date', type=str, help='Date for the options to expire')
  parser.add_argument('strike', type=float, help='Amount the strike price should be')
  parser.add_argument('options_type', choices=OPTIONS_TYPES)
  parser.add_argument('quantity', type=int)
  parser.add_argument('price', type=float)
  args = parser.parse_args()
  place_order(
      args.order_type,
      args.order_side,
      args.symbol,
      args.date,
      args.strike,
      args.options_type,
      args.quantity,
      args.price
  )

