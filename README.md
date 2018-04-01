# robinhood-python
Robinhood module in Python

Some current caveats:
* Development has been in python 3, I'm not taking much care to keep python 2 support at the moment.
* The scripts currently default to extreme caching policies, use --live to guarantee most recent data.
* Much of the code will assert (or not) in scenarioes where states and paging is involved where they haven't been handled correctly yet

## Module

* [RobinhoodClient](robinhood/RobinhoodClient.py)
  * Client that handles getting data from the Robinhood APIs
* [RobinhoodCachedClient](robinhood/RobinhoodClient.py)
  * Client that handles caching on top of the normal client
  * TODO
    * Handle more fine grained caching then on vs off (e.g. off, 5minute, 1day, etc.)
      * Use sane defaults everywhere (E.g. heavy on instruments and soft on quotes)
    * Historical quotes

## Scripts

* [login.py](login.py)
  * Forces a new login and caches the token. Note most scripts will do this
    automatically so you usually don't need to call this.
* [logout.py](logout.py)
  * Invalidates the current auth token and deletes the cached token

Various downloads:
* [download_portfolio.py](download_portfolio.py) [--live]
  * Current positions with various stats
* [download_history.py](download_history.py) [--live]
  * Downloads all account history (orders, dividends, transfers, rewards, margin, etc.)
* [download_documents.py](download_documents.py) [--live]
  * Documents (including PDFs) that you've received

Display information:
* [show_quote.py](show_quote.py) AMZN [--live]
  * Displays the latest quote for the given symbol along with auxilary info
* [show_pending_orders.py](show_pending_orders.py)
  * Displays any outstanding orders along with position information
* [show_interesting_stocks.py](show_interesting_stocks.py)
  * Show stocks that are on various lists
    * 10 popular S&P 500 stocks with Robinhood users
    * S&P 500 top movers up and down
    * Top 10 and 100 popular sticks with Robinhood users
  * TODO:
    * Movements into/outof lists?
* [show_potentials.py](show_potentials.py)
  * Show stocks and some stats to help decide on positions to push forward on.

Perform actions:
* [order.py](order.py) [market|limit] [buy|sell] SYMBOL QUANTITY PRICE [--no-cancel]
  * Prints the quote for the given symbol, confirms, and places an order
* [cancel.py](cancel.py) ORDER_ID...
  * Cancels one or more order ids given, or all pending orders if none given

Scripts to add:
* download_summary.py
  * Will download a shapshot of a very high level summary
  * TODO
    * Total buy in
    * Total buy out
    * Total dividend
    * Total change
    * Total change %
    * Total dividends
    * Positions sold out of

## Todo

* Mix in some IEX data

## Legal

* This library may have bugs which could result in financial consequences, you are responsible for anything you execute. Inspect the underlying code if you want to be sure it's doing what you think it should be doing.
* I am not affiliated with Robinhood and this library uses an undocumented API. If you have any questions about them, contact Robinhood directly: https://robinhood.com/
