#!/usr/bin/env python3

import json

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient

# Set up the client
client = RobinhoodCachedClient()
client.login()


def generate_orders():
  for order in client.get_orders():
    # TODO: go through order
    # TODO: get instrument
    pass


if __name__ == '__main__':
  generate_orders()
