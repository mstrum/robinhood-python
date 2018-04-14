#!/usr/bin/env python3

import argparse
import json

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, FORCE_LIVE

# Set up the client
client = RobinhoodCachedClient()
client.login()

mfa_details = client.get_mfa()
if not mfa_details['enabled']:
  print('It looks like MFA is already disabled, nothing to do here.')
  exit()
else:
  confirm = input('Are you sure you want to disable MFA? [N/y] ')
  if confirm not in ['y', 'yes']:
    print('Bailed out!')
    exit()

client.remove_mfa()
print('Disabled MFA :( Try me again soon.')
