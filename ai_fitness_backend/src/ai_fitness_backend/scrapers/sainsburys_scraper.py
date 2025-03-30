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
        self.base_url = "https://www.sainsburys.co.uk/gol-ui/SearchResults"
        self.api_url = "https://www.sainsburys.co.uk/groceries-api/gol-services/product/v1/product"
        
    async def search_product(self, product_name: str) -> List[Dict[str, Any]]:
        """Search for a product in Sainsbury's"""
        logger.info(f"Searching for {product_name} in Sainsbury's")
        
        params = {
            "searchTerm": product_name,
            "page": 1,
            "pageSize": 10
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=params, headers=headers) as response:
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
            products = data.get('products', [])
            
            for product in products:
                # Extract price information
                price_info = product.get('retail', {}).get('price', {})
                price = price_info.get('price', 0.0)
                
                # Extract unit price information
                unit_price_info = product.get('retail', {}).get('unitPrice', {})
                unit_price = unit_price_info.get('price', 0.0)
                
                product_data = {
                    'name': product.get('name', ''),
                    'price': price,
                    'unit_price': unit_price,
                    'url': f"https://www.sainsburys.co.uk/shop/gb/groceries/product/details/{product.get('id', '')}",
                    'image_url': product.get('image', ''),
                }
                
                results.append(self._format_result(product_data))
                
        except Exception as e:
            logger.error(f"Error parsing Sainsbury's results: {str(e)}")
            
        return results