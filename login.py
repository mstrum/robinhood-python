#!/usr/bin/env python3

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient


client = RobinhoodCachedClient()
client.login()
print('Logged in!')
