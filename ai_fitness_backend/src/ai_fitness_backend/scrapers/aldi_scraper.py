import logging
import aiohttp
from typing import List, Dict, Any
from ..scrapers.base_scraper import BaseScraper

logger = logging.getLogger("ai_fitness_api")


class AldiScraper(BaseScraper):
    """Scraper for Aldi supermarket"""

    def __init__(self):
        super().__init__()
        self.api_url = "https://api.aldi.co.uk/v3/product-search"

    async def search_product(self, product_name: str) -> List[Dict[str, Any]]:
        """Search for a product in Aldi"""
        logger.info(f"Searching for {product_name} in Aldi")

        params = {
            "currency": "GBP",
            "serviceType": "walk-in",
            "q": product_name,
            "limit": 30,
            "offset": 0,
            "sort": "relevance",
            "testVariant": "A",
            "servicePoint": "C092",  # This might need to be configurable
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json",
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
                        logger.error(f"Error searching Aldi: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error searching Aldi: {str(e)}")
            return []

    def _parse_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the results from the Aldi API"""
        results = []

        try:
            products = data.get("data", [])

            logger.info(f"Found {len(products)} products in Aldi response")

            for product in products:
                try:
                    # Extract product details
                    name = product.get("name", "")
                    brand = product.get("brandName", "")

                    # Extract price information
                    price_info = product.get("price", {})
                    price_amount = price_info.get("amount", 0)
                    # Convert from pence to pounds
                    price = (
                        float(price_amount) / 100 if price_amount is not None else 0.0
                    )

                    # Extract unit price information
                    comparison_price = price_info.get("comparison", 0)
                    comparison_display = price_info.get("comparisonDisplay", "")
                    unit_price = comparison_display if comparison_display else ""

                    # Construct the product URL
                    url_slug = product.get("urlSlugText", "")
                    url = f"https://www.aldi.co.uk/p/{url_slug}" if url_slug else ""

                    # Extract image URL
                    image_url = ""
                    assets = product.get("assets", [])
                    if assets and len(assets) > 0:
                        asset = assets[0]
                        # Replace {width} and {slug} in the URL template
                        image_url = asset.get("url", "")
                        if image_url:
                            image_url = image_url.replace("{width}", "800").replace(
                                "{slug}", url_slug
                            )

                    # Extract size information
                    size = product.get("sellingSize", "")

                    product_data = {
                        "name": name,
                        "price": price,
                        "unit_price": unit_price,
                        "url": url,
                        "image_url": image_url,
                        "size": size,
                        "brand": brand,
                    }

                    results.append(self._format_result(product_data))
                except Exception as e:
                    logger.error(f"Error parsing Aldi product: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing Aldi results: {str(e)}")

        return results
