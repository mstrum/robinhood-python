"""
NOTE: APIs and HTTP flow taken from:
https://github.com/Jamonek/Robinhood

More API documentation available at:
https://github.com/sanko/Robinhood
"""

import json

import requests


API_HOST = 'https://api.robinhood.com/'


class NotFound(Exception):
    pass


class RobinhoodClient:
  def __init__(self):
    self._session = requests.Session()
    self._session.headers = {
      'Accept': '*/*',
      'Accept-Encoding': 'gzip, deflate',
      'Accept-Language': 'en;q=1',
      'Content-type': 'application/x-www-form-urlencoded; charset=utf-8',
      'X-Robinhood-API-Version': '1.0.0',
      'Connection': 'keep-alive',
      'User-Agent': 'Robinhood/823 (iPhone; iOS 7.1.2; Scale/2.00)',
    }

  def set_auth_token(self, auth_token):
    self._session.headers['Authorization'] = 'Token {}'.format(auth_token)

  def set_auth_token_with_credentials(self, username, password):
    body = {
      'username': username,
      'password': password,
    }
    response = self._session.post(API_HOST + 'api-token-auth/', data=body)
    response.raise_for_status()
    auth_token = response.json()['token']
    self.set_auth_token(auth_token)
    return auth_token

  def clear_auth_token(self):
    response = self._session.post(API_HOST + 'api-token-logout/')
    response.raise_for_status()
    del self._session.headers['Authorization']

  def get_referral_code(self):
    """
    Example response:
    {
        "code": "matts952",
        "user_id": "00000000-0000-4000-0000-000000000000",
        "url": "https://share.robinhood.com/matts952"
    }
    """
    response = self._session.get(API_HOST + 'midlands/referral/code/')
    response.raise_for_status()
    return response.json()

  def get_markets(self):
    """
    Example response:
    {
        "previous": null,
        "results": [
            {
                "operating_mic": "OTCM",
                "mic": "OTCM",
                "url": "https://api.robinhood.com/markets/OTCM/",
                "timezone": "US/Eastern",
                "name": "Otc Markets",
                "city": "New York",
                "website": "www.otcmarkets.com",
                "acronym": "OTCM",
                "country": "United States of America",
                "todays_hours": "https://api.robinhood.com/markets/OTCM/hours/2018-03-02/"
            },
            ...
        ],
        "next": null
    }
    """
    response = self._session.get(API_HOST + 'markets/')
    response.raise_for_status()
    return response.json()

  def get_watchlists(self):
    """
    Example response:
    {
        "results": [
            {
                "name": "Default",
                "user": "https://api.robinhood.com/user/",
                "url": "https://api.robinhood.com/watchlists/Default/"
            }
        ],
        "previous": null,
        "next": null
    }
    """
    response = self._session.get(API_HOST + 'watchlists/')
    response.raise_for_status()
    return response.json()

  def get_watchlist_instruments(self, watchlist_name):
    """
    Example response:
    {
        "previous": null,
        "next": null,
        "results": [
            {
                "created_at": "2018-02-05T22:58:18.267521Z",
                "instrument": "https://api.robinhood.com/instruments/81733743-965a-4d93-b87a-6973cb9efd34/",
                "watchlist": "https://api.robinhood.com/watchlists/Default/",
                "url": "https://api.robinhood.com/watchlists/Default/81733743-965a-4d93-b87a-6973cb9efd34/"
            },
            ....
            }
        ]
    }
  
    """
    response = self._session.get(API_HOST + 'watchlists/{}/'.format(watchlist_name))
    response.raise_for_status()
    return response.json()

  def get_notification_settings(self):
    """
    Example response:
    {
        "trading_email": true,
        "market_email": true,
        "transfers_email": true,
        "margin_email": true,
        "transfers": {
            "email_enabled": true,
            "push_enabled": true
        },
        "account_summary": {
            "email_enabled": true,
            "push_enabled": true,
            "frequency": "weekly"
        },
        "dividends": {
            "email_enabled": true,
            "push_enabled": true,
            "tracking": "watched",
            "timing": "all"
        },
        "margin_maintenance": {
            "email_enabled": true,
            "push_enabled": true,
            "maintenance_threshold": "close"
        },
        "orders": {
            "email_enabled": true,
            "push_enabled": true
        },
        "compliance_push": true,
        "margin_push": true,
        "lang": "en-us",
        "earnings": {
            "email_enabled": true,
            "push_enabled": true,
            "tracking": "watched"
        },
        "price_movements": {
            "email_enabled": true,
            "push_enabled": true,
            "tracking": "watched",
            "threshold": "5_pct"
        },
        "compliance_email": true,
        "corporate_actions": {
            "email_enabled": true,
            "push_enabled": true,
            "tracking": "watched",
            "timing": "all"
        },
        "user": "https://api.robinhood.com/user/",
        "transfers_push": true,
        "cash_transfers": {
            "email_enabled": true,
            "push_enabled": true
        },
        "trading_push": true,
        "market_push": true
    }
    """
    response = self._session.get(API_HOST + 'settings/notifications')
    response.raise_for_status()
    return response.json()

  def get_notification_devices(self):
    """
    Example response:
    {
        "previous": null,
        "results": [
            {
                "token": "XXX:XXX-XXXX",
                "identifier": "XXXX",
                "url": "https://api.robinhood.com/notifications/devices/00000000-0000-4000-0000-000000000000/",
                "id": "00000000-0000-4000-0000-000000000000",
                "type": "android"
            }
        ],
        "next": null
    }
    """
    response = self._session.get(API_HOST + 'notifications/devices/')
    response.raise_for_status()
    return response.json()

  def get_account(self):
    """
    Example response:
    {
        "cash_held_for_orders": "0.0000",
        "uncleared_deposits": "0.0000",
        "max_ach_early_access_amount": "0.00",
        "positions": "https://api.robinhood.com/accounts/XXXXXXXX/positions/",
        "cash_balances": null,
        "only_position_closing_trades": false,
        "user": "https://api.robinhood.com/user/",
        "withdrawal_halted": false,
        "account_number": "XXXXXXXX",
        "sweep_enabled": false,
        "deactivated": false,
        "unsettled_debit": "0.0000",
        "buying_power": "0.0000",
        "option_level": null,
        "can_downgrade_to_cash": "https://api.robinhood.com/accounts/XXXXXXXX/can_downgrade_to_cash/",
        "type": "margin",
        "portfolio": "https://api.robinhood.com/accounts/XXXXXXXX/portfolio/",
        "updated_at": "2018-02-01T00:00:00.000000Z",
        "sma": "0.0000",
        "unsettled_funds": "0.0000",
        "nummus_enabled": null,
        "cash_available_for_withdrawal": "0.0000",
        "created_at": "2018-02-01T00:00:00.000000Z",
        "url": "https://api.robinhood.com/accounts/XXXXXXXX/",
        "margin_balances": {
            "cash_held_for_orders": "0.0000",
            "uncleared_deposits": "0.0000",
            "overnight_buying_power": "0.0000",
            "outstanding_interest": "0.0000",
            "unallocated_margin_cash": "0.0000",
            "gold_equity_requirement": "0.0000",
            "overnight_ratio": "0.00",
            "unsettled_debit": "0.0000",
            "margin_limit": "0.0000",
            "day_trade_ratio": "0.00",
            "overnight_buying_power_held_for_orders": "0.0000",
            "cash_held_for_options_collateral": "0.0000",
            "updated_at": "2018-03-01T00:00:00.000000Z",
            "start_of_day_dtbp": "0.0000",
            "start_of_day_overnight_buying_power": "0.0000",
            "cash_available_for_withdrawal": "0.0000",
            "unsettled_funds": "0.0000",
            "created_at": "2018-02-05T23:41:03.011013Z",
            "cash": "-199.0700",
            "day_trade_buying_power": "17932.8345",
            "day_trade_buying_power_held_for_orders": "0.0000",
            "marked_pattern_day_trader_date": null
        },
        "cash": "0.0000",
        "instant_eligibility": {
            "state": "ok",
            "reason": "",
            "reinstatement_date": null,
            "updated_at": null,
            "reversal": null
        },
        "sma_held_for_orders": "0.0000",
        "deposit_halted": false
    }
    """
    response = self._session.get(API_HOST + 'accounts/')
    response.raise_for_status()
    return response.json()['results'][0]

  def get_investment_profile(self):
    """
    Example response:
    {
        "time_horizon": "short_time_horizon",
        "tax_bracket": "",
        "option_trading_experience": "",
        "liquidity_needs": "very_important_liq_need",
        "source_of_funds": "savings_personal_income",
        "total_net_worth": "0_9",
        "risk_tolerance": "high_risk_tolerance",
        "updated_at": "2018-02-01T00:00:00.000000Z",
        "liquid_net_worth": "0_9",
        "annual_income": "0_9",
        "suitability_verified": true,
        "investment_experience": "limited_investment_exp",
        "user": "https://api.robinhood.com/user/",
        "professional_trader": null,
        "investment_experience_collected": true,
        "investment_objective": "growth_invest_obj"
    }
    """
    response = self._session.get(API_HOST + 'user/investment_profile/')
    response.raise_for_status()
    return response.json()

  def get_top100_instruments(self):
    """
    Example response:
    {
        "slug": "100-most-popular",
        "description": "",
        "instruments": [
            "https://api.robinhood.com/instruments/3a47ca97-d5a2-4a55-9045-053a588894de/",
            ...
        ],
        "name": "100 Most Popular"
    }
    """
    response = self._session.get(API_HOST + 'midlands/tags/tag/100-most-popular/')
    response.raise_for_status()
    return response.json()

  def get_top10_instruments(self):
    """
    Example response:
    {
        "slug": "10-most-popular",
        "description": "",
        "instruments": [
            "https://api.robinhood.com/instruments/3a47ca97-d5a2-4a55-9045-053a588894de/",
            ...
        ],
        "name": "10 Most Popular"
    }
    """
    response = self._session.get(API_HOST + 'midlands/tags/tag/10-most-popular/')
    response.raise_for_status()
    return response.json()

  def get_instruments(self, query=None):
    """
    Args:
      query: Can be any string, like a stock ticker or None for all (e.g. AAPL)

    Example response for AAPL:
    {
        "next": null,
        "previous": null,
        "results": [
            {
                "day_trade_ratio": "0.2500",
                "type": "stock",
                "symbol": "AAPL",
                "simple_name": "Apple",
                "quote": "https://api.robinhood.com/quotes/AAPL/",
                "fundamentals": "https://api.robinhood.com/fundamentals/AAPL/",
                "state": "active",
                "list_date": "1990-01-02",
                "id": "00000000-0000-4000-0000-000000000000",
                "maintenance_ratio": "0.2500",
                "country": "US",
                "min_tick_size": null,
                "tradability": "tradable",
                "bloomberg_unique": "EQ0010169500001000",
                "market": "https://api.robinhood.com/markets/XNAS/",
                "margin_initial_ratio": "0.5000",
                "url": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/",
                "tradeable": true,
                "name": "Apple Inc. - Common Stock",
                "splits": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/splits/"
            }
        ]
    }

    Example response for <None>:
    {
        "results": [
            {
                "list_date": "2014-02-26",
                "simple_name": "Praetorian Property",
                "margin_initial_ratio": "1.0000",
                "min_tick_size": null,
                "splits": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/splits/",
                "name": "Praetorian Property, Inc. Common Stock",
                "quote": "https://api.robinhood.com/quotes/PRRE/",
                "bloomberg_unique": "EQ0000000021483725",
                "url": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/",
                "type": "stock",
                "tradeable": false,
                "country": "US",
                "fundamentals": "https://api.robinhood.com/fundamentals/PRRE/",
                "market": "https://api.robinhood.com/markets/OTCM/",
                "id": "00000000-0000-4000-0000-000000000000",
                "symbol": "PRRE",
                "tradability": "untradable",
                "day_trade_ratio": "1.0000",
                "state": "unlisted",
                "maintenance_ratio": "1.0000"
            },
            ...
        ],
        "previous": null,
        "next": "https://api.robinhood.com/instruments/?cursor=XXXXXXXX"
    }
    """
    params = {'query': query}
    response = self._session.get(API_HOST + 'instruments/', params=params)
    response.raise_for_status()
    return response.json()

  def get_instrument_by_id(self, instrument_id):
    """
    Args:
      instrument_id: Internal robinhood instrument id (a uuid)

    Example response:
    {
        "tradability": "untradable",
        "type": "stock",
        "bloomberg_unique": "EQ0000000021483725",
        "list_date": "2014-02-26",
        "min_tick_size": null,
        "quote": "https://api.robinhood.com/quotes/PRRE/",
        "state": "unlisted",
        "market": "https://api.robinhood.com/markets/OTCM/",
        "symbol": "PRRE",
        "maintenance_ratio": "1.0000",
        "url": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/",
        "country": "US",
        "splits": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/splits/",
        "id": "00000000-0000-4000-0000-000000000000",
        "margin_initial_ratio": "1.0000",
        "tradeable": false,
        "fundamentals": "https://api.robinhood.com/fundamentals/PRRE/",
        "day_trade_ratio": "1.0000",
        "simple_name": "Praetorian Property",
        "name": "Praetorian Property, Inc. Common Stock"
    }
    """
    response = self._session.get(API_HOST + 'instruments/{}/'.format(instrument_id))
    response.raise_for_status()
    return response.json()

  def get_instrument_by_symbol(self, symbol):
    """
    Args:
      symbol: e.g. AAPL

    Example response:
    {
        "next": null,
        "results": [
            {
                "country": "US",
                "min_tick_size": null,
                "bloomberg_unique": "EQ0010169500001000",
                "type": "stock",
                "id": "00000000-0000-4000-0000-000000000000",
                "state": "active",
                "list_date": "1990-01-02",
                "symbol": "AAPL",
                "margin_initial_ratio": "0.5000",
                "quote": "https://api.robinhood.com/quotes/AAPL/",
                "url": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/",
                "name": "Apple Inc. - Common Stock",
                "splits": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/splits/",
                "fundamentals": "https://api.robinhood.com/fundamentals/AAPL/",
                "market": "https://api.robinhood.com/markets/XNAS/",
                "simple_name": "Apple",
                "tradability": "tradable",
                "maintenance_ratio": "0.2500",
                "day_trade_ratio": "0.2500",
                "tradeable": true
            }
        ],
        "previous": null
    }
    """
    params = {
      'symbol': symbol,
    }
    response = self._session.get(API_HOST + 'instruments/', params=params)
    response.raise_for_status()
    response_json = response.json()
    if len(response_json['results']) == 0:
      raise NotFound()
    assert len(response_json['results']) == 1
    instrument = response_json['results'][0]
    assert instrument['symbol'] == symbol
    return instrument

  def get_instrument_split_history(self, instrument_id):
    """
    Args:
      instrument_id: Internal robinhood instrument id (a uuid)

    Example response:
    {
        "previous": null,
        "next": null,
        "results": [
            {
                "execution_date": "2014-06-09",
                "multiplier": "7.00000000",
                "url": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/splits/93657cb7-478b-42b0-a23c-9a64042cb694/",
                "divisor": "1.00000000",
                "instrument": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/"
            }
        ]
    }
    """
    response = self._session.get(API_HOST + 'instruments/{}/splits'.format(instrument_id))
    response.raise_for_status()
    return response.json()

  def get_quote(self, symbol):
    """
    Args:
      symbol: E.g. AAPL

    Example response:
    {
        "adjusted_previous_close": "178.1200",
        "ask_price": "175.3000",
        "ask_size": 1400,
        "bid_price": "175.1100",
        "bid_size": 500,
        "has_traded": true,
        "instrument": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/",
        "last_trade_price": "175.0000",
        "previous_close_date": "2018-02-28",
        "previous_close": "178.1200",
        "symbol": "AAPL",
        "trading_halted": false,
        "updated_at": "2018-03-02T01:00:00Z",
        "last_extended_hours_trade_price": "175.1000",
        "last_trade_price_source": "consolidated"
    }

    """
    response = self._session.get(API_HOST + 'quotes/{}/'.format(symbol))
    response.raise_for_status()
    return response.json()

  def get_quotes(self, symbols):
    """
    Args:
      symbols: E.g. [AAPL, GOOG]

    Example response:
    {
        "results": [
            {
                "last_extended_hours_trade_price": "175.1000",
                "updated_at": "2018-03-02T01:00:00Z",
                "bid_size": 500,
                "bid_price": "175.1100",
                "trading_halted": false,
                "previous_close_date": "2018-02-28",
                "ask_size": 1400,
                "instrument": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/",
                "has_traded": true,
                "ask_price": "175.3000",
                "last_trade_price_source": "consolidated",
                "last_trade_price": "175.0000",
                "previous_close": "178.1200",
                "adjusted_previous_close": "178.1200",
                "symbol": "AAPL"
            },
            ...
        ]
    }
    """
    params = {'symbols': ','.join(symbols)}
    response = self._session.get(API_HOST + 'quotes/', params=params)
    response.raise_for_status()
    return response.json()

  def get_dividends(self):
    """
    Example response:
    {
        "results": [
            {
                "record_date": "2018-02-27",
                "url": "https://api.robinhood.com/dividends/00000000-0000-4000-0000-000000000000/",
                "payable_date": "2018-03-13",
                "paid_at": null,
                "amount": "0.84",
                "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
                "rate": "0.8400000000",
                "position": "1.0000",
                "withholding": "0.00",
                "id": "00000000-0000-4000-0000-000000000000",
                "instrument": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/"
            },
            ...
        ],
        "previous": null,
        "next": null
    }
    """
    response = self._session.get(API_HOST + 'dividends/')
    response.raise_for_status()
    return response.json()

  def get_orders(self, instrument_url=None):
    """
    Example response:
    {
        "next": "https://api.robinhood.com/orders/?cursor=XXXXXXXX",
        "results": [
            {
                "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
                "trigger": "immediate",
                "state": "cancelled",
                "stop_price": null,
                "cumulative_quantity": "0.00000",
                "last_transaction_at": "2018-03-01T00:00:00.000000Z",
                "reject_reason": null,
                "average_price": null,
                "quantity": "1.00000",
                "cancel": null,
                "price": "0.--000000",
                "override_dtbp_checks": false,
                "response_category": "success",
                "type": "limit",
                "override_day_trade_checks": false,
                "position": "https://api.robinhood.com/accounts/XXXXXXXX/positions/00000000-0000-4000-0000-000000000000/",
                "id": "00000000-0000-4000-0000-000000000000",
                "executions": [],
                "time_in_force": "gtc",
                "instrument": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/",
                "created_at": "2018-03-01T00:00:00.000000Z",
                "fees": "0.00",
                "updated_at": "2018-03-01T00:00:00.000000Z",
                "ref_id": "00000000-0000-4000-0000-000000000000",
                "side": "buy",
                "url": "https://api.robinhood.com/orders/00000000-0000-4000-0000-000000000000/",
                "extended_hours": true
            },
            ...
        ],
        "previous": null
    }
    """
    params = {}
    if instrument_url:
      params['instrument'] = instrument_url
    response = self._session.get(API_HOST + 'orders/', params=params)
    response.raise_for_status()
    return response.json()

  def get_portfolio(self):
    """
    Example response:
    {
        "equity_previous_close": "0.0000",
        "last_core_market_value": "0.0000",
        "excess_margin": "0.0000",
        "unwithdrawable_deposits": "0.0000",
        "withdrawable_amount": "0.0000",
        "adjusted_equity_previous_close": "0.0000",
        "market_value": "0.0000",
        "url": "https://api.robinhood.com/portfolios/XXXXXXXX/",
        "unwithdrawable_grants": "0.0000",
        "extended_hours_equity": "0.0000",
        "excess_maintenance": "0.0000",
        "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
        "extended_hours_market_value": "0.0000",
        "equity": "0.0000",
        "start_date": "2018-02-01",
        "excess_maintenance_with_uncleared_deposits": "0.0000",
        "excess_margin_with_uncleared_deposits": "0.0000",
        "last_core_equity": "0.0000"
    }
    """
    response = self._session.get(API_HOST + 'portfolios/')
    response.raise_for_status()
    return response.json()['results'][0]

  def get_positions(self):
    """
    Example response:
    {
        "results": [
            {
                "created_at": "2018-02-09T15:42:15.536132Z",
                "quantity": "1.0000",
                "url": "https://api.robinhood.com/positions/XXXXXXXX/00000000-0000-4000-0000-000000000000/",
                "shares_held_for_buys": "0.0000",
                "updated_at": "2018-02-00T00:00:00.000000Z",
                "shares_held_for_stock_grants": "0.0000",
                "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
                "shares_held_for_options_collateral": "0.0000",
                "intraday_average_buy_price": "0.0000",
                "pending_average_buy_price": "0.0000",
                "instrument": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/",
                "average_buy_price": "0.0000",
                "intraday_quantity": "0.0000",
                "shares_held_for_sells": "0.0000",
                "shares_held_for_options_events": "0.0000",
                "shares_pending_from_options_events": "0.0000"
            },
            ...
        ],
        "previous": null,
        "next": null
    }
    """
    # Possible param: nonzero=true includes only owned securities
    response = self._session.get(API_HOST + 'positions/')
    response.raise_for_status()
    return response.json()

  def get_position_by_instrument_id(self, account_number, instrument_id):
    """
    Example response:
    {
        "shares_held_for_options_events": "0.0000",
        "intraday_average_buy_price": "0.0000",
        "shares_held_for_buys": "0.0000",
        "shares_held_for_stock_grants": "0.0000",
        "intraday_quantity": "0.0000",
        "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
        "shares_pending_from_options_events": "0.0000",
        "updated_at": "2018-02-28T15:40:29.270433Z",
        "average_buy_price": "0.0000",
        "shares_held_for_sells": "0.0000",
        "instrument": "https://api.robinhood.com/instruments/450dfc6d-5510-4d40-abfb-f633b7d9be3e/",
        "shares_held_for_options_collateral": "0.0000",
        "pending_average_buy_price": "0.0000",
        "created_at": "2018-02-09T15:42:15.536132Z",
        "quantity": "0.0000",
        "url": "https://api.robinhood.com/accounts/XXXXXXXX/positions/450dfc6d-5510-4d40-abfb-f633b7d9be3e/"
    }

    """
    # Possible param: nonzero=true includes only owned securities
    response = self._session.get(API_HOST + 'accounts/{}/positions/{}/'.format(account_number, instrument_id))
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.not_found:
        raise NotFound()
    return response.json()

  def get_historical_quotes(self, symbols, interval, span, bounds):
    """
    Args:
      symbol: e.g. AAPL
      interval: [5minute, 10minute]
      span: [day, week]
      bounds: [extended, regular]
    Example response:
    {
        "results": [
            {
                "instrument": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/",
                "quote": "https://api.robinhood.com/quotes/00000000-0000-4000-0000-000000000000/",
                "historicals": [
                    {
                        "session": "reg",
                        "volume": 1404330,
                        "begins_at": "2018-03-01T14:30:00Z",
                        "low_price": "177.6107",
                        "open_price": "178.5500",
                        "close_price": "177.9400",
                        "interpolated": false,
                        "high_price": "179.3600"
                    },
                    ...
                ],
                "open_time": "2018-03-01T14:30:00Z",
                "open_price": "178.5500",
                "span": "day",
                "symbol": "AAPL",
                "interval": "10minute",
                "bounds": "regular",
                "previous_close_price": "178.1200"
            }
        ]
    }
    """
    params = {
      'symbols': ','.join(symbols),
      'interval': interval,
      'span': span,
      'bounds': bounds,
    }
    response = self._session.get(API_HOST + 'quotes/historicals/', params=params)
    response.raise_for_status()
    return response.json()

  def get_news(self, symbol):
    """
    Args:
      symbol: e.g. AAPL

    Example response:
    {
        "next": "https://api.robinhood.com/news/AAPL/?page=2",
        "previous": null,
        "count": 292,
        "results": [
            {
                "published_at": "2018-03-01T22:42:00Z",
                "api_source": "yahoo_finance",
                "title": "The Top 4 Tech Stocks the Smart Money Is Selling and the 2 They're Buying",
                "url": "https://finance.yahoo.com/news/top-4-tech-stocks-smart-223300292.html",
                "updated_at": "2018-03-01T23:03:53.728153Z",
                "author": "",
                "instrument": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/",
                "preview_image_url": "https://robinhood-prism-storage.s3.amazonaws.com/feed-images/19ecf438-202c-470d-8ce2-a3149843dcf3",
                "relay_url": "https://news.robinhood.com/22962f51-1536-39f6-a6d0-3adad7180078/",
                "num_clicks": 1012,
                "preview_image_width": 580,
                "uuid": "22962f51-1536-39f6-a6d0-3adad7180078",
                "preview_image_height": 431,
                "source": "Yahoo Finance",
                "summary": "Hedge funds have over $6 trillion worth of assets under management, so when the smart money starts moving into a stock, it's not unwise for investors to take notice, because it just might signal the start of an upswing in its value."
            },
            ...
        ]
    }
    """
    response = self._session.get(API_HOST + 'midlands/news/{}/'.format(symbol))
    response.raise_for_status()
    return response.json()

  def get_fundamental(self, symbol):
    """
    Args:
      symbol: e.g. AAPL

    Example response:
    {
        "average_volume": "28771372.6932",
        "num_employees": 123000,
        "low": "172.6800",
        "headquarters_state": "California",
        "market_cap": "905143676100.0000",
        "description": "Apple, Inc. engages in the design, manufacture, and marketing of mobile communication, media devices, personal computers, and portable digital music players. It operates through the following geographical segments: Americas, Europe, Greater China, Japan, and Rest of Asia Pacific. The Americas segment includes both North and South America. The Europe segment consists of European countries, as well as India, the Middle East, and Africa. The Greater China segment comprises of China, Hong Kong, and Taiwan. The Rest of Asia Pacific segment includes Australia and Asian countries not included in the reportable operating segments of the company. The company was founded by Steven Paul Jobs, Ronald Gerald Wayne, and Stephen G. Wozniak on April 1, 1976 and is headquartered in Cupertino, CA.",
        "open": "178.5500",
        "pe_ratio": "17.9804",
        "dividend_yield": "1.5572",
        "instrument": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/",
        "ceo": "Tim Cook",
        "volume": "24285834.0000",
        "high": "179.7750",
        "low_52_weeks": "137.0500",
        "headquarters_city": "Cupertino",
        "high_52_weeks": "180.6150",
        "year_founded": 1976
    }
    """
    response = self._session.get(API_HOST + 'fundamentals/{}/'.format(symbol))
    response.raise_for_status()
    return response.json()

  def get_fundamentals(self, symbols):
    """
    Args:
      symbols: e.g. [AAPL, ...]

    Example response:
    [
        {
            "description": "Apple, Inc. engages in the design, manufacture, and marketing of mobile communication, media devices, personal computers, and portable digital music players. It operates through the following geographical segments: Americas, Europe, Greater China, Japan, and Rest of Asia Pacific. The Americas segment includes both North and South America. The Europe segment consists of European countries, as well as India, the Middle East, and Africa. The Greater China segment comprises of China, Hong Kong, and Taiwan. The Rest of Asia Pacific segment includes Australia and Asian countries not included in the reportable operating segments of the company. The company was founded by Steven Paul Jobs, Ronald Gerald Wayne, and Stephen G. Wozniak on April 1, 1976 and is headquartered in Cupertino, CA.",
            "volume": "24285834.0000",
            "instrument": "https://api.robinhood.com/instruments/00000000-0000-4000-0000-000000000000/",
            "low_52_weeks": "137.0500",
            "pe_ratio": "17.9804",
            "headquarters_state": "California",
            "ceo": "Tim Cook",
            "average_volume": "28771372.6932",
            "high": "179.7750",
            "dividend_yield": "1.5572",
            "open": "178.5500",
            "year_founded": 1976,
            "headquarters_city": "Cupertino",
            "market_cap": "905143676100.0000",
            "high_52_weeks": "180.6150",
            "low": "172.6800",
            "num_employees": 123000
        }
    ]
    """
    params = {
      'symbols': ','.join(symbols),
    }
    response = self._session.get(API_HOST + 'fundamentals/', params=params)
    response.raise_for_status()
    return response.json()['results']

  def order(self, account_url, instrument_url, symbol, quantity, bid_price, transaction_type, trigger, order_type, time_in_force):
    """
    Args:
      account_url: 
      instrument_url: 
      symbol: e.g. AAPL
      quantity: Number in the transaction
      bid_price (float): Price when buying
      transaction_type: [buy, sell]
      trigger: [immediate, stop]
      order_type: [market, limit]
      time_in_force: [gfd, gtc, ioc, opg] (eod or until cancelled)
    """
    exit()
    body = {
      'account': account_url,
      'instrument': instrument_url,
      'price': bid_price,
      'quantity': quantity,
      'side': transaction_type,
      'symbol': symbol,
      'time_in_force': time_in_force,
      'trigger': trigger,
      'type': order_type,
    }
    response = self._session.post(API_HOST + 'orders/', data=body)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=4))
    return response.json()
