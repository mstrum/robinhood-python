# robinhood-python
Robinhood module in Python

*Warning* This is in HEAVY, early development and will completely change underneath you if you try to rely on it.

## scripts
* ./logout.py
  * Calls logout on Robinhood if currently logged in and deletes the local auth token cache
* ./quote.py AMZN
  * Returns the latest quote for the given symbol along with auxilary info
* ./generate_portfolio.py
  * Will download a shapshot of the current portfolio

To-create
* ./order.py
  * Will handle any order scenario
* ./potentials.py
  * Will show a view combining portfolio and watching symbols and show ones I may be interested in.
    * Positions I'm in that I want to increase
    * Positions I'm watching, especially if I have criteria

## Todo
* Deal with paging in a reusable and out-of-mind manner
* Cache as much data as possible
  * Handle more fine graned caching then on vs off
    * E.g. off, 5minute, 1day, etc.
  * Orders
  * TopX lists
  * Historical quotes
