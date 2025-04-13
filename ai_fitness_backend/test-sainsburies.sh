curl 'https://www.sainsburys.co.uk/groceries-api/gol-services/product/v1/product?filter\[keyword\]=cheese&include\[PRODUCT_AD\]=citrus&citrus_max_number_ads=5&page_number=1&page_size=60&sort_order=FAVOURITES_FIRST&salesWindow=1' \
  -H 'accept: application/json' \
  -H 'accept-language: en-US,en;q=0.9' \
  -H 'content-type: application/json' \
  -H 'referer: https://www.sainsburys.co.uk/gol-ui/SearchResults/cheese' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-fetch-dest: empty' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36' \
  -H 'wcauthtoken;'