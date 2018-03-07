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
    * Some APIs likely need paging support (only orders has it for now)
* robinhood.RobinhoodCachedClient
  * Client that handles caching on top of the normal client
  * TODO
    * Handle more fine grained caching then on vs off (e.g. off, 5minute, 1day, etc.)
    * Historical quotes

## Scripts

Lists dealing with the user and assets
* logout.py
  * Calls logout on Robinhood if currently logged in and deletes the local auth token cache
* quote.py AMZN
  * Returns the latest quote for the given symbol along with auxilary info
  * TODO
    * day trade check
    * day trade buying power check
* generate_portfolio.py
  * Will download a shapshot of the current portfolio
  * TODO
    * Add current equity values
    * Equity value %
    * Total equity index
    * Day change
    * Total change?
* generate_orders.py
  * Will download a shapshot of all fulfilled orders
  * TODO
    * Add in referral rewards
    * Handle pending orders
* generate_dividends.py
  * Will download a shapshot of all dividends past and future
* generate_transfers.py
  * Download the history of bank transfers
* generate_documents.py
  * Will download a shapshot of all documents including the PDFs
* generate_rewards.py
  * Will download a shapshot of the referral rewards you've gotten

Generic lists:
* generate_tag_list.py [10-most-popular|100-most-popular]
  * Will download a list of the most popular instruments
  * TODO
    * Show symbols that have entered/left the list since the last run
* generate_popular_stocks.py
  * Download the 10 most popular stocks in Robinhood as of Sunday
* generate_sp500_movers.py
  * Download the top movers, both down and up, from the S&P 500

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
* order.py
  * Will handle any order scenario
  * TODO:
    * Market buy
    * Market sell
    * Limit buy
    * Limit sell
