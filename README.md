# robinhood-python
Robinhood module in Python

*Warning* This is in HEAVY, early development and will completely change underneath you if you try to rely on it.

## scripts
* ./logout.py
  * Calls logout on Robinhood if currently logged in and deletes the local auth token cache
* ./quote.py AMZN
  * Returns the latest quote for the given symbol along with auxilary info

To-create
* ./order.py
  * Will handle any order scenario
* ./portfolio.py
  * Will show a portfolio view
* ./potentials.py
  * Will show a view combining portfolio and watching symbols and show ones I may be interested in.
    * Positions I'm in that I want to increase
    * Positions I'm watching, especially if I have criteria

## Todo
* Deal with paging in a reusable and out-of-site manner
* Cache as much data as possible
  * Orders that are fulfilled/canceled/etc. don't need to be downloaded twice
  * TopX probably don't need to be updated more than like once a day
  * Can probably cache portofio numbers for at least 5 minutes
  * Any historical grabs
