"""
This asks for the username and password, saving a token into a credentials
file at ~/.robinhood/credentials:

[account]
AuthToken = MYAUTHTOKEN

"""

import configparser
import getpass

from robinhood.RobinhoodClient import RobinhoodClient

# Set up the client
client = RobinhoodClient()

# Get an auth token
username = input('Username: ')
password = getpass.getpass()
print('What is the airspeed velocity of an unladen swallow')
auth_token = client.set_auth_token_with_credentials(username, password)

# Cache the account number while we're at it
account = client.get_account()
account_number = account['account_number']

# Write it out
config = configparser.ConfigParser()
config.read(['.creds'])
if 'account' not in config.sections():
  config['account'] = {}

with open('.creds', 'w') as credentials_file:
  config.set('account', 'AuthToken', auth_token)
  config.set('account', 'AccountNumber', account_number)
  config.write(credentials_file)
