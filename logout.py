"""
This asks for the username and password, saving a token into a credentials
file at ~/.robinhood/credentials:

[account]
AuthToken = MYAUTHTOKEN
"""

import configparser


config = configparser.ConfigParser()
config.read(['.creds'])
if not config.get('account', 'AuthToken'):
  print('Nothing to see here...')
  exit()

with open('.creds', 'w') as credentials_file:
  config.remove_option('account', 'AuthToken')
  config.write(credentials_file)
  print('Logged out!')
