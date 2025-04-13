import logging
import json
import aiohttp
from typing import List, Dict, Any
from ..scrapers.base_scraper import BaseScraper

logger = logging.getLogger("ai_fitness_api")


class SainsburysScraper(BaseScraper):
    """Scraper for Sainsbury's supermarket"""

    def __init__(self):
        super().__init__()
        self.api_url = (
            "https://www.sainsburys.co.uk/groceries-api/gol-services/product/v1/product"
        )

    async def search_product(self, product_name: str) -> List[Dict[str, Any]]:
        """Search for a product in Sainsbury's"""
        logger.info(f"Searching for {product_name} in Sainsbury's")

        # Construct the query parameters as shown in the test-sainsburies.sh script
        params = {
            "filter[keyword]": product_name,
            "include[PRODUCT_AD]": "citrus",
            "citrus_max_number_ads": "5",
            "page_number": "1",
            "page_size": "60",
            "sort_order": "FAVOURITES_FIRST",
            "salesWindow": "1",
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "accept": "application/json",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "referer": f"https://www.sainsburys.co.uk/gol-ui/SearchResults/{product_name}",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.api_url, params=params, headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_results(data)
                    else:
                        logger.error(f"Error searching Sainsbury's: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error searching Sainsbury's: {str(e)}")
            return []

    def _parse_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the results from the Sainsbury's API"""
        results = []

        try:
            # Extract products from the response
            products = data.get("products", [])

            logger.info(f"Found {len(products)} products in Sainsbury's response")

            for product in products:
                try:
                    # Extract the full_url
                    full_url = product.get("full_url", "")

                    # Extract other product details
                    name = product.get("name", "")

                    # Extract price information
                    retail_price = product.get("retail_price", {})
                    price = retail_price.get("price", 0.0) if retail_price else 0.0

                    # Extract unit price information
                    unit_price_info = product.get("unit_price", {})
                    unit_price = (
                        unit_price_info.get("price", 0.0) if unit_price_info else 0.0
                    )

                    # Extract image URL
                    image_url = product.get("image", "")

                    product_data = {
                        "name": name,
                        "price": price,
                        "unit_price": unit_price,
                        "url": full_url,
                        "image_url": image_url,
                    }

                    results.append(self._format_result(product_data))
                except Exception as e:
                    logger.error(f"Error parsing product: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing Sainsbury's results: {str(e)}")

        return results
