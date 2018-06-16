"""
A secure Robinhood library that simplifies API use.

Another python library that inspired this:
https://github.com/Jamonek/Robinhood
"""

from datetime import datetime, timedelta
import copy
import json
import uuid

import requests

from .exceptions import (
    BadRequest,
    Forbidden,
    MfaRequired,
    NotFound,
    NotLoggedIn,
    TooManyRequests
)
from .util import (
    CERT_BUNDLE_PATH,
    ANALYTICS,
    ANALYTICS_HOST,
    API,
    API_HOST,
    NUMMUS,
    NUMMUS_HOST,
    ORDER_SIDES,
    ORDER_TYPES,
    OPTIONS_TYPES,
    OPTIONS_STATES,
    TRADABILITY,
    BOUNDS,
    INTERVALS,
    SPANS,
    DIRECTIONS,
    DIRECTION_TO_ORDER_SIDE,
    get_cursor_from_url,
    get_last_id_from_url,
    instrument_id_to_url,
    options_instrument_id_to_url
)


def _raise_on_error(response):
  try:
    response.raise_for_status()
  except requests.HTTPError as http_error:
    if  http_error.response.status_code == requests.codes.unauthorized:
      raise NotLoggedIn(http_error.response.json()['detail'])
    elif  http_error.response.status_code == requests.codes.bad_request:
      raise BadRequest(http_error.response.json())
    elif  http_error.response.status_code == requests.codes.too_many_requests:
      raise TooManyRequests()
    elif  http_error.response.status_code == requests.codes.not_found:
      raise NotFound()
    if  http_error.response.status_code == requests.codes.forbidden:
      raise Forbidden(http_error.response.json())
    raise


