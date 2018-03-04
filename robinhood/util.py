from urllib.parse import parse_qs, urlparse

API_HOST = 'https://api.robinhood.com/'

KNOWN_TAGS = [
  '100-most-popular',
  '10-most-popular',
]


def get_instrument_id_from_url(instrument_url):
  instrument_id = urlparse(instrument_url).path.split('/')[-2]
  # Make sure this is in the expected format
  assert len(instrument_id) == 36  # UUID v4 length
  assert instrument_id[14] == '4'  # UUID v4 marker
  return instrument_id


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
