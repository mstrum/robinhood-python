# robinhood-python
Robinhood module in Python

*Warning* This is in HEAVY, early development and will completely change underneath you if you try to rely on it.

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

* logout.py
  * Calls logout on Robinhood if currently logged in and deletes the local auth token cache
* quote.py AMZN
  * Returns the latest quote for the given symbol along with auxilary info
* generate_portfolio.py
  * Will download a shapshot of the current portfolio
  * TODO
    * Add current equity values
* ./generate_orders.py
  * Will download a shapshot of all fulfilled orders
* ./generate_dividends.py
  * Will download a shapshot of all dividends past and future
* ./generate_documents.py
  * Will download a shapshot of all documents including the PDFs
* ./generate_tag_list.py [10-most-popular|100-most-popular]
  * Will download a list of the most popular instruments
* TODO
  * ./report.py
    * Unlike generate_portfolio, includes:
      * Dividends received
      * Positions that were fully sold
      * Profit/losses from sales
  * ./potentials.py
    * Will show a view combining portfolio and watching symbols and show ones I may be interested in.
      * Positions I'm in that I want to increase
      * Positions I'm watching, especially if I have criteria
  * ./order.py
    * Will handle any order scenario
    * TODO:
      * Market buy
      * Market sell
      * Limit buy
      * Limit sell
