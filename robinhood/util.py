from urllib.parse import parse_qs, urlparse
import os

CURRENT_DIRECTORY = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
API_HOST = 'https://api.robinhood.com/'
CERT_BUNDLE_PATH = os.path.join(CURRENT_DIRECTORY, 'certs', 'all.pem')
ANALYTICS_HOST = 'https://analytics.robinhood.com/'
NUMMUS_HOST = 'https://nummus.robinhood.com/'
NUMMUS = 'NUMMUS'
API = 'API'
ANALYTICS = 'ANALYTICS'


ORDER_TYPES = [
    'market',
    'limit',
]
ORDER_SIDES = [
    'buy',
    'sell',
]
TIME_IN_FORCES = [
    'gfd',
    'gtc',
    'ioc',
    'opg',
]
TRIGGERS = [
    'immediate',
    'stop',
]
ORDER_STATES = [
    'queued',
    'unconfirmed',
    'confirmed',
    'partially_filled',
    'filled',
    'rejected',
    'canceled',
    'failed',
]
TRADABILITY = [
    'tradable',
    'untradable',
]
INTERVALS = [
    '15second',
    '5minute',
    '10minute',
    'hour',
    'day',
    'week',
]
SPANS = [
    'day',
    'hour',
    'week',
    'year',
    '5year',
    'all',
]
BOUNDS = [
    '24_7',
    'regular',
    'extended',
    'trading',
]
OPTIONS_TYPES = [
    'put',
    'call',
]
OPTIONS_STATES = [
    'active',
    'inactive',
    'expired',
]
DIRECTIONS = [
    'debit',
    'credit',
]
DIRECTION_TO_SIDE = {
    'debit': 'buy',
    'credit': 'sell',
}
SIDE_TO_DIRECTION = {
    'buy': 'debit',
    'sell': 'credit',
}


def get_last_id_from_url(url):
  item_id = urlparse(url).path.split('/')[-2]
  # Make sure this is in the expected format
  assert len(item_id) == 36  # UUID v4 length
  assert item_id[14] == '4'  # UUID v4 marker
  return item_id


def get_cursor_from_url(url):
  parsed_query = parse_qs(urlparse(url).query)
  assert 'cursor' in parsed_query
  assert len(parsed_query.get('cursor', [])) == 1
  cursor = parsed_query['cursor'][0]
  assert cursor
  return cursor


def get_document_download_url_from_id(document_id):
  return '{}documents/{}/download/'.format(API_HOST, document_id)


def instrument_id_to_url(instrument_id):
  return '{}instruments/{}/'.format(API_HOST, instrument_id)

def options_instrument_id_to_url(instrument_id):
  return '{}options/instruments/{}/'.format(API_HOST, instrument_id)
