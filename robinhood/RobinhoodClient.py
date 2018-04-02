"""
Good unofficial API documentation:
https://github.com/sanko/Robinhood

Another python library that inspired this:
https://github.com/Jamonek/Robinhood

More API documentation available at:

Some APIs not in use yet:
* GET /marketdata/forex/historicals/{<SYMBOL>/?bounds=24_7
* GET /marketdata/historicals/<SYMBOL>/
* GET /marketdata/historicals/ symbols, interval, span, bounds, cursor
* GET /marketdata/prices/<INST_ID>/?delayed=false&source=consolidated
* GET /marketdata/quotes/?bounds=trading instruments|symbols
* GET /marketdata/quotes/<SYMBOL|INST_ID>/?bounds=trading
* GET /portfolios/historicals/<ACCOUNT_NUMBER>/ bounds, span, interval
* GET /search/ (w/query)
"""

import json

import requests

from .exceptions import BadRequest, MfaRequired, NotFound, NotLoggedIn, TooManyRequests
from .util import (
  ANALYTICS_HOST,
  API_HOST,
  KNOWN_TAGS,
  ORDER_SIDES,
  ORDER_TYPES,
  get_cursor_from_url,
  get_last_id_from_url,
  get_instrument_url_from_id
)


class RobinhoodClient:
  def __init__(self):
    self._session = requests.Session()
    self._session.headers = {
      'Accept': '*/*',
      'Accept-Encoding': 'gzip, deflate',
      'Accept-Language': 'en;q=1',
      'Content-type': 'application/x-www-form-urlencoded; charset=utf-8',
      'X-Robinhood-API-Version': '1.204.0',
      'Connection': 'keep-alive',
      'User-Agent': 'Robinhood/823 (iPhone; iOS 7.1.2; Scale/2.00)',
    }
    self._authorization_headers = {}

  def set_auth_token(self, auth_token):
    self._authorization_headers['Authorization'] = 'Token {}'.format(auth_token)

  def set_auth_token_with_credentials(self, username, password, mfa=None):
    body = {
      'username': username,
      'password': password,
    }
    if mfa:
      body['mfa_code'] = mfa

    response = self._session.post(API_HOST + 'api-token-auth/', data=body)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    if 'mfa_required' in response_json:
      raise MfaRequired()
    auth_token = response.json()['token']
    self.set_auth_token(auth_token)
    return auth_token

  def clear_auth_token(self):
    response = self._session.post(API_HOST + 'api-token-logout/')
    response.raise_for_status()
    del self._session.headers['Authorization']

  def get_user(self):
    """
    Example response:
    {
        "basic_info": "https://api.robinhood.com/user/basic_info/",
        "url": "https://api.robinhood.com/user/",
        "email_verified": true,
        "id": "00000000-000-4000-0000-0000000000",
        "additional_info": "https://api.robinhood.com/user/additional_info/",
        "id_info": "https://api.robinhood.com/user/id/",
        "last_name": "Bob",
        "first_name": "Smith",
        "email": "test@example.com",
        "international_info": "https://api.robinhood.com/user/international_info/",
        "investment_profile": "https://api.robinhood.com/user/investment_profile/",
        "employment": "https://api.robinhood.com/user/employment/",
        "username": "test",
        "created_at": "2018-02-01T22:46:39.922345Z"
    }
    """
    response = self._session.get(API_HOST + 'user/', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()

  def get_user_basic_info(self):
    """
    Example response:
    {
        "phone_number": "15555555555",
        "citizenship": "US",
        "address": "123 Fake St",
        "state": "CA",
        "number_dependents": 0,
        "updated_at": "2018-02-01T15:06:10.045924Z",
        "tax_id_ssn": "1234",
        "country_of_residence": "US",
        "user": "https://api.robinhood.com/user/",
        "zipcode": "000000000",
        "city": "Fake Town",
        "date_of_birth": "1999-01-01"
    }
    """
    response = self._session.get(API_HOST + 'user/basic_info', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()

  def get_user_additional_info(self):
    """
    Example response:
    {
        "security_affiliated_firm_relationship": "",
        "object_to_disclosure": false,
        "security_affiliated_person_name": "Tim",
        "updated_at": "2018-02-01T22:47:11.227574Z",
        "control_person": true,
        "control_person_security_symbol": "symbol",
        "user": "https://api.robinhood.com/user/",
        "security_affiliated_address": "addr",
        "security_affiliated_employee": false,
        "stock_loan_consent_status": "needs_response",
        "sweep_consent": false,
        "security_affiliated_firm_name": ""
    }
    """
    response = self._session.get(API_HOST + 'user/additional_info', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()

  def get_referral_code(self):
    """
    Example response:
    {
        "code": "matts952",
        "user_id": "00000000-0000-4000-0000-000000000000",
        "url": "https://share.robinhood.com/matts952"
    }
    """
    response = self._session.get(API_HOST + 'midlands/referral/code/', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()

  def get_margin_calls(self):
    response = self._session.get(API_HOST + 'margin/calls/', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    # TODO: auto page if needed
    assert not response_json['next']
    return response_json['results']

  def get_subscription_fees(self):
    """
    Example response:
    [
        {
            "id": "2-2-2-2",
            "date": "2018-02-21",
            "credit": "0.00",
            "subscription": "https://api.robinhood.com/subscription/subscriptions/0-0-0-0/",
            "amount": "0.00",
            "url": "https://api.robinhood.com/subscription/subscription_fees/2-2-2-2/",
            "carry_forward_credit": "0.00",
            "created_at": "2018-01-22T01:33:42.237983Z",
            "refunds": []
        }
    ]

    """
    response = self._session.get(API_HOST + 'subscription/subscription_fees/', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    # TODO: auto page if needed
    assert not response_json['next']
    return response_json['results']

  def get_subscriptions(self):
    """
    Example response:
    [
        {
            "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
            "id": "0-0-0-0",
            "plan": {
                "subscription_margin_limit": "0.00",
                "instant_deposit_limit": "0.00",
                "monthly_cost": "0.00",
                "margin_interest": null,
                "id": "1-1-1-1"
            },
            "credit": "0.00",
            "renewal_date": "2018-03-20",
            "ended_at": null,
            "url": "https://api.robinhood.com/subscription/subscriptions/0-0-0-0/",
            "created_at": "2018-02-22T01:33:42.231295Z",
            "unsubscribe": null
        }
    ]
    """
    params = {
      'active': 'true',
    }
    response = self._session.get(API_HOST + 'subscription/subscriptions/', params=params, headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    # TODO: auto page if needed
    assert not response_json['next']
    return response_json['results']

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
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    # This api likely never pages, but you never know.
    assert not response_json['next']
    return response_json

  def download_document_by_id(self, document_id):
    """The response is a PDF file"""
    response = self._session.get(
      API_HOST + 'documents/{}/download/'.format(document_id),
      headers=self._authorization_headers
    )
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.content

  def get_document_by_id(self, document_id):
    """
    Example response:
    {
        "insert_1_url": "",
        "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
        "download_url": "https://api.robinhood.com/documents/00000000-0000-4000-0000-000000000000/download/",
        "insert_4_url": "",
        "insert_2_url": "",
        "insert_6_url": "",
        "url": "https://api.robinhood.com/documents/00000000-0000-4000-0000-000000000000/",
        "created_at": "2018-02-01T16:17:07.579125Z",
        "insert_3_url": "",
        "id": "00000000-0000-4000-0000-000000000000",
        "updated_at": "2018-02-01T18:58:54.013192Z",
        "type": "trade_confirm",
        "insert_5_url": "",
        "date": "2018-02-01"
    }
    """
    response = self._session.get(API_HOST + 'documents/{}/'.format(document_id), headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()

  def get_documents(self):
    """
    Example response:
    {
        "results": [
            {
                "insert_1_url": "",
                "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
                "download_url": "https://api.robinhood.com/documents/00000000-0000-4000-0000-000000000000/download/",
                "insert_4_url": "",
                "insert_2_url": "",
                "insert_6_url": "",
                "url": "https://api.robinhood.com/documents/00000000-0000-4000-0000-000000000000/",
                "created_at": "2018-02-01T16:17:07.579125Z",
                "insert_3_url": "",
                "id": "00000000-0000-4000-0000-000000000000",
                "updated_at": "2018-02-01T18:58:54.013192Z",
                "type": "trade_confirm",
                "insert_5_url": "",
                "date": "2018-02-01"
            },
            ...
        ],
        "previous": null,
        "next": null
    }
    """
    response = self._session.get(API_HOST + 'documents/', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

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
    response = self._session.get(API_HOST + 'watchlists/', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json

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
    response = self._session.get(API_HOST + 'watchlists/{}/'.format(watchlist_name), headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json

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
    response = self._session.get(API_HOST + 'settings/notifications', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
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
    response = self._session.get(API_HOST + 'notifications/devices/', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    # This probably won't autopage for a LONG time
    assert not response_json['next']
    return response_json

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
            "day_trade_buying_power": "0.00",
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
    response = self._session.get(API_HOST + 'accounts/', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
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
    response = self._session.get(API_HOST + 'user/investment_profile/', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()

  def get_popularity(self, instrument_id):
    """
    Example response:
    {
        "num_open_positions": 155,
        "instrument": "https://api.robinhood.com/instruments/e6f3bb44-dcdf-445b-bbcb-2e738fd21d6d/"
    }
    """
    response = self._session.get(API_HOST + 'instruments/{}/popularity/'.format(instrument_id))
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json())
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()

  def get_popularities(self, instrument_ids):
    """
    Example response:
    {
        "next": null,
        "results": [
            {
                "instrument": "https://api.robinhood.com/instruments/e6f3bb44-dcdf-445b-bbcb-2e738fd21d6d/",
                "num_open_positions": 155
            }
        ],
        "previous": null
    }
    """
    # We are limited to about 50, so we need to do multiple calls if grabbing more than that.
    if len(instrument_ids) > 50:
      full_popularities = []
      for i in range(0, len(instrument_ids), 50):
        full_popularities.extend(self.get_popularities(instrument_ids[i:i + 50]))
      return full_popularities

    params = {
      'ids': ','.join(instrument_ids),
    }
    response = self._session.get(API_HOST + 'instruments/popularity/', params=params)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json())
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

  def get_rating(self, instrument_id):
    """
    Example response:
    {
        "summary": {
            "num_hold_ratings": 11,
            "num_buy_ratings": 2,
            "num_sell_ratings": 0
        },
        "ratings": [],
        "instrument_id": "e6f3bb44-dcdf-445b-bbcb-2e738fd21d6d"
    }
    """
    response = self._session.get(API_HOST + 'midlands/ratings/{}/'.format(instrument_id))
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json())
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()

  def get_ratings(self, instrument_ids):
    """
    Example response:
    {
        "count": 1,
        "results": [
            {
                "summary": {
                    "num_hold_ratings": 11,
                    "num_buy_ratings": 2,
                    "num_sell_ratings": 0
                },
                "ratings": [],
                "instrument_id": "e6f3bb44-dcdf-445b-bbcb-2e738fd21d6d"
            }
        ],
        "previous": null,
        "next": null
    }
    """
    # For now, do 20 at a time instead of paging. We can hit a scenerio where
    # we have to limit both the instrument ids and page.
    if len(instrument_ids) > 20:
      full_ratings = []
      for i in range(0, len(instrument_ids), 20):
        full_ratings.extend(self.get_ratings(instrument_ids[i:i + 20]))
      return full_ratings

    params = {
      'ids': ','.join(instrument_ids),
    }
    response = self._session.get(API_HOST + 'midlands/ratings/', params=params)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json())
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

  def get_instrument_reasons_for_personal_tag(self, tag):
    """
    Example response:
    [
        {
            "symbol": "FB",
            "id": "ebab2398-028d-4939-9f1d-13bf38f81c50",
            "reason": "More trades than usual"
        },
        ...
    ]
    """
    assert tag in KNOWN_TAGS
    response = self._session.get(ANALYTICS_HOST + 'instruments/tag/{}/'.format(tag), headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json())
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    return response_json['instruments']

  def get_similar_to(self, instrument_id):
    """
    Example response:
    [
        {
            "description": "Visa, Inc. engages in ...",
            "extraData": {},
            "logo_url": ".../Visa_2014_logo_detail.svg/175px-Visa_2014_logo_detail.svg.png",
            "tags": [
                {
                    "slug": "top-100-popular",
                    "name": "Top 100 Popular"
                },
                ...
            ],
            "instrument_id": "93495afe-b84b-4664-881c-b6361b0edeef",
            "simple_name": "Visa",
            "symbol": "V",
            "name": "VISA Inc.",
            "brands": "Visa"
        },
        ...
    ]
    """
    params = {
      'similar_to': instrument_id,
    }
    response = self._session.get(ANALYTICS_HOST + 'instruments/', params=params)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json())
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    return response_json

  def get_instrument_ids_for_tag(self, tag):
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
    assert tag in KNOWN_TAGS
    response = self._session.get(API_HOST + 'midlands/tags/tag/{}/'.format(tag))
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json())
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    instrument_ids = [get_last_id_from_url(instrument_url) for instrument_url in response_json['instruments']]
    return instrument_ids

  def get_instruments(self, instrument_ids):
    """
    Example response:
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
    # We are limited to 75 based on how long the query param can be, so we
    # need to do multiple calls if grabbing more than 75 instruments.
    if len(instrument_ids) > 75:
      full_instruments = []
      for i in range(0, len(instrument_ids), 75):
        full_instruments.extend(self.get_instruments(instrument_ids=instrument_ids[i:i + 75]))
      return full_instruments

    params = {
      'ids': ','.join(instrument_ids),
      'active_instruments_only': 'false',
    }
    response = self._session.get(API_HOST + 'instruments/', params=params)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json())
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

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
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json())
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
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
      'active_instruments_only': True,
    }
    response = self._session.get(API_HOST + 'instruments/', params=params)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json())
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
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
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    # This is probably never the case.
    assert not response_json['next']
    return response_json

  def get_quote(self, instrument_id):
    """
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
    response = self._session.get(API_HOST + 'quotes/{}/'.format(instrument_id))
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json())
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()

  def get_quotes(self, instrument_ids):
    """
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
    if len(instrument_ids) > 35:
      full_quotes = []
      for i in range(0, len(instrument_ids), 35):
        full_quotes.extend(self.get_quotes(instrument_ids[i:i + 35]))
      return full_quotes

    # bounds=trading ?
    params = {
      'instruments': ','.join([get_instrument_url_from_id(instrument_id) for instrument_id in instrument_ids])
    }

    response = self._session.get(API_HOST + 'quotes/', params=params)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json())
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()['results']

  def get_prices(self, symbols=None, instrument_ids=None):
    """
    Example response:
    {
        "results": [
            {
                "size": 1149976,
                "updated_at": "2018-03-07T01:00:00Z",
                "bid_size": 100,
                "price": "176.6700",
                "instrument_id": "450dfc6d-5510-4d40-abfb-f633b7d9be3e",
                "ask_size": 100,
                "ask_price": "173.9900",
                "bid_price": "173.6500"
            },
            ...
        ]
    }
    """
    assert symbols or instrument_ids
    assert not (symbols and instrument_ids)
    params = {
      'source': 'consolidated',
      'delayed': 'true',
    }
    if symbols:
      params['symbols'] = ','.join(symbols)
    if instrument_ids:
      params['instruments'] = ','.join([get_instrument_url_from_id(instrument_id) for instrument_id in instrument_ids])
    response = self._session.get(API_HOST + 'marketdata/prices/'.format(instrument_id), params=params)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json())
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()

  def get_dividend_by_id(self, dividend_id):
    """
    Example response:
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
    }
    """
    response = self._session.get(API_HOST + 'dividends/{}/'.format(dividend_id), headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()

  def get_ach_relationship_by_id(self, relationship_id):
    """
    Example response:
    {
        "bank_account_holder_name": "Bob Smith",
        "created_at": "2018-02-01T23:41:03.251980Z",
        "unlink": "https://api.robinhood.com/ach/relationships/00000000-0000-4000-0000-000000000000/unlink/",
        "id": "00000000-0000-4000-0000-000000000000",
        "bank_account_nickname": "MY CHECKING",
        "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
        "bank_account_number": "1234",
        "verify_micro_deposits": null,
        "withdrawal_limit": null,
        "verified": true,
        "initial_deposit": "0.00",
        "bank_routing_number": "12344567",
        "url": "https://api.robinhood.com/ach/relationships/00000000-0000-4000-0000-000000000000/",
        "unlinked_at": null,
        "bank_account_type": "checking",
        "verification_method": "bank_auth"
    }
    """
    response = self._session.get(API_HOST + 'ach/relationships/{}'.format(relationship_id), headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()

  def get_ach_transfer_by_id(self, transfer_id):
    """
    Example response:
    {
        "status_description": "",
        "fees": "0.00",
        "cancel": null,
        "id": "00000000-0000-4000-0000-000000000000",
        "created_at": "2018-02-01T05:54:32.902711Z",
        "amount": "0.00",
        "ach_relationship": "https://api.robinhood.com/ach/relationships/00000000-0000-4000-0000-000000000000/",
        "early_access_amount": "0.00",
        "expected_landing_date": "2018-02-08",
        "state": "pending",
        "updated_at": "2018-02-01T05:54:33.524297Z",
        "scheduled": false,
        "direction": "deposit",
        "url": "https://api.robinhood.com/ach/transfers/00000000-0000-4000-0000-000000000000/"
    }
    """
    response = self._session.get(API_HOST + 'ach/transfers/{}'.format(transfer_id), headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      raise
    return response.json()

  def get_ach_transfers(self):
    """
    Example response:
    [
        {
            "status_description": "",
            "fees": "0.00",
            "cancel": null,
            "id": "00000000-0000-4000-0000-000000000000",
            "created_at": "2018-02-01T05:54:32.902711Z",
            "amount": "0.00",
            "ach_relationship": "https://api.robinhood.com/ach/relationships/00000000-0000-4000-0000-000000000000/",
            "early_access_amount": "0.00",
            "expected_landing_date": "2018-02-08",
            "state": "pending",
            "updated_at": "2018-02-01T05:54:33.524297Z",
            "scheduled": false,
            "direction": "deposit",
            "url": "https://api.robinhood.com/ach/transfers/00000000-0000-4000-0000-000000000000/"
        },
        ...
    ]
    """
    # There's also updated_at[gte]
    response = self._session.get(API_HOST + 'ach/transfers/', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

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
    response = self._session.get(API_HOST + 'dividends/', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

  def get_order_by_id(self, order_id):
    """
    See util.ORDER_STATES

    Example response:
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
    }
    """
    response = self._session.get(API_HOST + 'orders/{}/'.format(order_id), headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()

  def get_orders(self, instrument_id=None):
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
    orders = []
    cursor = None

    while True:
      params = {}
      if instrument_id:
        params['instrument'] = get_instrument_url_from_id(instrument_id)
      if cursor:
        params['cursor'] = cursor
      response = self._session.get(API_HOST + 'orders/', params=params, headers=self._authorization_headers)
      try:
        response.raise_for_status()
      except requests.HTTPError as http_error:
        if  http_error.response.status_code == requests.codes.unauthorized:
          raise NotLoggedIn(http_error.response.json()['detail'])
        elif  http_error.response.status_code == requests.codes.too_many_requests:
          raise TooManyRequests()
        raise
      orders_json = response.json()
      orders.extend(orders_json['results'])
      if orders_json['next']:
        cursor = get_cursor_from_url(orders_json['next'])
      else:
        return orders

  def get_popular_stocks(self):
    """
    The most active S&P 500 stocks based on the trading activity of Robinhood customers.

    Example response:
    This is only updated on Sunday.
    {
        "title": "Popular Stocks",
        "subtitle": "Rankings based on trading activity of Robinhood customers",
        "data": [
            {
                "symbol": "AAPL",
                "subtitle": "Apple"
            },
            ...
        ],
        "disclosure": "The Popular Stocks feature is meant for informational purposes and is not ..."
    }
    """
    response = requests.get('https://brokerage-static.s3.amazonaws.com/popular_stocks/data.json')
    response_json = response.json()
    assert len(response_json) == 1
    return response_json[0]

  def get_sp500_movers(self, direction):
    """
    Args:
      direction: up or down

    Example response:
    {
        "count": 10,
        "previous": null,
        "results": [
            {
                "instrument_url": "https://api.robinhood.com/instruments/e6f3bb44-dcdf-445b-bbcb-2e738fd21d6d/",
                "symbol": "XL",
                "price_movement": {
                    "market_hours_last_price": "55.9200",
                    "market_hours_last_movement_pct": "29.15"
                },
                "description": "XL Group Ltd. is a holding company, which engages in the provision of general insurance services. The company operates in two segments: Insurance and Reinsurance. The Insurance segment provides commercial property, casualty and specialty insurance products on a global basis. The Reinsurance provides casualty, property risk, property catastrophe, specialty, and other reinsurance lines on a global basis with business being written on both a proportional and non-proportional treaty basis and also on a facultative basis. XL Group was founded in 1986 and is headquartered in Hamilton, Bermuda.",
                "updated_at": "2018-03-05T14:03:03.190560Z"
            },
            ...
        ],
        "next": null
    }
    """
    params = {
      'direction': direction,
    }
    response = self._session.get(API_HOST + 'midlands/movers/sp500/', params=params, headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()['results']

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
    response = self._session.get(API_HOST + 'portfolios/', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()['results'][0]

  def get_positions(self, include_old=False):
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
    params = {}
    if not include_old:
      params['nonzero'] = 'true'
    response = self._session.get(
      API_HOST + 'positions/',
      params=params,
      headers=self._authorization_headers
    )
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    portfolio_json = response.json()
    # TODO: autopage
    assert not portfolio_json['next']
    return portfolio_json['results']

  def get_position_by_instrument_id(self, instrument_id, use_account_number=None):
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
    account_number = use_account_number or self.get_account()['account_number']
    # Possible param: nonzero=true includes only owned securities
    response = self._session.get(
      API_HOST + 'accounts/{}/positions/{}/'.format(account_number, instrument_id),
      headers=self._authorization_headers
    )
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.not_found:
        raise NotFound()
      elif  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()

  def get_historical_quotes(self, symbols, interval, span, bounds):
    """
    Args:
      symbol: e.g. AAPL
      interval: [5minute, 10minute, day, week]
      span: [day, week, year, 5year]
      bounds: [extended, regular, trading]

    Example combos:
      * span=week, interval=10minute
      * span=year, interval=day
      * span=5year, interval=week
      * span=5year, interval=week
      * span=day, interval=5minute

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
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json())
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
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
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()

  def get_tags(self, instrument_id):
    """
    Example response:
    [
        {
            "name": "Insurance",
            "instruments": [
                "https://api.robinhood.com/instruments/46c13eda-65e8-4bc5-b44f-95a05a24bede/",
                ...
            ],
            "slug": "insurance",
            "description": ""
        },
        ...
    ]
    """
    response = self._session.get(API_HOST + 'midlands/tags/instrument/{}/'.format(instrument_id))
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    return response_json['tags']

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
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
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
    # We are limited to 100, so we need to do multiple calls if grabbing more than that.
    if len(symbols) > 100:
      full_fundamentals = []
      for i in range(0, len(symbols), 100):
        full_fundamentals.extend(self.get_fundamentals(symbols[i:i + 100]))
      return full_fundamentals

    params = {
      'symbols': ','.join(symbols),
    }
    response = self._session.get(API_HOST + 'fundamentals/', params=params)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json())
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()['results']

  def get_referrals(self):
    """
    Example response:
    {
        "count": 3,
        "next": null,
        "previous": null,
        "results": [
            {
                "campaign": "general",
                "created_at": "2018-02-07T20:35:06.131924Z",
                "direction": "from",
                "experiment": "stock-claim",
                "id": "1000000-00-400-00-00000",
                "reward": {
                    "cash": null,
                    "stocks": [
                        {
                            "instrument_url": "https://api.robinhood.com/instruments/2000000-00-400-00-00000/",
                            "symbol": "GRPN",
                            "quantity": 1.0,
                            "cost_basis": 5.13,
                            "state": "granted",
                            "state_description": "Received",
                            "claimable": false,
                            "uuid": "3000000-00-400-00-00000",
                            "random": true
                        }
                    ]
                },
                "state": "received",
                "state_description": null,
                "updated_at": "2018-02-07T22:38:44.491145Z",
                "remind_url": null,
                "url": "https://api.robinhood.com/referral/1000000-00-400-00-00000/",
                "other_user": {
                    "first_name": "Billy",
                    "last_initial": "S"
                },
                "can_remind": false
            },
            ...
        ]
    }
    """
    response = self._session.get(API_HOST + 'midlands/referral/', headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

  def cancel_order(self, order_id):
    """
    Example response:
    {}
    """
    response = self._session.post(API_HOST + 'orders/{}/cancel/'.format(order_id), headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json()['detail'])
      raise
    return response.json()

  def order(self, account_url, instrument_url, order_type, order_side, symbol, quantity, price):
    """
    Args:
      account_url
      instrument_url
      order_type: [market, limit]
      order_side: [buy, sell]
      symbol: e.g. AAPL
      quantity: Number in the transaction
      price (float): Price when buying

    Example response:
    {
        "override_day_trade_checks": false,
        "id": "00000000-0000-4000-0000-000000000000d",
        "cumulative_quantity": "0.00000",
        "trigger": "immediate",
        "ref_id": null,
        "state": "unconfirmed",
        "quantity": "1.00000",
        "response_category": null,
        "extended_hours": false,
        "price": "234.00000000",
        "url": "https://api.robinhood.com/orders/00000000-0000-4000-0000-000000000000d/",
        "fees": "0.00",
        "created_at": "2018-03-08T00:56:03.878630Z",
        "executions": [],
        "last_transaction_at": "2018-02-01T00:56:03.878630Z",
        "type": "limit",
        "side": "sell",
        "cancel": "https://api.robinhood.com/orders/00000000-0000-4000-0000-000000000000d/cancel/",
        "instrument": "https://api.robinhood.com/instruments/10000000-0000-4000-0000-000000000000/",
        "position": "https://api.robinhood.com/positions/XXXXXXXX/10000000-0000-4000-0000-000000000000/",
        "stop_price": null,
        "average_price": null,
        "updated_at": "2018-02-01T00:56:03.955774Z",
        "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
        "reject_reason": null,
        "time_in_force": "gtc",
        "override_dtbp_checks": false
    }
    """
    assert order_side in ORDER_SIDES
    assert order_type in ORDER_TYPES

    body = {
      'account': account_url,
      'instrument': instrument_url,
      'price': price,
      'quantity': quantity,
      'side': order_side,
      'symbol': symbol,
      'time_in_force': 'gtc', # see util.TIME_IN_FORCES
      'trigger': 'immediate', # see util.TRIGGERS
      'type': order_type,
    }
    response = self._session.post(API_HOST + 'orders/', data=body, headers=self._authorization_headers)
    try:
      response.raise_for_status()
    except requests.HTTPError as http_error:
      if  http_error.response.status_code == requests.codes.unauthorized:
        raise NotLoggedIn(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.bad_request:
        raise BadRequest(http_error.response.json()['detail'])
      elif  http_error.response.status_code == requests.codes.too_many_requests:
        raise TooManyRequests()
      raise
    return response.json()
