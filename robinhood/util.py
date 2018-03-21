from urllib.parse import parse_qs, urlparse

API_HOST = 'https://api.robinhood.com/'
ANALYTICS_HOST = 'https://analytics.robinhood.com/'

KNOWN_TAGS = [
  '100-most-popular',
  '10-most-popular',
  'top-movers',
  # Personal tag
  'for-you',
]
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


def get_instrument_url_from_id(instrument_id):
  return '{}instruments/{}/'.format(API_HOST, instrument_id)
