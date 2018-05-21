#!/usr/bin/env python3

import argparse
import json
import os
import shutil

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, CACHE_FIRST, FORCE_LIVE
from robinhood.RobinhoodPortfolio import RobinhoodPortfolio

# Set up the client
client = RobinhoodCachedClient()
client.login()


def show_potentials(decay_priority, cache_mode):
  portfolio = RobinhoodPortfolio(client, {'cache_mode': cache_mode})

  # Load sentiment if available.
  if os.path.exists('sentiment.json'):
    with open('sentiment.json', 'r') as sentiment_file:
      sentiment_json = json.load(sentiment_file)
    shutil.copyfile('sentiment.json', 'sentiment.old.json')
  else:
    sentiment_json = {}

  # Delete any equities that were sold off.
  sentiment_symbols = sentiment_json.keys()
  for symbol in sentiment_symbols:
    if symbol not in portfolio.symbols:
      del sentiment_json[symbol]

  # Add any new ones.
  for symbol in portfolio.symbols:
    if symbol not in sentiment_json:
      sentiment_json[symbol] = {}

  # Bump up priority if there are any p0
  if decay_priority:
    highest_priority = min(p.get('priority', 9999) for p in sentiment_json.values())
    if highest_priority == 0:
      for position in sentiment_json.values():
        position_pority = position.get('priority')
        if position_pority is not None:
          position['priority'] += 1

  with open('sentiment.json', 'w') as sentiment_file:
    json.dump(sentiment_json, sentiment_file, indent=4)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Show various position potentials to buy into')
  parser.add_argument(
      '--live',
      action='store_true',
      help='Force to not use cache for APIs where values change'
  )
  parser.add_argument(
      '--decay-priority',
      action='store_true',
      help='Lower the priority of everything'
  )
  args = parser.parse_args()
  show_potentials(
      args.decay_priority,
      FORCE_LIVE if args.live else CACHE_FIRST
  )
