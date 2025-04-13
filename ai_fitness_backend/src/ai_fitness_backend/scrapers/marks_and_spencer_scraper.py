import logging
import json
import re
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Tuple, Optional
from ..scrapers.base_scraper import BaseScraper

logger = logging.getLogger("ai_fitness_api")


class MarksAndSpencerScraper(BaseScraper):
    """Scraper for Marks & Spencer supermarket"""

    def __init__(self):
        super().__init__()
        self.search_url = "https://www.marksandspencer.com/search"
        self.base_url = "https://www.marksandspencer.com"

    async def search_product(self, product_name: str) -> List[Dict[str, Any]]:
        """Search for a product in Marks & Spencer"""
        logger.info(f"Searching for {product_name} in Marks & Spencer")
        
        # First, get the final URL after all redirects
        initial_url = f"{self.search_url}?searchType=normal&searchTerm={product_name}"
        final_url = await self._get_final_redirect_url(initial_url)
        
        if not final_url:
            logger.error("Failed to get final redirect URL")
            return []
        
        logger.info(f"Final URL after redirects: {final_url}")
        
        # Now make the actual request to the final URL
        html_content = await self._make_api_request(final_url)
        
        if not html_content:
            logger.error("Failed to get HTML content from final URL")
            return []
        
        # Parse the HTML content
        return self._parse_html_results(html_content, product_name)

    async def _get_final_redirect_url(self, url: str) -> Optional[str]:
        """Follow redirects and return the final URL"""
        headers = self._get_headers()
        cookie_str = self._get_cookie_string()
        headers["Cookie"] = cookie_str
        
        logger.info(f"Following redirects from: {url}")
        logger.info(f"Using cookie: {cookie_str}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Make a HEAD request first to follow redirects without downloading content
                async with session.head(
                    url,
                    headers=headers,
                    allow_redirects=True,
                    max_redirects=10
                ) as response:
                    final_url = str(response.url)
                    logger.info(f"Final URL after redirects: {final_url}")
                    return final_url
                    
        except Exception as e:
            logger.error(f"Error following redirects: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def _make_api_request(self, url: str) -> Optional[str]:
        """Make the actual API request to the given URL"""
        headers = self._get_headers()
        cookie_str = self._get_cookie_string()
        headers["Cookie"] = cookie_str
        
        # Add referer header for the actual request
        headers["referer"] = self.base_url
        
        logger.info(f"Making API request to: {url}")
        
        # Maximum number of retries
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=30)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    logger.info(f"Request attempt {attempt + 1}/{max_retries}")
                    
                    async with session.get(
                        url,
                        headers=headers,
                        allow_redirects=True  # Allow redirects for simplicity
                    ) as response:
                        if response.status == 200:
                            html_content = await response.text()
                            logger.info(f"API request successful")
                            return html_content
                        else:
                            logger.error(f"Error in API request: {response.status}")
                
                # Wait before retrying (exponential backoff)
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time} seconds before retrying...")
                    await asyncio.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Error in API request (attempt {attempt + 1}): {str(e)}")
                
                # Wait before retrying (exponential backoff)
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time} seconds before retrying...")
                    await asyncio.sleep(wait_time)
        
        logger.error(f"Failed to make API request after {max_retries} attempts")
        return None

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for the request"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "accept": "application/json",  # Match the test script
            "accept-language": "en-US,en;q=0.8",
            "dnt": "1",
            "priority": "u=0, i",
            "sec-ch-ua": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "sec-gpc": "1",
            "upgrade-insecure-requests": "1"
        }

    def _get_cookie_string(self) -> str:
        """Get cookie string for the request"""
        store_cookie = {"id": "657", "name": "GLASGOW ARGYLE STREET"}
        country_cookie = "GB"
        return f'MS_FOOD_STORE={json.dumps(store_cookie)}; MS_ORIGIN_COUNTRY={country_cookie};'

    def _parse_html_results(
        self, html_content: str, product_name: str
    ) -> List[Dict[str, Any]]:
        """Parse the HTML results from the Marks & Spencer website"""
        results = []

        try:
            # Extract the __NEXT_DATA__ JSON from the HTML
            next_data_match = re.search(
                r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
                html_content,
                re.DOTALL,
            )

            if not next_data_match:
                logger.warning("Could not find __NEXT_DATA__ in the HTML response")
                return self._parse_html_fallback(html_content, product_name)

            next_data_json = next_data_match.group(1)
            data = json.loads(next_data_json)

            # Log a sample of the data structure to help with debugging
            logger.debug(
                f"JSON data structure keys: {list(data.get('props', {}).get('pageProps', {}).keys())}"
            )

            # Navigate to the product list at the specified path
            product_lists = (
                data.get("props", {})
                .get("pageProps", {})
                .get("viewModel", {})
                .get("productSearch", {})
                .get("productLists", {})
            )

            if not product_lists:
                logger.warning("Could not find product lists in the JSON data")
                return self._parse_html_fallback(html_content, product_name)

            # Get the ranged products
            ranged_products = product_lists.get("ranged", [])

            if not ranged_products:
                logger.warning("No ranged products found in the JSON data")
                return self._parse_html_fallback(html_content, product_name)

            logger.info(f"Found {len(ranged_products)} products in M&S response")

            # Filter products by the search term if provided
            search_term_lower = product_name.lower()

            for product in ranged_products:
                try:
                    # Check if the product matches the search term
                    product_title = product.get("title", "")

                    # Skip if the product doesn't match the search term
                    if (
                        search_term_lower
                        and search_term_lower not in product_title.lower()
                    ):
                        continue

                    # Extract product details
                    product_id = product.get("id", "")
                    seo_url = product.get("seoUrl", "")
                    image_url = product.get("imageUrl", "")
                    price_text = product.get("price", "£0.00").replace("£", "")
                    unit_price = product.get("unitPrice", "")
                    weight = product.get("weight", "")
                    brand = product.get("brand", "")
                    labels = product.get("labels", [])
                    stock_info = product.get("stockLevelIndicator", {})
                    stock_status = stock_info.get("label", "Unknown")

                    # Log the raw price data for debugging
                    logger.debug(
                        f"Raw price data for {product_title}: {product.get('price')}"
                    )

                    # Convert price to float
                    try:
                        price = float(price_text)
                    except ValueError:
                        price = 0.0

                    # Construct full URLs
                    full_url = f"https://www.marksandspencer.com{seo_url}"
                    full_image_url = (
                        f"https://asset1.marksandspencer.com/is/image/mands/{image_url}"
                        if image_url
                        else ""
                    )

                    # Create a formatted product name that includes labels if present
                    formatted_name = product_title
                    if weight:
                        formatted_name += f" {weight}"

                    # Add labels as tags
                    tags = []
                    if labels:
                        tags = labels

                    product_data = {
                        "name": formatted_name.strip(),
                        "price": price,
                        "unit_price": unit_price,
                        "url": full_url,
                        "image_url": full_image_url,
                        "brand": brand or "Marks & Spencer",
                        "weight": weight,
                        "tags": tags,
                        "stock_status": stock_status,
                    }

                    results.append(self._format_result(product_data))
                except Exception as e:
                    logger.error(f"Error parsing product: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing M&S HTML results: {str(e)}")
            return self._parse_html_fallback(html_content, product_name)

        return results

    def _parse_html_fallback(
        self, html_content: str, product_name: str
    ) -> List[Dict[str, Any]]:
        """Fallback method to parse HTML directly if JSON extraction fails"""
        results = []

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Look for product cards in the HTML
            product_cards = soup.select(".product-card")

            if not product_cards:
                logger.warning("No product cards found in HTML")
                return []

            logger.info(f"Found {len(product_cards)} product cards in HTML")

            for card in product_cards:
                try:
                    # Extract product name
                    name_elem = card.select_one(".product-card__title")
                    product_name = (
                        name_elem.text.strip() if name_elem else "Unknown Product"
                    )

                    # Extract price
                    price_elem = card.select_one(".product-card__price")
                    price_text = (
                        price_elem.text.strip().replace("£", "")
                        if price_elem
                        else "0.00"
                    )

                    # Convert price to float
                    try:
                        price = float(price_text)
                    except ValueError:
                        price = 0.0

                    # Extract URL
                    url_elem = card.select_one("a.product-card__link")
                    url = url_elem.get("href", "") if url_elem else ""
                    full_url = (
                        f"https://www.marksandspencer.com{url}"
                        if url.startswith("/")
                        else url
                    )

                    # Extract image URL
                    img_elem = card.select_one("img.product-card__image")
                    image_url = img_elem.get("src", "") if img_elem else ""

                    # Extract unit price if available
                    unit_price_elem = card.select_one(".product-card__unit-price")
                    unit_price = unit_price_elem.text.strip() if unit_price_elem else ""

                    # Extract weight if available
                    weight_elem = card.select_one(".product-card__size")
                    weight = weight_elem.text.strip() if weight_elem else ""

                    # Extract labels/tags if available
                    tags = []
                    label_elems = card.select(".product-card__badge")
                    for label_elem in label_elems:
                        if label_elem and label_elem.text.strip():
                            tags.append(label_elem.text.strip())

                    product_data = {
                        "name": product_name,
                        "price": price,
                        "unit_price": unit_price,
                        "url": full_url,
                        "image_url": image_url,
                        "brand": "Marks & Spencer",
                        "weight": weight,
                        "tags": tags,
                        "stock_status": "Unknown",  # Not easily available in HTML
                    }

                    results.append(self._format_result(product_data))
                except Exception as e:
                    logger.error(f"Error parsing product card: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in HTML fallback parsing: {str(e)}")

        return results
