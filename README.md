# robinhood-python
Robinhood module in Python

Some current caveats:
* Development has been in python 3, I'm not taking much care to keep python 2 support at the moment.
* The scripts currently default to extreme caching policies, use --live to guarantee most recent data.
* Much of the code will assert (or not) in scenarioes where states and paging is involved where they haven't been handled correctly yet

## Module

* robinhood.RobinhoodClient
  * Client that handles getting data from the Robinhood APIs
  * TODO
    * Some APIs likely need paging support, I've personally added as needed
* robinhood.RobinhoodCachedClient
  * Client that handles caching on top of the normal client
  * TODO
    * Handle more fine grained caching then on vs off (e.g. off, 5minute, 1day, etc.)
    * Historical quotes

## Scripts

* logout.py
  * Invalidates the current auth token and deletes the cached token

Various downloads:
* generate_portfolio.py
  * Current positions with various stats
* generate_orders.py
  * Fulfilled orders
  * TODO
    * Add in referral rewards
    * Handle pending orders
* generate_dividends.py
  * All dividends, received or planned
* generate_transfers.py
  * ACH bank transfers
* generate_documents.py
  * Documents (including PDFs) that you've received
* generate_rewards.py
  * Referral rewards you've gotten

Display information:
* quote.py AMZN
  * Displays the latest quote for the given symbol along with auxilary info
  * TODO
    * day trade check
    * day trade buying power check

Perform actions:
* order.py
  * Prints the quote for the given symbol, confirms, and places an order

Generic lists:
* generate_tag_list.py [10-most-popular|100-most-popular]
  * Stocks that have the given tag
  * TODO
    * Show symbols that have entered/left the list since the last run
* generate_popular_stocks.py
  * Most popular stocks in Robinhood as of Sunday
* generate_sp500_movers.py
  * Top movers, both down and up, from the S&P 500

Scripts to add:
* generate_summary.py
  * Will download a shapshot of a very high level summary
  * TODO
    * Total buy in
    * Total buy out
    * Total dividend
    * Total change
    * Total change %
* report.py
  * Unlike generate_portfolio, includes:
    * Dividends received
    * Positions that were fully sold
    * Profit/losses from sales
* potentials.py
  * Will show a view combining portfolio and watching symbols and show ones I may be interested in.
    * Positions I'm in that I want to increase
    * Positions I'm watching, especially if I have criteria
