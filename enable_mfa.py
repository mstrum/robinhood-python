#!/usr/bin/env python3

import argparse
import json

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient, FORCE_LIVE

# Set up the client
client = RobinhoodCachedClient()
client.login()

SMS = 'sms'
APP = 'app'

def enable_mfa(mfa_source):
  if mfa_source == APP:
    request_mfa_details = client.request_app_mfa()
    totp_token = request_mfa_details['totp_token']
    print('Your time-based one-time password token is: {}'.format(totp_token))
    otp = input("After entering into your app, please enter a one time code: ")
    verify_details = client.verify_app_mfa(otp)

  elif mfa_source == SMS:
    phone_number = input("What phone number would you like to receive for MFA codes? ")
    sms_details = client.request_sms_mfa(phone_number)
    print('You should be getting a code sent to {}'.format(sms_details['phone_number']))
    otp = input("Please enter the code you are sent: ")
    verify_details = client.verify_sms_mfa(otp)

  if not verify_details['enabled']:
    print('It looks like something went wrong, unable to setup MFA.')
    exit()

  print("It looks you're good to go!")
  backup = client.get_mfa_backup()
  print("If you lose access to your MFA device, your backup code is: {}".format(backup['backup_code']))
  print('Keep it secret, keep it safe.')


if __name__ == '__main__':
  mfa_details = client.get_mfa()
  if mfa_details['enabled']:
    challenge_type = mfa_details['challenge_type']
    print('It looks like MFA is already enabled (using {}), nothing to do here.'.format(challenge_type))
    exit()

  parser = argparse.ArgumentParser(description='Enable MFA on your Robinhood account')
  parser.add_argument('mfa_source', choices=[SMS, APP])
  args = parser.parse_args()
  enable_mfa(args.mfa_source)
