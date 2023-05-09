import requests
from yahoo_fin.stock_info import *
quote = get_live_price("reliance.ns")
print(quote)