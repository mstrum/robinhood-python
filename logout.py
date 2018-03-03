"""
This asks for the username and password, saving a token into a credentials
file at ~/.robinhood/credentials:

[account]
AuthToken = MYAUTHTOKEN
"""
from robinhood.RobinhoodCachedClient import RobinhoodCachedClient

client = RobinhoodCachedClient()
client.logout()
print('Logged out!')
