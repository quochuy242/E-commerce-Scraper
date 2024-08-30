import time

import requests

uniqlo_product_url = "https://www.uniqlo.com/vn/api/commerce/v3/vi/products?path=%2C%2C23257&limit=24&offset=72&isV2Review=true"


start_time = time.time()
response = requests.get(url=uniqlo_product_url)
print(f"Request took {time.time() - start_time} seconds")
