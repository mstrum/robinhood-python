#!/usr/bin/env python3

import argparse
import csv

from robinhood.RobinhoodCachedClient import RobinhoodCachedClient

# Set up the client
client = RobinhoodCachedClient()
client.login()


def download_documents(live):
  with open('documents.csv', 'w', newline='') as csv_file:
    fieldnames = ['document_id', 'date', 'type', 'path']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    for document in client.get_documents(force_live=live):
      document_id = document['id']
      document_type = document['type']
      document_date = document['date']

      contents = client.download_document_by_id(document_id)
      pdf_path = 'document_{}.pdf'.format(document_id)
      with open(pdf_path, 'wb') as document_pdf_file:
        document_pdf_file.write(contents)

      csv_writer.writerow({
        'document_id': document_id,
        'date': document_date,
        'type': document_type,
        'path': pdf_path,
      })


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Download a list of your documents')
  parser.add_argument('--live', action='store_true', help='Force to not use cache for APIs where values change')
  args = parser.parse_args()
  download_documents(args.live)
