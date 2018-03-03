# robinhood-python
Robinhood module in Python

*Warning* This is in HEAVY, early development and will completely change underneath you if you try to rely on it.

## Module

* robinhood.RobinhoodClient
  * Client that handles getting data from the Robinhood APIs
  * TODO
    * Deal with paging in a reusable and out-of-mind manner
* robinhood.RobinhoodCachedClient
  * Client that handles caching on top of the normal client
  * TODO
    * Handle more fine graned caching then on vs off (e.g. off, 5minute, 1day, etc.)
    * Orders
    * TopX lists
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
* TODO
  * ./orders.py
    * Will download a shapshot of all fulfilled orders
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
