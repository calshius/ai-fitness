import logging
import aiohttp
import json
from typing import List, Dict, Any
from ..scrapers.base_scraper import BaseScraper

logger = logging.getLogger("ai_fitness_api")


class MorrisonsScraper(BaseScraper):
    """Scraper for Morrisons supermarket"""

    def __init__(self):
        super().__init__()
        self.api_url = "https://groceries.morrisons.com/api/v6/products/search"

    async def search_product(self, product_name: str) -> List[Dict[str, Any]]:
        """Search for a product in Morrisons"""
        logger.info(f"Searching for {product_name} in Morrisons")

        params = {"term": product_name}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "accept": "application/json; charset=utf-8",
            "accept-language": "en-US,en;q=0.6",
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
                        logger.error(f"Error searching Morrisons: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error searching Morrisons: {str(e)}")
            return []

    def _parse_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the results from the Morrisons API"""
        results = []

        try:
            # Extract products from the entities.product object
            products = data.get("entities", {}).get("product", {})

            logger.info(f"Found {len(products)} products in Morrisons response")

            for product_id, product in products.items():
                try:
                    # Extract product details
                    name = product.get("name", "")

                    # Extract price information
                    price_info = product.get("price", {}).get("current", {})
                    price = float(price_info.get("amount", 0.0)) if price_info else 0.0

                    # Extract unit price information
                    unit_price_info = (
                        product.get("price", {}).get("unit", {}).get("current", {})
                    )
                    unit_price = (
                        unit_price_info.get("amount", "") if unit_price_info else ""
                    )
                    unit_label = (
                        product.get("price", {}).get("unit", {}).get("label", "")
                    )

                    # Format unit price with label
                    formatted_unit_price = (
                        f"{unit_price} {unit_label}"
                        if unit_price and unit_label
                        else ""
                    )

                    # Extract retailer product ID
                    retailer_id = product.get("retailerProductId", "")

                    # Construct the product URL
                    url = f"https://groceries.morrisons.com/products/{name.lower().replace(' ', '-')}/{retailer_id}"

                    # Extract image URL
                    image_info = product.get("image", {})
                    image_url = image_info.get("src", "") if image_info else ""

                    # Extract size information
                    size = product.get("size", {}).get("value", "")

                    # Extract brand
                    brand = product.get("brand", "")

                    product_data = {
                        "name": name,
                        "price": price,
                        "unit_price": formatted_unit_price,
                        "url": url,
                        "image_url": image_url,
                        "size": size,
                        "brand": brand,
                    }

                    results.append(self._format_result(product_data))
                except Exception as e:
                    logger.error(f"Error parsing product: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing Morrisons results: {str(e)}")

        return results
