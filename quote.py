import argparse
from datetime import datetime
from decimal import Decimal
from math import ceil
from pathlib import Path
import configparser
import json

from dateutil.parser import parse
import click
import pytz

from robinhood.RobinhoodClient import RobinhoodClient, NoPositionFound

# Set up the client
client = RobinhoodClient()

# Get an auth token
config = configparser.ConfigParser()
config.read([str(Path.home() / '.robinhood' / 'credentials')])
client.set_auth_token_with_credentials(
  config['account']['RobinhoodUsername'],
  config['account']['RobinhoodPassword']
)
account_number = config['account'].get('RobinhoodAccountNumber')


def get_quote(symbol):
  now = datetime.now(pytz.UTC)
  try:
    global account_number
    if not account_number:
      account = client.get_account()
      account_number = account['account_number']

    # Get instrument parts
    instrument = client.get_instrument_by_symbol(symbol)
    instrument_id = instrument['id']
    instrument_url = instrument['url']
    listed_since = parse(instrument['list_date']).date()
    tradable = instrument['tradeable']
    simple_name = instrument['simple_name']

    # Get fundamentals
    fundamental = client.get_fundamental(symbol)
    founded_year = fundamental['year_founded']
    high_52 = Decimal(fundamental['high_52_weeks'])
    low_52 = Decimal(fundamental['low_52_weeks'])
    last_open = Decimal(fundamental['open'])
    last_high = Decimal(fundamental['high'])
    last_low = Decimal(fundamental['low'])
    pe_ratio = Decimal(fundamental['pe_ratio']) if fundamental['pe_ratio'] else None
    dividend_yield = Decimal(fundamental['dividend_yield'])

    print('==================== {} ({}) ===================='.format(symbol, simple_name))
    if not tradable:
      print('!!!!!!!!!!!!! NOT TRADEABLE !!!!!!!!!!!!!')
    print('founded {} ... listed {}'.format(founded_year, listed_since.year))

    print()
    print('---------------- recents ----------------')
    print('dy\t{:.2f}%\t\tpe\t{:.2f}x'.format(dividend_yield, pe_ratio))
    print('52w\t${:.2f} <-> ${:.2f}'.format(low_52, high_52))
    print('1d\t${:.2f} <-> ${:.2f} (from ${:.2f})'.format(last_low, last_high, last_open))

    print()
    print('---------------- position ----------------')

    # Get position
    try:
      position = client.get_position_by_instrument_id(account_number, instrument_id)
    except NoPositionFound:
      position_average_buy_price = 0
      position_quantity = 0
      position_equity = 0
      print('None')
    else:
      position_average_buy_price = Decimal(position['average_buy_price'])
      position_quantity = int(float(position['quantity']))
      position_equity = position_quantity * position_average_buy_price
      print('{} @ ${:.2f} = ${:.2f}'.format(position_quantity, position_average_buy_price, position_equity))

    # Get order history, put as a subdisplay of position
    print()
    print('\t------------ orders ------------')
    orders = client.get_orders(instrument_url)
    assert not orders['next']
    if len(orders['results']) == 0:
      print('\tNone')
    else:
      for order in orders['results']:
        if order['state'] in ['cancelled', 'failed', 'rejected']:
          continue
        if order['state'] != 'filled':
          raise Exception('Not filled?')
        order_type = order['type']
        assert len(order['executions']) == 1
        for execution in order['executions']:
          execution_price = Decimal(execution['price'])
          execution_quantity = int(float(execution['quantity']))
          execution_date = parse(execution['settlement_date']).date()
        print('\t{:%m/%d/%Y}\t{}\t{} @ ${:.2f}'.format(execution_date, order_type, execution_quantity, execution_price))

    # Get quote
    quote = client.get_quote(symbol)
    updated_at = parse(quote['updated_at'])
    updated_minutes_ago = ceil((now - updated_at).total_seconds() / 60)
    has_traded = quote['has_traded']
    trading_halted = quote['trading_halted']
    last_close_price = Decimal(quote['previous_close'])
    last_close_date = parse(quote['previous_close_date']).date()
    last_extended_hours_trade_price = Decimal(quote['last_extended_hours_trade_price'])
    last_trade_price = Decimal(quote['last_trade_price'])
    bid_price = Decimal(quote['bid_price'])
    bid_size = int(quote['bid_size'])
    ask_price = Decimal(quote['ask_price'])
    ask_size = int(quote['ask_size'])

    print()
    print('---------------- quote ----------------')
    if trading_halted:
      print('!!!!!!!!!!!!! HALTED !!!!!!!!!!!!!')
    if not has_traded:
      print('!!!!!!!!!!!!! HAS NOT TRADED !!!!!!!!!!!!!')
    print('{} @ ${:.2f} <-> {} @ ${:.2f} (last {:.2f})'.format(bid_size, bid_price, ask_size, ask_price, last_trade_price))
    print('\t{}m ago @ {:%I:%M%p}'.format(updated_minutes_ago, updated_at.astimezone(pytz.timezone('US/Pacific'))))
    print('\tlast close ${:.2f} on {:%b %d} (ext ${:.2f})'.format(last_close_price, last_close_date, last_extended_hours_trade_price))

  finally:
    client.clear_auth_token()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Get a quote for a symbol')
  parser.add_argument('symbol', help='A symbol to get a quote on')
  args = parser.parse_args()
  get_quote(args.symbol)
