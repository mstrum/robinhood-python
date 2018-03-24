# robinhood-python
Robinhood module in Python

Some current caveats:
* Development has been in python 3, I'm not taking much care to keep python 2 support at the moment.
* The scripts currently default to extreme caching policies, use --live to guarantee most recent data.
* Much of the code will assert (or not) in scenarioes where states and paging is involved where they haven't been handled correctly yet

## Module

* [RobinhoodClient](robinhood/RobinhoodClient.py)
  * Client that handles getting data from the Robinhood APIs
  * TODO
    * Some more APIs likely need paging support
* [RobinhoodCachedClient](robinhood/RobinhoodClient.py)
  * Client that handles caching on top of the normal client
  * TODO
    * Handle more fine grained caching then on vs off (e.g. off, 5minute, 1day, etc.)
      * Use sane defaults everywhere (E.g. heavy on instruments and soft on quotes)
    * Historical quotes

## Scripts

* login.py
  * Forces a new login and caches the token. Note most scripts will do this
    automatically so you usually don't need to call this.
* logout.py
  * Invalidates the current auth token and deletes the cached token

Various downloads:
* generate_portfolio.py [--live]
  * Current positions with various stats
* download_history.py [--live]
  * Downloads all account history (orders, dividends, transfers, rewards, margin, etc.)
* generate_documents.py [--live]
  * Documents (including PDFs) that you've received

Display information:
* show_quote.py AMZN [--live]
  * Displays the latest quote for the given symbol along with auxilary info
  * TODO
    * day trade check
    * day trade buying power check
* show_pending_orders.py
  * Displays any outstanding orders along with position information
* show_interesting_stocks.py
  * Show stocks that are on various lists
    * 10 popular S&P 500 stocks with Robinhood users
    * S&P 500 top movers up and down
    * Top 10 and 100 popular sticks with Robinhood users
  * TODO:
    * Movements into/outof lists?

Perform actions:
* order.py market|limit buy|sell SYMBOL QUANTITY PRICE
  * Prints the quote for the given symbol, confirms, and places an order

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

## Todo

* Mix in some IEX data