class RobinhoodClient:
  def __init__(self):
    self._api_session = requests.Session()
    self._api_session.verify = CERT_BUNDLE_PATH
    self._nummus_session = requests.Session()
    self._nummus_session.verify = CERT_BUNDLE_PATH
    self._analytics_session = requests.Session()
    self._analytics_session.verify = CERT_BUNDLE_PATH
    common_headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en;q=1',
        'Content-type': 'application/x-www-form-urlencoded; charset=utf-8',
        'X-Robinhood-API-Version': '1.204.0',
        'Connection': 'keep-alive',
        'User-Agent': 'Robinhood/823 (iPhone; iOS 7.1.2; Scale/2.00)',
    }
    self._api_session.headers = common_headers
    self._nummus_session.headers = common_headers
    self._analytics_session.headers = common_headers
    self._authorization_headers = {}
    self._oauth2_refresh_token = None
    self._oauth2_expires_at = None
    self._client_id = 'c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS'

  def _get_session(self, host, authed=False):
    if host == API:
      session = self._api_session
    elif host == NUMMUS:
      session = self._nummus_session
    elif host == ANALYTICS:
      session = self._analytics_session
    else:
      raise Exception('Missing host for {}'.format(host))

    # Set auth as required
    if authed:
      self.ensure_valid_oauth2_token()
      session.headers.update(self._authorization_headers)
    else:
      for key in self._authorization_headers.keys():
        if key in session.headers:
          del session.headers[key]

    return session

  def set_oauth2_token(self, token_type, access_token, expires_at, refresh_token):
    self._authorization_headers['Authorization'] = '{} {}'.format(token_type, access_token)
    self._oauth2_refresh_token = refresh_token
    self._oauth2_expires_at = expires_at

  def ensure_valid_oauth2_token(self):
    if not self._oauth2_refresh_token:
      raise Exception('Cannot ensure valid OAuth2 token. No refresh token.')
    elif datetime.now() > self._oauth2_expires_at:
      self.refresh_oauth2_token()

  def refresh_oauth2_token(self):
    body = {
      'refresh_token': self._oauth2_refresh_token,
      'grant_type': 'refresh_token',
      'client_id': self._client_id
    }
    response = self._get_session(API).post(API_HOST + 'oauth2/token/', data=body)
    _raise_on_error(response)
    oauth2_details = response.json()
    if 'mfa_required' in oauth2_details:
        raise MfaRequired()
    self.set_oauth2_token(
      oauth2_details['token_type'],
      oauth2_details['access_token'],
      datetime.now() + timedelta(seconds=oauth2_details['expires_in']),
      oauth2_details['refresh_token']
    )

  def set_auth_token_with_credentials(self, username, password, mfa=None):
    body = {
      'username': username,
      'password': password,
      'grant_type': 'password',
      'client_id': self._client_id
    }
    if mfa:
      body['mfa_code'] = mfa

    response = self._get_session(API).post(API_HOST + 'oauth2/token/', data=body)
    _raise_on_error(response)
    oauth2_details = response.json()
    if 'mfa_required' in oauth2_details:
      raise MfaRequired()
    self.set_oauth2_token(
      oauth2_details['token_type'],
      oauth2_details['access_token'],
      datetime.now() + timedelta(seconds=oauth2_details['expires_in']),
      oauth2_details['refresh_token']
    )

  def clear_auth_token(self):
    body = {
        'client_id': self._client_id,
        'token': self._oauth2_refresh_token
    }
    response = self._get_session(API, authed=True).post(API_HOST + 'oauth2/revoke_token/', )
    _raise_on_error(response)
    self._authorization_headers = {}
    del self._session.headers['Authorization']

  def _collect_results(self, request_method, request_args, request_kwargs={}, request_params={}):
    """Used within apis that are paged"""
    results = []
    cursor = None
    page_params = copy.copy(request_params)

    while True:
      if cursor:
        page_params['cursor'] = cursor
      response = request_method(
          *request_args,
          **request_kwargs,
          params=page_params
      )
      _raise_on_error(response)
      response_json = response.json()
      results.extend(response_json['results'])
      if response_json['next']:
        cursor = get_cursor_from_url(response_json['next'])
      else:
        return results

  def request_app_mfa(self):
    """
    Example response:
    {
      'enabled': False,
      'totp_token': 'XXXX'
    }
    """
    response = self._get_session(API, authed=True).put(API_HOST + 'mfa/app/request/')
    _raise_on_error(response)
    return response.json()

  def request_sms_mfa(self, phone_number):
    """
    Example response:
    {
      'phone_number': '##########',
      'enabled': False
    }
    """
    body = {'phone_number': phone_number}
    response = self._get_session(API, authed=True).put(API_HOST + 'mfa/sms/request/', data=body)
    _raise_on_error(response)
    return response.json()

  def verify_app_mfa(self, mfa_code):
    """
    Example successful return:
    {
      'challenge_type': 'app',
      'enabled': True
    }
    """
    body = {'mfa_code': mfa_code}
    response = self._get_session(API, authed=True).put(API_HOST + 'mfa/app/verify/', data=body)
    _raise_on_error(response)
    return response.json()

  def verify_sms_mfa(self, mfa_code):
    """
    Example response:
    {
      'challenge_type': 'sms',
      'phone_number': '##########',
      'enabled': True,
    }
    """
    body = {'mfa_code': mfa_code}
    response = self._get_session(API, authed=True).put(API_HOST + 'mfa/sms/verify/', data=body)
    _raise_on_error(response)
    return response.json()

  def get_mfa_backup(self):
    """
    Note that this re-generates the backup and invlidates any existing backup code.

    Example response:
    {
      'backup_code': '###########'
    }
    """
    response = self._get_session(API, authed=True).get(API_HOST + 'mfa/recovery/')
    _raise_on_error(response)
    return response.json()

  def get_mfa(self):
    """
    Example response with MFA setup:
    {
      'challenge_type': 'app',
      'enabled': True
    }

    Example response without MFA setup:
    {
      'enabled': False
    }
    """
    response = self._get_session(API, authed=True).get(API_HOST + 'mfa/')
    _raise_on_error(response)
    return response.json()

  def remove_mfa(self):
    """No response, just success."""
    response = self._get_session(API, authed=True).delete(API_HOST + 'mfa/')
    _raise_on_error(response)

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
    response = self._get_session(API, authed=True).get(API_HOST + 'user/')
    _raise_on_error(response)
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
    response = self._get_session(API, authed=True).get(API_HOST + 'user/basic_info')
    _raise_on_error(response)
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
    response = self._get_session(API, authed=True).get(API_HOST + 'user/additional_info')
    _raise_on_error(response)
    return response.json()

  def get_experiments(self):
    """
    Example response:
    [
        {
            "experiment_name": "android-onboarding-fund-account-sipc-disclaimer"
        },
        {
            "experiment_name": "support-categories"
        },
        ...
    ]
    """
    response = self._get_session(ANALYTICS, authed=True).get(ANALYTICS_HOST + 'experiments/')
    _raise_on_error(response)
    return response.json()

  def get_referral_code(self):
    """
    Example response:
    {
        "code": "matts952",
        "user_id": "0-0-4-0",
        "url": "https://share.robinhood.com/matts952"
    }
    """
    response = self._get_session(API, authed=True).get(API_HOST + 'midlands/referral/code/')
    _raise_on_error(response)
    return response.json()

  def get_margin_calls(self):
    response = self._get_session(API, authed=True).get(API_HOST + 'margin/calls/')
    _raise_on_error(response)
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
    response = self._get_session(API, authed=True).get(API_HOST + 'subscription/subscription_fees/')
    _raise_on_error(response)
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
    response = self._get_session(API, authed=True).get(API_HOST + 'subscription/subscriptions/', params=params)
    _raise_on_error(response)
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
    response = self._get_session(API).get(API_HOST + 'markets/')
    _raise_on_error(response)
    response_json = response.json()
    # This api likely never pages, but you never know.
    assert not response_json['next']
    return response_json

  def download_document_by_id(self, document_id):
    """The response is a PDF file"""
    # This document actually comes from another domain
    response = self._get_session(API, authed=True).get(API_HOST + 'documents/{}/download/'.format(document_id))
    _raise_on_error(response)
    return response.content

  def get_document_by_id(self, document_id):
    """
    Example response:
    {
        "insert_1_url": "",
        "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
        "download_url": "https://api.robinhood.com/documents/0-0-4-0/download/",
        "insert_4_url": "",
        "insert_2_url": "",
        "insert_6_url": "",
        "url": "https://api.robinhood.com/documents/0-0-4-0/",
        "created_at": "2018-02-01T16:17:07.579125Z",
        "insert_3_url": "",
        "id": "0-0-4-0",
        "updated_at": "2018-02-01T18:58:54.013192Z",
        "type": "trade_confirm",
        "insert_5_url": "",
        "date": "2018-02-01"
    }
    """
    response = self._get_session(API, authed=True).get(API_HOST + 'documents/{}/'.format(document_id))
    _raise_on_error(response)
    return response.json()

  def get_documents(self):
    """
    Example response:
    {
        "results": [
            {
                "insert_1_url": "",
                "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
                "download_url": "https://api.robinhood.com/documents/0-0-4-0/download/",
                "insert_4_url": "",
                "insert_2_url": "",
                "insert_6_url": "",
                "url": "https://api.robinhood.com/documents/0-0-4-0/",
                "created_at": "2018-02-01T16:17:07.579125Z",
                "insert_3_url": "",
                "id": "0-0-4-0",
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
    response = self._get_session(API, authed=True).get(API_HOST + 'documents/')
    _raise_on_error(response)
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
    response = self._get_session(API, authed=True).get(API_HOST + 'watchlists/')
    _raise_on_error(response)
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
    response = self._get_session(API, authed=True).get(API_HOST + 'watchlists/{}/'.format(watchlist_name))
    _raise_on_error(response)
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
    response = self._get_session(API, authed=True).get(API_HOST + 'settings/notifications')
    _raise_on_error(response)
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
                "url": "https://api.robinhood.com/notifications/devices/0-0-4-0/",
                "id": "0-0-4-0",
                "type": "android"
            }
        ],
        "next": null
    }
    """
    response = self._get_session(API, authed=True).get(API_HOST + 'notifications/devices/')
    _raise_on_error(response)
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
    response = self._get_session(API, authed=True).get(API_HOST + 'accounts/')
    _raise_on_error(response)
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
    response = self._get_session(API, authed=True).get(API_HOST + 'user/investment_profile/')
    _raise_on_error(response)
    return response.json()

  def get_popularity(self, instrument_id):
    """
    Example response:
    {
        "num_open_positions": 155,
        "instrument": "https://api.robinhood.com/instruments/e6f3bb44-dcdf-445b-bbcb-2e738fd21d6d/"
    }
    """
    response = self._get_session(API).get(API_HOST + 'instruments/{}/popularity/'.format(instrument_id))
    _raise_on_error(response)
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
      # HACK: This should never call a subclass' method
      my_class = self.__class__
      self.__class__ = RobinhoodClient
      full_popularities = []
      for i in range(0, len(instrument_ids), 50):
        full_popularities.extend(self.get_popularities(instrument_ids[i:i + 50]))
      self.__class__ = my_class
      return full_popularities

    params = {
        'ids': ','.join(instrument_ids),
    }
    response = self._get_session(API).get(API_HOST + 'instruments/popularity/', params=params)
    _raise_on_error(response)
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
    response = self._get_session(API).get(API_HOST + 'midlands/ratings/{}/'.format(instrument_id))
    _raise_on_error(response)
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
      # HACK: This should never call a subclass' method
      my_class = self.__class__
      self.__class__ = RobinhoodClient
      full_ratings = []
      for i in range(0, len(instrument_ids), 20):
        full_ratings.extend(self.get_ratings(instrument_ids[i:i + 20]))
      self.__class__ = my_class
      return full_ratings

    params = {
        'ids': ','.join(instrument_ids),
    }
    response = self._get_session(API).get(API_HOST + 'midlands/ratings/', params=params)
    _raise_on_error(response)
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
    response = self._get_session(ANALYTICS, authed=True).get(ANALYTICS_HOST + 'instruments/tag/{}/'.format(tag))
    _raise_on_error(response)
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
    response = self._get_session(ANALYTICS).get(ANALYTICS_HOST + 'instruments/', params=params)
    _raise_on_error(response)
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
    response = self._get_session(API).get(API_HOST + 'midlands/tags/tag/{}/'.format(tag))
    _raise_on_error(response)
    response_json = response.json()
    instrument_ids = [
        get_last_id_from_url(instrument_url) for instrument_url in response_json['instruments']
    ]
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
                "splits": "https://api.robinhood.com/instruments/0-0-4-0/splits/",
                "name": "Praetorian Property, Inc. Common Stock",
                "quote": "https://api.robinhood.com/quotes/PRRE/",
                "bloomberg_unique": "EQ0000000021483725",
                "url": "https://api.robinhood.com/instruments/0-0-4-0/",
                "type": "stock",
                "tradeable": false,
                "country": "US",
                "fundamentals": "https://api.robinhood.com/fundamentals/PRRE/",
                "market": "https://api.robinhood.com/markets/OTCM/",
                "id": "0-0-4-0",
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
      # HACK: This should never call a subclass' method
      my_class = self.__class__
      self.__class__ = RobinhoodClient
      full_instruments = []
      for i in range(0, len(instrument_ids), 75):
        full_instruments.extend(self.get_instruments(instrument_ids=instrument_ids[i:i + 75]))
      self.__class__ = my_class
      return full_instruments

    params = {
        'ids': ','.join(instrument_ids),
        'active_instruments_only': 'false',
    }
    response = self._get_session(API).get(API_HOST + 'instruments/', params=params)
    _raise_on_error(response)
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

  def get_earnings(self, instrument_id):
    """
    Args:
      instrument_id: Internal robinhood instrument id (a uuid)

    Example response:
    [
        {
            "year": 2016,
            "instrument": "https://api.robinhood.com/instruments/450dfc6d-5510-4d40-abfb-f633b7d9be3e/",
            "call": null,
            "report": {
                "date": "2016-10-25",
                "verified": true,
                "timing": "pm"
            },
            "quarter": 3,
            "symbol": "AAPL",
            "eps": {
                "actual": "1.6700",
                "estimate": "1.6500"
            }
        },
        {
            "year": 2016,
            "instrument": "https://api.robinhood.com/instruments/450dfc6d-5510-4d40-abfb-f633b7d9be3e/",
            "call": null,
            "report": {
                "date": "2017-01-31",
                "verified": true,
                "timing": "pm"
            },
            "quarter": 4,
            "symbol": "AAPL",
            "eps": {
                "actual": "3.3600",
                "estimate": "3.2200"
            }
        },
        ...
    ]
    """
    params = {
        'instrument': instrument_id_to_url(instrument_id),
        'range': '21day',
    }
    response = self._get_session(API).get(API_HOST + 'marketdata/earnings/'.format(instrument_id), params=params)
    _raise_on_error(response)
    return response.json()['results']

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
        "url": "https://api.robinhood.com/instruments/0-0-4-0/",
        "country": "US",
        "splits": "https://api.robinhood.com/instruments/0-0-4-0/splits/",
        "id": "0-0-4-0",
        "margin_initial_ratio": "1.0000",
        "tradeable": false,
        "fundamentals": "https://api.robinhood.com/fundamentals/PRRE/",
        "day_trade_ratio": "1.0000",
        "simple_name": "Praetorian Property",
        "name": "Praetorian Property, Inc. Common Stock"
    }
    """
    response = self._get_session(API).get(API_HOST + 'instruments/{}/'.format(instrument_id))
    _raise_on_error(response)
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
                "id": "0-0-4-0",
                "state": "active",
                "list_date": "1990-01-02",
                "symbol": "AAPL",
                "margin_initial_ratio": "0.5000",
                "quote": "https://api.robinhood.com/quotes/AAPL/",
                "url": "https://api.robinhood.com/instruments/0-0-4-0/",
                "name": "Apple Inc. - Common Stock",
                "splits": "https://api.robinhood.com/instruments/0-0-4-0/splits/",
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
    response = self._get_session(API).get(API_HOST + 'instruments/', params=params)
    _raise_on_error(response)
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
                "url": "https://api.robinhood.com/instruments/0-0-4-0/splits/93657cb7-478b-42b0-a23c-9a64042cb694/",
                "divisor": "1.00000000",
                "instrument": "https://api.robinhood.com/instruments/0-0-4-0/"
            }
        ]
    }
    """
    response = self._get_session(API).get(API_HOST + 'instruments/{}/splits'.format(instrument_id))
    _raise_on_error(response)
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
        "instrument": "https://api.robinhood.com/instruments/0-0-4-0/",
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
    response = self._get_session(API).get(API_HOST + 'quotes/{}/'.format(instrument_id))
    _raise_on_error(response)
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
                "instrument": "https://api.robinhood.com/instruments/0-0-4-0/",
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
      # HACK: This should never call a subclass' method
      my_class = self.__class__
      self.__class__ = RobinhoodClient
      full_quotes = []
      for i in range(0, len(instrument_ids), 35):
        full_quotes.extend(self.get_quotes(instrument_ids[i:i + 35]))
      self.__class__ = my_class
      return full_quotes

    # bounds=trading ?
    params = {
        'instruments': ','.join([
            instrument_id_to_url(instrument_id) for instrument_id in instrument_ids
        ])
    }

    response = self._get_session(API).get(API_HOST + 'quotes/', params=params)
    _raise_on_error(response)
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
      params['instruments'] = ','.join([
          instrument_id_to_url(instrument_id) for instrument_id in instrument_ids
      ])
    response = self._get_session(API).get(API_HOST + 'marketdata/prices/', params=params)
    _raise_on_error(response)
    return response.json()

  def get_dividend_by_id(self, dividend_id):
    """
    Example response:
    {
        "record_date": "2018-02-27",
        "url": "https://api.robinhood.com/dividends/0-0-4-0/",
        "payable_date": "2018-03-13",
        "paid_at": null,
        "amount": "0.84",
        "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
        "rate": "0.8400000000",
        "position": "1.0000",
        "withholding": "0.00",
        "id": "0-0-4-0",
        "instrument": "https://api.robinhood.com/instruments/0-0-4-0/"
    }
    """
    response = self._get_session(API, authed=True).get(API_HOST + 'dividends/{}/'.format(dividend_id))
    _raise_on_error(response)
    return response.json()

  def get_ach_relationships(self):
    """
    Example response:
    [
        {
            "bank_account_holder_name": "Bob Smith",
            "created_at": "2018-02-01T23:41:03.251980Z",
            "unlink": "https://api.robinhood.com/ach/relationships/0-0-4-0/unlink/",
            "id": "0-0-4-0",
            "bank_account_nickname": "MY CHECKING",
            "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
            "bank_account_number": "1234",
            "verify_micro_deposits": null,
            "withdrawal_limit": null,
            "verified": true,
            "initial_deposit": "0.00",
            "bank_routing_number": "12344567",
            "url": "https://api.robinhood.com/ach/relationships/0-0-4-0/",
            "unlinked_at": null,
            "bank_account_type": "checking",
            "verification_method": "bank_auth"
        },
        ...
    ]
    """
    response = self._get_session(API, authed=True).get(API_HOST + 'ach/relationships')
    _raise_on_error(response)
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

  def get_ach_relationship_by_id(self, relationship_id):
    """
    Example response:
    {
        "bank_account_holder_name": "Bob Smith",
        "created_at": "2018-02-01T23:41:03.251980Z",
        "unlink": "https://api.robinhood.com/ach/relationships/0-0-4-0/unlink/",
        "id": "0-0-4-0",
        "bank_account_nickname": "MY CHECKING",
        "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
        "bank_account_number": "1234",
        "verify_micro_deposits": null,
        "withdrawal_limit": null,
        "verified": true,
        "initial_deposit": "0.00",
        "bank_routing_number": "12344567",
        "url": "https://api.robinhood.com/ach/relationships/0-0-4-0/",
        "unlinked_at": null,
        "bank_account_type": "checking",
        "verification_method": "bank_auth"
    }
    """
    response = self._get_session(API, authed=True).get(API_HOST + 'ach/relationships/{}'.format(relationship_id))
    _raise_on_error(response)
    return response.json()

  def get_ach_transfer_by_id(self, transfer_id):
    """
    Example response:
    {
        "status_description": "",
        "fees": "0.00",
        "cancel": null,
        "id": "0-0-4-0",
        "created_at": "2018-02-01T05:54:32.902711Z",
        "amount": "0.00",
        "ach_relationship": "https://api.robinhood.com/ach/relationships/0-0-4-0/",
        "early_access_amount": "0.00",
        "expected_landing_date": "2018-02-08",
        "state": "pending",
        "updated_at": "2018-02-01T05:54:33.524297Z",
        "scheduled": false,
        "direction": "deposit",
        "url": "https://api.robinhood.com/ach/transfers/0-0-4-0/"
    }
    """
    response = self._get_session(API, authed=True).get(API_HOST + 'ach/transfers/{}'.format(transfer_id))
    _raise_on_error(response)
    return response.json()

  def get_ach_transfers(self):
    """
    Example response:
    [
        {
            "status_description": "",
            "fees": "0.00",
            "cancel": null,
            "id": "0-0-4-0",
            "created_at": "2018-02-01T05:54:32.902711Z",
            "amount": "0.00",
            "ach_relationship": "https://api.robinhood.com/ach/relationships/0-0-4-0/",
            "early_access_amount": "0.00",
            "expected_landing_date": "2018-02-08",
            "state": "pending",
            "updated_at": "2018-02-01T05:54:33.524297Z",
            "scheduled": false,
            "direction": "deposit",
            "url": "https://api.robinhood.com/ach/transfers/0-0-4-0/"
        },
        ...
    ]
    """
    # There's also updated_at[gte]
    response = self._get_session(API, authed=True).get(API_HOST + 'ach/transfers/')
    _raise_on_error(response)
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
                "url": "https://api.robinhood.com/dividends/0-0-4-0/",
                "payable_date": "2018-03-13",
                "paid_at": null,
                "amount": "0.84",
                "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
                "rate": "0.8400000000",
                "position": "1.0000",
                "withholding": "0.00",
                "id": "0-0-4-0",
                "instrument": "https://api.robinhood.com/instruments/0-0-4-0/"
            },
            ...
        ],
        "previous": null,
        "next": null
    }
    """
    response = self._get_session(API, authed=True).get(API_HOST + 'dividends/')
    _raise_on_error(response)
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
        "position": "https://api.robinhood.com/accounts/XXXXXXXX/positions/0-0-4-0/",
        "id": "0-0-4-0",
        "executions": [],
        "time_in_force": "gtc",
        "instrument": "https://api.robinhood.com/instruments/0-0-4-0/",
        "created_at": "2018-03-01T00:00:00.000000Z",
        "fees": "0.00",
        "updated_at": "2018-03-01T00:00:00.000000Z",
        "ref_id": "0-0-4-0",
        "side": "buy",
        "url": "https://api.robinhood.com/orders/0-0-4-0/",
        "extended_hours": true
    }
    """
    response = self._get_session(API, authed=True).get(API_HOST + 'orders/{}/'.format(order_id))
    _raise_on_error(response)
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
                "position": "https://api.robinhood.com/accounts/XXXXXXXX/positions/0-0-4-0/",
                "id": "0-0-4-0",
                "executions": [],
                "time_in_force": "gtc",
                "instrument": "https://api.robinhood.com/instruments/0-0-4-0/",
                "created_at": "2018-03-01T00:00:00.000000Z",
                "fees": "0.00",
                "updated_at": "2018-03-01T00:00:00.000000Z",
                "ref_id": "0-0-4-0",
                "side": "buy",
                "url": "https://api.robinhood.com/orders/0-0-4-0/",
                "extended_hours": true
            },
            ...
        ],
        "previous": null
    }
    """
    # HACK: This should never call a subclass' method
    my_class = self.__class__
    self.__class__ = RobinhoodClient

    params = {}
    if instrument_id:
      params['instrument'] = instrument_id_to_url(instrument_id)

    orders = self._collect_results(
        self._get_session(API, authed=True).get,
        [API_HOST + 'orders/'],
        request_params=params
    )

    self.__class__ = my_class
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

  def get_home_screen_disclosures(self):
    response = requests.get('https://brokerage-static.s3.amazonaws.com/disclosures/home_screen_disclosures.json')
    return response.json()

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
    response = self._get_session(API, authed=True).get(API_HOST + 'midlands/movers/sp500/', params=params)
    _raise_on_error(response)
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
    response = self._get_session(API, authed=True).get(API_HOST + 'portfolios/')
    _raise_on_error(response)
    return response.json()['results'][0]

  def get_portfolio_history(self, interval, span=None, use_account_number=None):
    """
    Example response:
    {
        "span": "day",
        "bounds": "trading",
        "interval": "5minute",
        "adjusted_previous_close_equity": "32.4500",
        "total_return": "0.0252",
        "adjusted_open_equity": "31.8283",
        "previous_close_equity": "32.4500",
        "open_equity": "31.8283",
        "equity_historicals": [
            {
                "session": "post",
                "close_market_value": "51.3814",
                "net_return": "0.0000",
                "close_equity": "30.3214",
                "open_equity": "30.3214",
                "open_market_value": "51.3814",
                "adjusted_close_equity": "30.3214",
                "begins_at": "2018-04-06T21:50:00Z",
                "adjusted_open_equity": "30.3214"
            },
            {
                "session": "post",
                "close_market_value": "51.3814",
                "net_return": "0.0000",
                "close_equity": "30.3214",
                "open_equity": "30.3214",
                "open_market_value": "51.3814",
                "adjusted_close_equity": "30.3214",
                "begins_at": "2018-04-06T21:55:00Z",
                "adjusted_open_equity": "30.3214"
            },
            ...
        ],
        "open_time": "2018-04-06T13:00:00Z"
    }
    """
    assert interval in INTERVALS
    account_number = use_account_number or self.get_account()['account_number']
    params = {
        'bounds': 'trading',
        'interval': '5minute',
    }
    if span:
      assert span in SPANS
      params['span'] = span
    response = self._get_session(API, authed=True).get(
        API_HOST + 'portfolios/historicals/{}/'.format(account_number), params=params)
    _raise_on_error(response)
    return response.json()

  def get_positions(self, include_old=False):
    """
    Example response:
    {
        "results": [
            {
                "created_at": "2018-02-09T15:42:15.536132Z",
                "quantity": "1.0000",
                "url": "https://api.robinhood.com/positions/XXXXXXXX/0-0-4-0/",
                "shares_held_for_buys": "0.0000",
                "updated_at": "2018-02-00T00:00:00.000000Z",
                "shares_held_for_stock_grants": "0.0000",
                "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
                "shares_held_for_options_collateral": "0.0000",
                "intraday_average_buy_price": "0.0000",
                "pending_average_buy_price": "0.0000",
                "instrument": "https://api.robinhood.com/instruments/0-0-4-0/",
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
    response = self._get_session(API, authed=True).get(API_HOST + 'positions/', params=params)
    _raise_on_error(response)
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
    response = self._get_session(API, authed=True).get(
        API_HOST + 'accounts/{}/positions/{}/'.format(account_number, instrument_id))
    _raise_on_error(response)
    return response.json()

  def get_historical_quote(self, symbol, interval, span=None, bounds=None):
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
        "instrument": "https://api.robinhood.com/instruments/0-0-4-0/",
        "quote": "https://api.robinhood.com/quotes/0-0-4-0/",
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
    """
    assert interval in INTERVALS
    params = {
        'symbol': ','.join(symbol),
        'interval': interval,
    }
    if span:
      assert span in SPANS
      params['span'] = span
    if bounds:
      assert bounds in BOUNDS
      params['bounds'] = bounds
    response = self._get_session(API).get(API_HOST + 'quotes/historicals/{}/'.format(symbol), params=params)
    _raise_on_error(response)
    return response.json()

  def get_historical_quotes(self, symbols, interval, span=None, bounds=None):
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
                "instrument": "https://api.robinhood.com/instruments/0-0-4-0/",
                "quote": "https://api.robinhood.com/quotes/0-0-4-0/",
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
    assert interval in INTERVALS
    params = {
        'symbols': ','.join(symbols),
        'interval': interval,
    }
    if span:
      assert span in SPANS
      params['span'] = span
    if bounds:
      assert bounds in BOUNDS
      params['bounds'] = bounds
    response = self._get_session(API).get(API_HOST + 'quotes/historicals/', params=params)
    _raise_on_error(response)
    return response.json()['results']

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
                "instrument": "https://api.robinhood.com/instruments/0-0-4-0/",
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
    response = self._get_session(API).get(API_HOST + 'midlands/news/{}/'.format(symbol))
    _raise_on_error(response)
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
    response = self._get_session(API).get(API_HOST + 'midlands/tags/instrument/{}/'.format(instrument_id))
    _raise_on_error(response)
    response_json = response.json()
    return response_json['tags']

  def get_fundamental(self, instrument_id):
    """
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
        "instrument": "https://api.robinhood.com/instruments/0-0-4-0/",
        "ceo": "Tim Cook",
        "volume": "24285834.0000",
        "high": "179.7750",
        "low_52_weeks": "137.0500",
        "headquarters_city": "Cupertino",
        "high_52_weeks": "180.6150",
        "year_founded": 1976
    }
    """
    response = self._get_session(API).get(API_HOST + 'fundamentals/{}/'.format(instrument_id))
    _raise_on_error(response)
    return response.json()

  def get_fundamentals(self, instrument_ids):
    """
    Example response:
    [
        {
            "description": "Apple, Inc. engages in the design, manufacture, and marketing of mobile communication, media devices, personal computers, and portable digital music players. It operates through the following geographical segments: Americas, Europe, Greater China, Japan, and Rest of Asia Pacific. The Americas segment includes both North and South America. The Europe segment consists of European countries, as well as India, the Middle East, and Africa. The Greater China segment comprises of China, Hong Kong, and Taiwan. The Rest of Asia Pacific segment includes Australia and Asian countries not included in the reportable operating segments of the company. The company was founded by Steven Paul Jobs, Ronald Gerald Wayne, and Stephen G. Wozniak on April 1, 1976 and is headquartered in Cupertino, CA.",
            "volume": "24285834.0000",
            "instrument": "https://api.robinhood.com/instruments/0-0-4-0/",
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
    if len(instrument_ids) > 35:
      # HACK: This should never call a subclass' method
      my_class = self.__class__
      self.__class__ = RobinhoodClient
      full_fundamentals = []
      for i in range(0, len(instrument_ids), 35):
        full_fundamentals.extend(self.get_fundamentals(instrument_ids[i:i + 35]))
      self.__class__ = my_class
      return full_fundamentals

    params = {
        'instruments': ','.join([
            instrument_id_to_url(instrument_id) for instrument_id in instrument_ids
        ])
    }
    response = self._get_session(API).get(API_HOST + 'fundamentals/', params=params)
    _raise_on_error(response)
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
    response = self._get_session(API, authed=True).get(API_HOST + 'midlands/referral/')
    _raise_on_error(response)
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

  def cancel_order(self, order_id):
    """
    Example response:
    {}
    """
    response = self._get_session(API, authed=True).post(API_HOST + 'orders/{}/cancel/'.format(order_id))
    _raise_on_error(response)
    return response.json()

  def order(self, instrument_id, order_type, order_side, symbol, quantity, price, use_account_url=None):
    """
    Args:
      instrument_id
      order_type: [market, limit]
      order_side: [buy, sell]
      symbol: e.g. AAPL
      quantity: Number in the transaction
      price (float): Price when buying

    Example response:
    {
        "override_day_trade_checks": false,
        "id": "0-0-4-0d",
        "cumulative_quantity": "0.00000",
        "trigger": "immediate",
        "ref_id": null,
        "state": "unconfirmed",
        "quantity": "1.00000",
        "response_category": null,
        "extended_hours": false,
        "price": "234.00000000",
        "url": "https://api.robinhood.com/orders/0-0-4-0d/",
        "fees": "0.00",
        "created_at": "2018-03-08T00:56:03.878630Z",
        "executions": [],
        "last_transaction_at": "2018-02-01T00:56:03.878630Z",
        "type": "limit",
        "side": "sell",
        "cancel": "https://api.robinhood.com/orders/0-0-4-0d/cancel/",
        "instrument": "https://api.robinhood.com/instruments/1-0-4-0/",
        "position": "https://api.robinhood.com/positions/XXXXXXXX/1-0-4-0/",
        "stop_price": null,
        "average_price": null,
        "updated_at": "2018-02-01T00:56:03.955774Z",
        "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
        "reject_reason": null,
        "time_in_force": "gtc",
        "override_dtbp_checks": false
    }
    """
    account_url = use_account_url or self.get_account()['url']
    assert order_side in ORDER_SIDES
    assert order_type in ORDER_TYPES

    body = {
        'account': account_url,
        'instrument': instrument_id_to_url(instrument_id),
        'price': price,
        'quantity': quantity,
        'side': order_side,
        'symbol': symbol,
        'time_in_force': 'gtc', # see util.TIME_IN_FORCES
        'trigger': 'immediate', # see util.TRIGGERS
        'type': order_type,
    }
    response = self._get_session(API, authed=True).post(API_HOST + 'orders/', data=body)
    _raise_on_error(response)
    return response.json()

  ### CRYPTO ###

  def get_crypto_halts(self):
    """
    Example response:
    TODO
    """
    response = self._get_session(NUMMUS, authed=True).get(NUMMUS_HOST + 'halts/')
    _raise_on_error(response)
    return response.json()['results']

  def get_crypto_activations(self):
    """
    Example response:
    [
        {
            "email": "",
            "created_at": "2018-03-29T22:30:05.307055-04:00",
            "last_name": "",
            "external_rejection_reason": "",
            "updated_at": "2018-04-08T19:50:37.457590-04:00",
            "speculative": true,
            "user_id": "0-0-0-0",
            "state": "in_review",
            "id": "1-0-0-0",
            "external_status_code": "ineligible_jurisdiction",
            "first_name": "",
            "type": "new_account",
            "external_rejection_code": "ineligible_jurisdiction"
        }
    ]
    """
    response = self._get_session(NUMMUS, authed=True).get(NUMMUS_HOST + 'activations/')
    _raise_on_error(response)
    response_json = response.json()
    assert not response_json['next']
    return response_json['results']

  def get_crypto_watchlists(self):
    """
    Example response:
    TODO
    """
    response = self._get_session(NUMMUS, authed=True).get(NUMMUS_HOST + 'watchlists/')
    _raise_on_error(response)
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

  def get_crypto_holdings(self):
    """
    Example response:
    TODO
    """
    response = self._get_session(NUMMUS, authed=True).get(NUMMUS_HOST + 'holdings/')
    _raise_on_error(response)
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

  def get_crypto_portfolio(self, portfolio_id):
    """
    Example response:
    TODO
    """
    response = self._get_session(NUMMUS, authed=True).get(NUMMUS_HOST + 'portfolios/{}/'.format(portfolio_id))
    _raise_on_error(response)
    return response.json()

  def get_crypto_portfolios(self):
    """
    Example response:
    TODO
    """
    response = self._get_session(NUMMUS, authed=True).get(NUMMUS_HOST + 'portfolios/')
    _raise_on_error(response)
    return response.json()['results']

  def get_crypto_order(self, order_id):
    """
    Example response:
    TODO
    """
    response = self._get_session(NUMMUS, authed=True).get(NUMMUS_HOST + 'orders/{}/'.format(order_id))
    _raise_on_error(response)
    return response.json()

  def get_crypto_orders(self):
    """
    Example response:
    TODO
    """
    response = self._get_session(NUMMUS, authed=True).get(NUMMUS_HOST + 'orders/')
    _raise_on_error(response)
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

  def get_crypto_currency_pairs(self):
    """
    Example response:
    [
        {
            "symbol": "BTC-USD",
            "min_order_price_increment": "0.010000000000000000",
            "id": "3d961844-d360-45fc-989b-f6fca761d511",
            "quote_currency": {
                "name": "US Dollar",
                "code": "USD",
                "id": "1072fc76-1862-41ab-82c2-485837590762",
                "type": "fiat",
                "increment": "0.010000000000000000"
            },
            "name": "Bitcoin to US Dollar",
            "tradability": "tradable",
            "min_order_size": "0.000010000000000000",
            "display_only": false,
            "min_order_quantity_increment": "0.000000010000000000",
            "max_order_size": "5.0000000000000000",
            "asset_currency": {
                "name": "Bitcoin",
                "code": "BTC",
                "id": "d674efea-e623-4396-9026-39574b92b093",
                "type": "cryptocurrency",
                "increment": "0.000000010000000000"
            }
        },
        ...
    ]
    """
    response = self._get_session(NUMMUS, authed=True).get(NUMMUS_HOST + 'currency_pairs/')
    _raise_on_error(response)
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

  def get_crypto_currency_pair(self, currency_pair_id):
    """
    Example response:
    {
        "symbol": "BTC-USD",
        "min_order_price_increment": "0.010000000000000000",
        "id": "3d961844-d360-45fc-989b-f6fca761d511",
        "quote_currency": {
            "name": "US Dollar",
            "code": "USD",
            "id": "1072fc76-1862-41ab-82c2-485837590762",
            "type": "fiat",
            "increment": "0.010000000000000000"
        },
        "name": "Bitcoin to US Dollar",
        "tradability": "tradable",
        "min_order_size": "0.000010000000000000",
        "display_only": false,
        "min_order_quantity_increment": "0.000000010000000000",
        "max_order_size": "5.0000000000000000",
        "asset_currency": {
            "name": "Bitcoin",
            "code": "BTC",
            "id": "d674efea-e623-4396-9026-39574b92b093",
            "type": "cryptocurrency",
            "increment": "0.000000010000000000"
        }
    }
    """
    response = self._get_session(NUMMUS, authed=True).get(
        NUMMUS_HOST + 'currency_pairs/{}/'.format(currency_pair_id))
    _raise_on_error(response)
    return response.json()

  def get_crypto_quote(self, symbol_or_currency_pair_id):
    """
    Example response:
    {
        "open_price": "6644.0700",
        "high_price": "7094.8800",
        "volume": "360467.1666",
        "id": "3d961844-d360-45fc-989b-f6fca761d511",
        "bid_price": "6972.1400",
        "symbol": "BTCUSD",
        "mark_price": "6984.3650",
        "low_price": "6551.3600",
        "ask_price": "6996.5900"
    }
    """
    response = self._get_session(API, authed=True).get(
        API_HOST + 'marketdata/forex/quotes/{}/'.format(symbol_or_currency_pair_id))
    _raise_on_error(response)
    return response.json()

  def get_crypto_quotes(self, currency_pair_ids=None, symbols=None):
    """
    Example response:
    [
        {
            "open_price": "6644.0700",
            "high_price": "7094.8800",
            "volume": "360467.1666",
            "id": "3d961844-d360-45fc-989b-f6fca761d511",
            "bid_price": "6972.1400",
            "symbol": "BTCUSD",
            "mark_price": "6984.3650",
            "low_price": "6551.3600",
            "ask_price": "6996.5900"
        },
        ...
    ]
    """
    assert not (symbols and currency_pair_ids)
    assert symbols or currency_pair_ids
    params = {}
    if currency_pair_ids:
      params['ids'] = ','.join(currency_pair_ids)
    if symbols:
      params['symbols'] = ','.join(symbols)
    response = self._get_session(API, authed=True).get(
        API_HOST + 'marketdata/forex/quotes/', params=params)
    _raise_on_error(response)
    return response.json()['results']

  def get_crypto_historicals(self, currency_pair_id, interval, bounds=None, span=None):
    """
    Example response:
    {
        "open_price": "6767.5400",
        "span": "day",
        "symbol": "BTCUSD",
        "previous_close_price": "6767.5400",
        "interval": "5minute",
        "id": "3d961844-d360-45fc-989b-f6fca761d511",
        "data_points": [
            {
                "open_price": "6586.0400",
                "volume": "0.0000",
                "begins_at": "2018-04-06T13:30:00Z",
                "session": "reg",
                "low_price": "6572.7050",
                "interpolated": false,
                "close_price": "6590.4750",
                "high_price": "6596.7200"
            },
            {
                "open_price": "6586.0150",
                "volume": "0.0000",
                "begins_at": "2018-04-06T13:35:00Z",
                "session": "reg",
                "low_price": "6579.1450",
                "interpolated": false,
                "close_price": "6587.2850",
                "high_price": "6594.2450"
            },
            ...
        ],
        "bounds": "regular",
        "open_time": "2018-04-06T13:30:00Z",
        "previous_close_time": "2018-04-05T20:00:00Z"
    }
    """
    assert interval in INTERVALS
    params = {
        'interval': interval,
    }
    if bounds:
      assert bounds in BOUNDS
      params['bounds'] = bounds
    if span:
      assert span in SPANS
      params['span'] = span
    response = self._get_session(API, authed=True).get(
        API_HOST + 'marketdata/forex/historicals/{}/'.format(currency_pair_id), params=params)
    _raise_on_error(response)
    return response.json()

  def cancel_crypto_order(self, order_id):
    """
    Example response:
    TODO
    """
    response = self._get_session(NUMMUS, authed=True).post(
        NUMMUS_HOST + 'orders/{}/cancel/'.format(order_id))
    _raise_on_error(response)
    return response.json()

  def order_crypto(self, currency_pair_id, order_type, order_side, quantity, price):
    """
    Example response:
    TODO
    """
    assert order_side in ORDER_SIDES
    assert order_type in ORDER_TYPES
    body = {
        'side': order_side,
        'currency_pair_id': currency_pair_id,
        'price': price,
        'quantity': quantity,
        'ref_id': str(uuid.uuid4()),
        'time_in_force': 'gtc',
        'type': order_type,
    }
    response = self._get_session(NUMMUS, authed=True).post(NUMMUS_HOST + 'orders/')
    _raise_on_error(response)
    return response.json()

  ### OPTIONS ###

  def get_options_suitability(self):
    """
    Example response:
    {
        "fields_that_need_update": [],
        "max_option_level": "option_level_2"
    }
    """
    response = self._get_session(API, authed=True).get(API_HOST + 'options/suitability/')
    _raise_on_error(response)
    return response.json()

  def get_options_position(self, position_id):
    """
    Example response:
    TODO
    """
    response = self._get_session(API, authed=True).get(API_HOST + 'options/positions/{}/'.format(position_id))
    _raise_on_error(response)
    return response.json()

  def get_options_positions(self, include_old=False):
    """
    Example response:
    TODO
    """
    params = {}
    if not include_old:
      params['nonzero'] = 'True'
    response = self._get_session(API, authed=True).get(API_HOST + 'options/positions/', params=params)
    _raise_on_error(response)
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

  def get_options_order(self, order_id):
    """
    Example response:
    {
        "response_category": null,
        "type": "limit",
        "id": "1-0-0-0",
        "cancel_url": "https://api.robinhood.com/options/orders/1-0-0-0/cancel/",
        "canceled_quantity": "0.00000",
        "trigger": "immediate",
        "price": "0.10000000",
        "premium": "10.00000000",
        "quantity": "1.00000",
        "processed_quantity": "0.00000",
        "processed_premium": "0.0000",
        "created_at": "2018-04-08T07:28:21.582166Z",
        "pending_quantity": "1.00000",
        "chain_symbol": "AAXN",
        "direction": "debit",
        "time_in_force": "gfd",
        "updated_at": "2018-04-08T07:28:21.909451Z",
        "legs": [
            {
                "ratio_quantity": 1,
                "executions": [],
                "id": "3-0-0-0",
                "side": "buy",
                "option": "https://api.robinhood.com/options/instruments/93988a72-cd5a-461a-a25d-d63cdd7d46de/",
                "position_effect": "open"
            }
        ],
        "state": "queued",
        "chain_id": "a6cb269e-d5b5-4a52-a1f6-863d6376a814",
        "ref_id": "2-0-0-0"
    }
    """
    response = self._get_session(API, authed=True).get(API_HOST + 'options/order/{}/'.format(order_id))
    _raise_on_error(response)
    return response.json()

  def get_options_orders(self):
    """
    Example response:
    [
        {
            "response_category": null,
            "type": "limit",
            "id": "1-0-0-0",
            "cancel_url": "https://api.robinhood.com/options/orders/1-0-0-0/cancel/",
            "canceled_quantity": "0.00000",
            "trigger": "immediate",
            "price": "0.10000000",
            "premium": "10.00000000",
            "quantity": "1.00000",
            "processed_quantity": "0.00000",
            "processed_premium": "0.0000",
            "created_at": "2018-04-08T07:28:21.582166Z",
            "pending_quantity": "1.00000",
            "chain_symbol": "AAXN",
            "direction": "debit",
            "time_in_force": "gfd",
            "updated_at": "2018-04-08T07:28:21.909451Z",
            "legs": [
                {
                    "ratio_quantity": 1,
                    "executions": [],
                    "id": "3-0-0-0",
                    "side": "buy",
                    "option": "https://api.robinhood.com/options/instruments/93988a72-cd5a-461a-a25d-d63cdd7d46de/",
                    "position_effect": "open"
                }
            ],
            "state": "queued",
            "chain_id": "a6cb269e-d5b5-4a52-a1f6-863d6376a814",
            "ref_id": "2-0-0-0"
        }
    ]
    """
    return self._collect_results(
        self._get_session(API, authed=True).get,
        [API_HOST + 'options/orders/']
    )

  def get_options_events(self, instrument_id=None):
    """
    Example response:
    TODO
    """
    # states=preparing seems to be passed in if instrument is
    params = {}
    if instrument_id:
      params['equity_instrument_id'] = instrument_id
    response = self._get_session(API, authed=True).get(API_HOST + 'options/events/', params=params)
    _raise_on_error(response)
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

  def get_options_marketdata(self, options_instrument_id):
    """
    Example response:
    {
        "vega": null,
        "last_trade_size": null,
        "low_price": null,
        "volume": 0,
        "implied_volatility": null,
        "break_even_price": "81.8700",
        "previous_close_date": "2018-04-05",
        "adjusted_mark_price": "0.1300",
        "bid_size": 0,
        "mark_price": "0.1250",
        "bid_price": "0.0000",
        "chance_of_profit_short": null,
        "previous_close_price": "0.0800",
        "instrument": "https://api.robinhood.com/options/instruments/73f75306-ad07-4734-972b-22ab9dec6693/",
        "ask_price": "0.2500",
        "rho": null,
        "high_price": null,
        "chance_of_profit_long": null,
        "theta": null,
        "last_trade_price": null,
        "ask_size": 62,
        "delta": null,
        "open_interest": 0,
        "gamma": null
    }
    """
    response = self._get_session(API, authed=True).get(
        API_HOST + 'marketdata/options/{}/'.format(options_instrument_id))
    _raise_on_error(response)
    response_json = response.json()
    return response_json

  def get_options_marketdatas(self, options_instrument_ids):
    """
    Example response:
    [
        {
            "vega": null,
            "last_trade_size": null,
            "low_price": null,
            "volume": 0,
            "implied_volatility": null,
            "break_even_price": "81.8700",
            "previous_close_date": "2018-04-05",
            "adjusted_mark_price": "0.1300",
            "bid_size": 0,
            "mark_price": "0.1250",
            "bid_price": "0.0000",
            "chance_of_profit_short": null,
            "previous_close_price": "0.0800",
            "instrument": "https://api.robinhood.com/options/instruments/73f75306-ad07-4734-972b-22ab9dec6693/",
            "ask_price": "0.2500",
            "rho": null,
            "high_price": null,
            "chance_of_profit_long": null,
            "theta": null,
            "last_trade_price": null,
            "ask_size": 62,
            "delta": null,
            "open_interest": 0,
            "gamma": null
        },
        ...
    ]
    """
    params = {
        'instruments': ','.join([
            options_instrument_id_to_url(options_instrument_id) for options_instrument_id in options_instrument_ids
        ]),
    }
    response = self._get_session(API, authed=True).get(API_HOST + 'marketdata/options/', params=params)
    _raise_on_error(response)
    results = response.json()['results']
    assert len(results) == len(options_instrument_ids)
    return results

  def get_options_instrument(self, options_instrument_id):
    """
    Example response:
    {
        "type": "put",
        "min_ticks": {
            "cutoff_price": "3.00",
            "below_tick": "0.05",
            "above_tick": "0.10"
        },
        "updated_at": "2018-04-07T02:10:26.762886Z",
        "created_at": "2018-03-28T04:36:05.205235Z",
        "tradability": "untradable",
        "chain_id": "a714bbf4-c17c-496a-b8e1-d38e58ee8a91",
        "state": "expired",
        "url": "https://api.robinhood.com/options/instruments/73f75306-ad07-4734-972b-22ab9dec6693/",
        "chain_symbol": "ADI",
        "expiration_date": "2018-04-06",
        "strike_price": "82.0000",
        "id": "73f75306-ad07-4734-972b-22ab9dec6693"
    }
    """
    response = self._get_session(API, authed=True).get(
        API_HOST + 'options/instruments/{}/'.format(options_instrument_id))
    _raise_on_error(response)
    response_json = response.json()
    return response_json

  def get_options_instruments(self, options_instrument_ids=None, chain_id=None, options_type=None, tradability=None, state=None, expiration_dates=None):
    """
    Example response:
    [
        {
            "type": "put",
            "min_ticks": {
                "cutoff_price": "3.00",
                "below_tick": "0.05",
                "above_tick": "0.10"
            },
            "updated_at": "2018-04-07T02:10:26.762886Z",
            "created_at": "2018-03-28T04:36:05.205235Z",
            "tradability": "untradable",
            "chain_id": "a714bbf4-c17c-496a-b8e1-d38e58ee8a91",
            "state": "expired",
            "url": "https://api.robinhood.com/options/instruments/73f75306-ad07-4734-972b-22ab9dec6693/",
            "chain_symbol": "ADI",
            "expiration_date": "2018-04-06",
            "strike_price": "82.0000",
            "id": "73f75306-ad07-4734-972b-22ab9dec6693"
        },
        ...
    ]
    """
    # Also exist: chain_id, expiration_dates
    params = {}
    if options_instrument_ids:
      params['ids'] = ','.join(options_instrument_ids),
    if chain_id:
      params['chain_id'] = chain_id
    if options_type:
      assert options_type in OPTIONS_TYPES
      params['type'] = options_type
    if state:
      assert state in OPTIONS_STATES
      params['state'] = state
    if tradability:
      assert tradability in TRADABILITY
      params['tradability'] = tradability
    if expiration_dates:
      params['expiration_dates'] = ','.join(expiration_dates)

    options_instruments = self._collect_results(
        self._get_session(API, authed=True).get,
        [API_HOST + 'options/instruments/'],
        request_params=params
    )

    return options_instruments

  def get_options_chains(self, chain_ids=None, instrument_ids=None):
    """
    Example response (for AAPL, whose instrument ids is 450dfc6d-5510-4d40-abfb-f633b7d9be3e):
    [
        {
            "id": "cee01a93-626e-4ee6-9b04-60e2fd1392d1",
            "underlying_instruments": [
                {
                    "id": "2-0-0-0",
                    "instrument": "https://api.robinhood.com/instruments/450dfc6d-5510-4d40-abfb-f633b7d9be3e/",
                    "quantity": 100
                }
            ],
            "trade_value_multiplier": "100.0000",
            "symbol": "AAPL",
            "min_ticks": {
                "cutoff_price": "3.00",
                "above_tick": "0.05",
                "below_tick": "0.01"
            },
            "can_open_position": true,
            "cash_component": null,
            "expiration_dates": [
                "2018-04-13",
                ...
            ]
        },
        {
            "id": "db268e26-e383-41a6-9d99-8ab21d6f2cba",
            "underlying_instruments": [
                {
                    "id": "1-0-0-0",
                    "instrument": "https://api.robinhood.com/instruments/450dfc6d-5510-4d40-abfb-f633b7d9be3e/",
                    "quantity": 100
                }
            ],
            "trade_value_multiplier": "100.0000",
            "symbol": "1AAPL",
            "min_ticks": {
                "cutoff_price": "3.00",
                "above_tick": "0.05",
                "below_tick": "0.01"
            },
            "can_open_position": false,
            "cash_component": null,
            "expiration_dates": []
        },
        {
            "id": "f980211b-e15d-48a8-82e8-4c9000183a09",
            "underlying_instruments": [
                {
                    "id": "0-0-0-0",
                    "instrument": "https://api.robinhood.com/instruments/450dfc6d-5510-4d40-abfb-f633b7d9be3e/",
                    "quantity": 100
                }
            ],
            "trade_value_multiplier": "100.0000",
            "symbol": "2AAPL",
            "min_ticks": {
                "cutoff_price": "3.00",
                "above_tick": "0.05",
                "below_tick": "0.01"
            },
            "can_open_position": false,
            "cash_component": null,
            "expiration_dates": []
        }
    ]
    """
    assert not (chain_ids and instrument_ids)
    params = {}
    if chain_ids:
      params['ids'] = ','.join(chain_ids),
    if instrument_ids:
      params['equity_instrument_ids'] = ','.join(instrument_ids),
    response = self._get_session(API, authed=True).get(API_HOST + 'options/chains/', params=params)
    _raise_on_error(response)
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

  def get_options_discoveries(self, chain_id):
    """
    Example response:
    [
        {
            "description": "Best if you have a strong, short-term belief that AMZN will go up.",
            "strategy_category": "bullish",
            "legs": [
                {
                    "position_effect": "open",
                    "side": "buy",
                    "option_id": "284a5f05-40dd-4d92-8b40-40ce0bc94fca"
                }
            ],
            "tags": [
                "short_term",
                "high_risk"
            ],
            "strategy_type": "buy_call"
        },
        ...
    ]
    """
    response = self._get_session(ANALYTICS, authed=True).get(ANALYTICS_HOST + 'options_discovery/{}/'.format(chain_id))
    _raise_on_error(response)
    return response.json()['results']

  def get_options_chain_collateral(self, chain_id, use_account_number=None):
    """
    This appears to return a not found if there aren't any existing holdings.

    Example response (when holdings exist):
    {
        "collateral_held_for_orders": {
            "cash": {
                "infinite": false,
                "direction": "debit",
                "amount": "0.0000"
            },
            "equities": [
                {
                    "instrument": "https://api.robinhood.com/instruments/450dfc6d-5510-4d40-abfb-f633b7d9be3e/",
                    "quantity": "0.0000",
                    "symbol": "AAPL",
                    "direction": "debit"
                }
            ]
        },
        "collateral": {
            "cash": {
                "infinite": false,
                "direction": "debit",
                "amount": "0.0000"
            },
            "equities": [
                {
                    "instrument": "https://api.robinhood.com/instruments/450dfc6d-5510-4d40-abfb-f633b7d9be3e/",
                    "quantity": "0.0000",
                    "symbol": "AAPL",
                    "direction": "debit"
                }
            ]
        }
    }
    """
    account_number = use_account_number or self.get_account()['account_number']
    params = {
        'account_number': account_number,
    }
    response = self._get_session(API, authed=True).get(
        API_HOST + 'options/chains/{}/collateral/'.format(chain_id), params=params)
    _raise_on_error(response)
    return response.json()

  def get_options_level_changes(self, use_account_url=None):
    """
    Example response:
    [
        {
            "state": "approved",
            "updated_at": "2018-03-22T14:57:49.100699Z",
            "id": "0-0-0-0",
            "account": "https://api.robinhood.com/accounts/XXXXXXXX/",
            "created_at": "2018-02-22T14:57:01.376251Z",
            "option_level": "option_level_2"
        },
        ...
    ]
    """
    account_url = use_account_url or self.get_account()['url']
    params = {
        'acount': account_url,
    }
    response = self._get_session(API, authed=True).get(API_HOST + 'options/level_changes/', params=params)
    _raise_on_error(response)
    response_json = response.json()
    # TODO: autopage
    assert not response_json['next']
    return response_json['results']

  def cancel_options_order(self, order_id):
    """
    Example response:
    {}
    """
    response = self._get_session(API, authed=True).post(API_HOST + 'options/orders/{}/cancel/'.format(order_id))
    _raise_on_error(response)
    return response.json()

  def order_options(self, options_instrument_id, order_type, direction, quantity, price, use_account_url=None):
    """
    Example response:
    {
        "response_category": null,
        "type": "limit",
        "id": "1-0-0-0",
        "cancel_url": "https://api.robinhood.com/options/orders/1-0-0-0/cancel/",
        "canceled_quantity": "0.00000",
        "trigger": "immediate",
        "price": "0.10000000",
        "premium": "10.00000000",
        "quantity": "1.00000",
        "processed_quantity": "0.00000",
        "processed_premium": "0.0000",
        "created_at": "2018-04-08T07:28:21.582166Z",
        "pending_quantity": "1.00000",
        "chain_symbol": "AAXN",
        "direction": "debit",
        "time_in_force": "gfd",
        "updated_at": "2018-04-08T07:28:21.909451Z",
        "legs": [
            {
                "ratio_quantity": 1,
                "executions": [],
                "id": "3-0-0-0",
                "side": "buy",
                "option": "https://api.robinhood.com/options/instruments/93988a72-cd5a-461a-a25d-d63cdd7d46de/",
                "position_effect": "open"
            }
        ],
        "state": "queued",
        "chain_id": "a6cb269e-d5b5-4a52-a1f6-863d6376a814",
        "ref_id": "0-0-0-0"
    }
    """
    assert order_type in ORDER_TYPES
    assert direction in DIRECTIONS
    account_url = use_account_url or self.get_account()['url']
    body = {
        'account': account_url,
        'direction': direction,
        'legs': [{
            'side': DIRECTION_TO_ORDER_SIDE[direction],
            'option': options_instrument_id_to_url(options_instrument_id),
            'position_effect': 'open',
            'ratio_quantity': 1,
        }],
        'price': price,
        'quantity': quantity,
        'ref_id': str(uuid.uuid4()),
        'time_in_force': 'gtc',
        'type': order_type,
    }

    # Unlike everything else until now, the api wants json...
    custom_headers = {
        'Content-type': 'application/json; charset=utf-8',
    }
    response = self._get_session(API, authed=True).post(
        API_HOST + 'options/orders/', data=json.dumps(body), headers=custom_headers)
    _raise_on_error(response)
    return response.json()
