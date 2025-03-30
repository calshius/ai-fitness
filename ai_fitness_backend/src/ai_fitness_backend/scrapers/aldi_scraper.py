import logging
import json
import aiohttp
from typing import List, Dict, Any
from ..scrapers.base_scraper import BaseScraper

logger = logging.getLogger("ai_fitness_api")

class AldiScraper(BaseScraper):
    """Scraper for Aldi supermarket"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.aldi.co.uk/search"
        self.api_url = "https://www.aldi.co.uk/api/product-search"
        
    async def search_product(self, product_name: str) -> List[Dict[str, Any]]:
        """Search for a product in Aldi"""
        logger.info(f"Searching for {product_name} in Aldi")
        
        params = {
            "q": product_name,
            "page": 1,
            "count": 10
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
                        logger.error(f"Error searching Aldi: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error searching Aldi: {str(e)}")
            return []
            
    def _parse_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the results from the Aldi API"""
        results = []
        
        try:
            products = data.get('results', [])
            
            for product in products:
                # Extract price information
                price = product.get('price', {}).get('value', 0.0)
                
                # Extract unit price information
                unit_price = product.get('pricePerUnit', {}).get('value', 0.0)
                
                product_data = {
                    'name': product.get('name', ''),
                    'price': price,
                    'unit_price': unit_price,
                    'url': f"https://www.aldi.co.uk{product.get('url', '')}",
                    'image_url': product.get('image', ''),
                }
                
                results.append(self._format_result(product_data))
                
        except Exception as e:
            logger.error(f"Error parsing Aldi results: {str(e)}")
            
        return results