import logging
import scrapy
import json
import aiohttp
from typing import List, Dict, Any
from ..scrapers.base_scraper import BaseScraper

logger = logging.getLogger("ai_fitness_api")

class TescoScraper(BaseScraper):
    """Scraper for Tesco supermarket"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.tesco.com/groceries/en-GB/search"
        self.api_url = "https://www.tesco.com/groceries/en-GB/resources/product-data/search"
        
    async def search_product(self, product_name: str) -> List[Dict[str, Any]]:
        """Search for a product in Tesco"""
        logger.info(f"Searching for {product_name} in Tesco")
        
        params = {
            "query": product_name,
            "page": 1,
            "count": 10
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_results(data)
                    else:
                        logger.error(f"Error searching Tesco: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error searching Tesco: {str(e)}")
            return []
            
    def _parse_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the results from the Tesco API"""
        results = []
        
        try:
            products = data.get('products', [])
            
            for product in products:
                product_data = {
                    'name': product.get('name', ''),
                    'price': product.get('price', 0.0),
                    'unit_price': product.get('unitPrice', {}).get('price', 0.0),
                    'url': f"https://www.tesco.com{product.get('url', '')}",
                    'image_url': product.get('image', ''),
                }
                
                results.append(self._format_result(product_data))
                
        except Exception as e:
            logger.error(f"Error parsing Tesco results: {str(e)}")
            
        return results
