from urllib.parse import urlparse


def get_instrument_id_from_url(instrument_url):
  instrument_id = urlparse(instrument_url).path.split('/')[-2]
  # Make sure this is in the expected format
  assert len(instrument_id) == 36  # UUID v4 length
  assert instrument_id[14] == '4'  # UUID v4 marker
  return instrument_id
