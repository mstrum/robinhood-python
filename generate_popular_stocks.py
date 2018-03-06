#!/usr/bin/env python3

import csv

import requests

# This is only updated on Sunday
response = requests.get('https://brokerage-static.s3.amazonaws.com/popular_stocks/data.json')
response_json = response.json()
assert len(response_json) == 1
popular_list = response_json[0]

with open('popular.csv', 'w', newline='') as csv_file:
  fieldnames = ['symbol', 'name']
  csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
  csv_writer.writeheader()
  for popular_symbol in popular_list['data']:
    csv_writer.writerow({
      'symbol': popular_symbol['symbol'],
      'name': popular_symbol['subtitle'],
    })
