import re
from typing import Dict, List, Optional

def extract_food_suggestions(text: str) -> Dict[str, List[str]]:
    """
    Extract food suggestions from the LLM response.
    Returns a dictionary with meal types as keys and lists of food items as values.
    """
    suggestions = {
        "breakfast": [],
        "lunch": [],
        "dinner": []
    }
    
    # Simple parsing logic - look for food suggestions section and extract items
    lines = text.split('\n')
    current_meal = None
    
    # Check if we have a FOOD SUGGESTIONS section
    food_section_found = False
    for i, line in enumerate(lines):
        if "FOOD SUGGESTIONS:" in line.upper():
            food_section_found = True
            break
    
    if not food_section_found:
        return suggestions
    
    # Parse the food suggestions
    for line in lines:
        line = line.strip().lower()
        
        if "breakfast" in line:
            current_meal = "breakfast"
            # Try to extract items if they're on the same line
            if ":" in line:
                items = line.split(":", 1)[1].strip()
                if items:
                    suggestions["breakfast"] = [item.strip() for item in items.split(",")]
        elif "lunch" in line:
            current_meal = "lunch"
            # Try to extract items if they're on the same line
            if ":" in line:
                items = line.split(":", 1)[1].strip()
                if items:
                    suggestions["lunch"] = [item.strip() for item in items.split(",")]
        elif "dinner" in line:
            current_meal = "dinner"
            # Try to extract items if they're on the same line
            if ":" in line:
                items = line.split(":", 1)[1].strip()
                if items:
                    suggestions["dinner"] = [item.strip() for item in items.split(",")]
        elif current_meal and "," in line and not line.startswith("-") and not line.startswith("•"):
            # This is likely a comma-separated list of food items
            suggestions[current_meal] = [item.strip() for item in line.split(",")]
    
    return suggestions
