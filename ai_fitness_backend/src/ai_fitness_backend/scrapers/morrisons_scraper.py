import logging
import aiohttp
import json
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from ..scrapers.base_scraper import BaseScraper

logger = logging.getLogger("ai_fitness_api")


class MorrisonsScraper(BaseScraper):
    """Scraper for Morrisons supermarket"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://groceries.morrisons.com/search"

    async def search_product(self, product_name: str) -> List[Dict[str, Any]]:
        """Search for a product in Morrisons"""
        logger.info(f"Searching for {product_name} in Morrisons")

        params = {"q": product_name}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        try:
            # Configure client session with appropriate settings
            conn = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(
                connector=conn, timeout=timeout
            ) as session:
                async with session.get(
                    self.base_url, params=params, headers=headers, allow_redirects=True
                ) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        return self._extract_product_listing_data(html_content)
                    else:
                        logger.error(f"Error searching Morrisons: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error searching Morrisons: {str(e)}")
            return []

    def _extract_product_listing_data(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract product data from the product-listing-structured-data script tag"""
        results = []

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Find the script tag with product listing structured data
            product_listing_script = soup.find(
                "script", attrs={"data-test": "product-listing-structured-data"}
            )

            if product_listing_script and product_listing_script.string:
                try:
                    # Parse the JSON data
                    data = json.loads(product_listing_script.string)

                    # Extract the item list elements
                    items = data.get("itemListElement", [])

                    logger.info(f"Found {len(items)} products in structured data")

                    # Process each item
                    for item in items:
                        try:
                            # Get the product URL
                            url = item.get("url", "")

                            # Extract product details from the URL
                            product_name = (
                                url.split("/")[-2].replace("-", " ").title()
                                if url
                                else "Unknown Product"
                            )

                            # Create a product entry with available information
                            product_data = {
                                "name": product_name,
                                "price": 0.0,  # Price not available in this data
                                "unit_price": "",  # Unit price not available in this data
                                "url": url,
                                "image_url": "",  # Image URL not available in this data
                            }

                            results.append(self._format_result(product_data))
                        except Exception as e:
                            logger.error(f"Error processing product item: {str(e)}")
                            continue
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON from script tag: {str(e)}")
            else:
                logger.warning(
                    "Could not find product-listing-structured-data script tag"
                )

                # If we can't find the specific script tag, try to find any script with product data
                all_scripts = soup.find_all("script")
                for script in all_scripts:
                    if script.string and '"itemListElement"' in script.string:
                        try:
                            # Try to extract JSON data
                            match = re.search(
                                r'({.*"itemListElement":\s*\[.*\].*})', script.string
                            )
                            if match:
                                data = json.loads(match.group(1))
                                items = data.get("itemListElement", [])

                                logger.info(
                                    f"Found {len(items)} products in alternative script tag"
                                )

                                for item in items:
                                    try:
                                        url = item.get("url", "")
                                        product_name = (
                                            url.split("/")[-2].replace("-", " ").title()
                                            if url
                                            else "Unknown Product"
                                        )

                                        product_data = {
                                            "name": product_name,
                                            "price": 0.0,
                                            "unit_price": "",
                                            "url": url,
                                            "image_url": "",
                                        }

                                        results.append(
                                            self._format_result(product_data)
                                        )
                                    except Exception as e:
                                        logger.error(
                                            f"Error processing product item: {str(e)}"
                                        )
                                        continue
                        except Exception as e:
                            logger.error(f"Error extracting JSON from script: {str(e)}")
                            continue

            # If we still have no results, try to fetch additional details for each product
            if results:
                logger.info(f"Successfully extracted {len(results)} products")
            else:
                logger.warning("Could not extract any products from the HTML")

        except Exception as e:
            logger.error(f"Error extracting product listing data: {str(e)}")

        return results
