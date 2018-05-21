from decimal import Decimal

from robinhood.util import get_last_id_from_url


class RobinhoodPortfolio:
  """Class to help with working with a portfolio as a whole."""
  def __init__(self, client, client_kwargs):
    """Gather info together to represent the portfolio."""
    # Start off by getting all of the current positions.
    positions = client.get_positions(**client_kwargs)
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

    # Augment with instruments.
    instrument_ids = list(position_by_instrument_id.keys())
    instruments = client.get_instruments(instrument_ids)
    for instrument in instruments:
      instrument_id = instrument['id']
      position_by_instrument_id[instrument_id]['symbol'] = instrument['symbol']
      position_by_instrument_id[instrument_id]['simple_name'] = instrument['simple_name']
      position_by_instrument_id[instrument_id]['full_name'] = instrument['name']
      position_by_instrument_id[instrument_id]['shortest_name'] = instrument['simple_name'] or instrument['name'] 

    # Augment with popularities.
    popularities = client.get_popularities(instrument_ids, **client_kwargs)
    for popularity in popularities:
      instrument_id = get_last_id_from_url(popularity['instrument'])
      position_by_instrument_id[instrument_id]['robinhood_holders'] = popularity['num_open_positions']

    # Augment with ratings.
    ratings = client.get_ratings(instrument_ids, **client_kwargs)
    for rating in ratings:
      instrument_id = rating['instrument_id']
      num_ratings = sum(v for _, v in rating['summary'].items()) if rating['summary'] else None
      if num_ratings:
        percent_buy = rating['summary']['num_buy_ratings'] * 100 / num_ratings
        percent_sell = rating['summary']['num_sell_ratings']  * 100 / num_ratings
      position_by_instrument_id[instrument_id]['buy_rating'] = 'N/A' if not num_ratings else '{:.2f}'.format(percent_buy)
      position_by_instrument_id[instrument_id]['sell_rating'] = 'N/A' if not num_ratings else '{:.2f}'.format(percent_sell)

    # Augment with quotes.
    position_quotes = client.get_quotes(instrument_ids, **client_kwargs)
    for quote in position_quotes:
      instrument_id = get_last_id_from_url(quote['instrument'])
      position = position_by_instrument_id[instrument_id]

      position['last_price'] = Decimal(quote['last_trade_price'])
      position['equity_worth'] = position['quantity'] * position['last_price']
      position['previous_close'] = Decimal(quote['previous_close'])

    # Store some common calculations
    total_equity = sum(position['equity_worth'] for position in position_by_instrument_id.values())
    for position in position_by_instrument_id.values():
      position['equity_percentage'] = position['equity_worth'] * 100 / total_equity
      position['total_price_change'] = position['last_price'] - position['average_buy_price']
      position['day_price_change'] = position['last_price'] = - position['previous_close']
      position['day_percentage_change'] = position['day_price_change'] * 100 / position['previous_close']
      position['total_percentage_change'] = position['total_price_change']  * 100 / position['average_buy_price'] if position['average_buy_price'] else 100

    positions_by_equity_worth = sorted(
        position_by_instrument_id.values(),
        key=lambda p: p['equity_worth'],
        reverse=True
    )

    self.total_equity = total_equity
    self.positions_by_equity_worth = positions_by_equity_worth
    self.position_by_instrument_id = position_by_instrument_id
    self.symbol_to_instrument_id = {position['symbol']: instrument_id for instrument_id, position in position_by_instrument_id.items()}

  @property
  def symbols(self):
    return self.symbol_to_instrument_id.keys()

  @property
  def instrument_ids(self):
    return self.position_by_instrument_id.keys()

  @property
  def positions(self):
    return self.positions_by_equity_worth

  def get_position_for_symbol(self, symbol):
    instrument_id = self.symbol_to_instrument_id[symbol]
    position = self.position_by_instrument_id[instrument_id]
    return position
