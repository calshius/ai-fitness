import logging
import scrapy
from scrapy.crawler import CrawlerProcess
from abc import ABC, abstractmethod
from typing import List, Dict, Any

logger = logging.getLogger("ai_fitness_api")

class BaseScraper(ABC):
    """Base class for all supermarket scrapers"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.results = []
        
    @abstractmethod
    async def search_product(self, product_name: str) -> List[Dict[str, Any]]:
        """
        Search for a product in the supermarket
        
        Args:
            product_name: The name of the product to search for
            
        Returns:
            A list of product dictionaries with at least the following keys:
            - name: The name of the product
            - price: The price of the product
            - unit_price: The price per unit (e.g., per kg)
            - url: The URL to the product page
            - image_url: The URL to the product image
            - supermarket: The name of the supermarket
        """
        pass
    
    def _format_result(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format the product data to a standard format"""
        required_keys = ['name', 'price', 'unit_price', 'url', 'image_url']
        
        # Ensure all required keys are present
        for key in required_keys:
            if key not in product_data:
                product_data[key] = None
                
        # Add supermarket name
        product_data['supermarket'] = self.name.replace('Scraper', '')
        
        return product_data
