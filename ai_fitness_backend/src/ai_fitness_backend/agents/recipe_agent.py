import logging
import re
from typing import List, Dict, Any, Optional
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

from ..scrapers.tesco_scraper import TescoScraper
from ..scrapers.sainsburys_scraper import SainsburysScraper
from ..scrapers.morrisons_scraper import MorrisonsScraper
from ..scrapers.marks_and_spencer_scraper import MarksAndSpencerScraper
from ..scrapers.aldi_scraper import AldiScraper
from ..llm import get_llm_response, get_llm_client

logger = logging.getLogger("ai_fitness_api")


class RecipeAgent:
    """Agent for generating recipes based on macro requirements using LangChain"""

    def __init__(self):
        self.scrapers = {
            "tesco": TescoScraper(),
            "sainsburys": SainsburysScraper(),
            "morrisons": MorrisonsScraper(),
            "marks_spencer": MarksAndSpencerScraper(),
            "aldi": AldiScraper(),
        }

        # Initialize LangChain components
        # Using a simple OpenAI LLM for LangChain - you can replace this with your preferred LLM
        self.llm = get_llm_client(temperature=0.7)
        self.memory = ConversationBufferMemory(memory_key="chat_history")
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent_executor()

    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools from the agent's capabilities"""

        tools = [
            Tool(
                name="GetIngredients",
                func=self._get_ingredients_tool,
                description="Searches for ingredients in supermarkets. Input should be a comma-separated list of food items.",
            ),
            Tool(
                name="GetFoodSuggestions",
                func=self._get_food_suggestions_tool,
                description="Gets food suggestions based on macro requirements. Input should be a JSON string with protein, carbs, fat, calories, and meal_type.",
            ),
            Tool(
                name="GenerateRecipeInstructions",
                func=self._generate_recipe_instructions_tool,
                description="Generates recipe instructions for given food items. Input should be a JSON string with food_items list and meal_type.",
            ),
        ]

        return tools

    def _create_agent_executor(self) -> AgentExecutor:
        """Create the LangChain agent executor"""

        # Define the prompt template for the agent
        prompt = PromptTemplate.from_template(
            """You are a nutrition expert and chef specializing in meal planning based on macronutrient requirements.
            
            You have access to the following tools:
            
            {tools}
            
            Use the following format:
            
            Question: the input question you must answer
            Thought: you should always think about what to do
            Action: the action to take, should be one of [{tool_names}]
            Action Input: the input to the action
            Observation: the result of the action
            ... (this Thought/Action/Action Input/Observation can repeat N times)
            Thought: I now know the final answer
            Final Answer: the final answer to the original input question
            
            Begin!
            
            Question: {input}
            Thought: {agent_scratchpad}
            """
        )

        # Create the agent
        agent = create_react_agent(llm=self.llm, tools=self.tools, prompt=prompt)

        # Create the agent executor
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
        )

        return agent_executor

    async def _get_ingredients_tool(self, input_str: str) -> str:
        """Tool for getting ingredients"""
        try:
            # Parse input - expecting comma-separated food items
            food_items = [item.strip() for item in input_str.split(",")]
            supermarket = None  # Default to all supermarkets

            # Get ingredients
            ingredients = await self.get_ingredients(food_items, supermarket)
            return str(ingredients)
        except Exception as e:
            logger.error(f"Error in GetIngredients tool: {str(e)}")
            return f"Error getting ingredients: {str(e)}"

    async def _get_food_suggestions_tool(self, input_str: str) -> str:
        """Tool for getting food suggestions"""
        try:
            # Parse input - expecting JSON string
            import json

            input_data = json.loads(input_str)

            macros = {
                "protein": input_data.get("protein"),
                "carbs": input_data.get("carbs"),
                "fat": input_data.get("fat"),
                "calories": input_data.get("calories"),
            }
            meal_type = input_data.get("meal_type")

            # Get food suggestions
            suggestions = await self.get_food_suggestions_from_llm(macros, meal_type)
            return str(suggestions)
        except Exception as e:
            logger.error(f"Error in GetFoodSuggestions tool: {str(e)}")
            return f"Error getting food suggestions: {str(e)}"

    async def _generate_recipe_instructions_tool(self, input_str: str) -> str:
        """Tool for generating recipe instructions"""
        try:
            # Parse input - expecting JSON string
            import json

            input_data = json.loads(input_str)

            food_items = input_data.get("food_items", [])
            meal_type = input_data.get("meal_type")

            # Generate recipe instructions
            recipe_name, instructions = await self.generate_recipe_instructions(
                food_items, meal_type
            )
            return json.dumps({"name": recipe_name, "instructions": instructions})
        except Exception as e:
            logger.error(f"Error in GenerateRecipeInstructions tool: {str(e)}")
            return f"Error generating recipe instructions: {str(e)}"

    async def process_recipe_request(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a recipe request using the LangChain agent

        Args:
            request_data: Dictionary with request parameters

        Returns:
            The generated recipe plan
        """
        try:
            # Extract request parameters
            macros = {
                "protein": request_data.get("protein"),
                "carbs": request_data.get("carbs"),
                "fat": request_data.get("fat"),
                "calories": request_data.get("calories"),
            }
            meal_type = request_data.get("meal_type")
            food_items = request_data.get("food_items", [])
            supermarket = request_data.get("supermarket")

            # Determine the task based on provided parameters
            if food_items and not any(macros.values()):
                # If only food items are provided, just get ingredients
                ingredients = await self.get_ingredients(food_items, supermarket)
                recipe_name, instructions = await self.generate_recipe_instructions(
                    food_items, meal_type
                )

                return {
                    "name": recipe_name,
                    "ingredients": ingredients,
                    "instructions": instructions,
                    "meal_type": meal_type,
                }
            else:
                # Generate a complete meal plan
                return await self.generate_meal_plan(macros, meal_type, supermarket)
        except Exception as e:
            logger.error(f"Error processing recipe request: {str(e)}")
            raise e

    async def get_ingredients(
        self, food_items: List[str], supermarket: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get ingredients for a list of food items

        Args:
            food_items: List of food items to search for
            supermarket: Optional supermarket to search in. If None, search in all supermarkets.

        Returns:
            A list of ingredients with their details
        """
        logger.info(f"Getting ingredients for {food_items}")

        results = []

        # Determine which scrapers to use
        scrapers_to_use = []
        if supermarket and supermarket.lower() in self.scrapers:
            scrapers_to_use = [self.scrapers[supermarket.lower()]]
        else:
            scrapers_to_use = list(self.scrapers.values())

        # Search for each food item
        for food_item in food_items:
            item_results = []

            for scraper in scrapers_to_use:
                try:
                    scraper_results = await scraper.search_product(food_item)
                    item_results.extend(scraper_results)
                except Exception as e:
                    logger.error(f"Error with {scraper.name} for {food_item}: {str(e)}")

            # If we found results, add the best one
            if item_results:
                # Sort by price (assuming lower is better)
                item_results.sort(
                    key=lambda x: float(x["price"]) if x["price"] else float("inf")
                )
                results.append(item_results[0])

        return results

    async def get_food_suggestions_from_llm(
        self, macros: Dict[str, float], meal_type: str = None
    ) -> List[str]:
        """
        Get food suggestions from LLM based on macro requirements and meal type

        Args:
            macros: Dictionary with macro requirements (protein, carbs, fat, calories)
            meal_type: Optional meal type (breakfast, lunch, dinner)

        Returns:
            A list of suggested food items
        """
        logger.info(f"Getting food suggestions for {meal_type} with macros {macros}")

        # Create a prompt for the LLM
        prompt = f"""
        Based on the following macro requirements:
        - Protein: {macros.get("protein", "N/A")}g
        - Carbs: {macros.get("carbs", "N/A")}g
        - Fat: {macros.get("fat", "N/A")}g
        - Calories: {macros.get("calories", "N/A")}
        
        Please suggest 5-7 specific food items for a {meal_type if meal_type else "balanced"} meal.
        
        Format your response as a simple comma-separated list of food items.
        For example: chicken breast, brown rice, broccoli, olive oil, sweet potato
        """

        system_role = "You are a nutrition expert specializing in meal planning based on macronutrient requirements."

        try:
            # Get response from LLM
            response = get_llm_response(prompt, system_role)

            # Extract food items from response
            # Remove any bullet points, numbers, or other formatting
            clean_response = re.sub(
                r"^\s*[-•*\d]+\s*", "", response, flags=re.MULTILINE
            )

            # Split by commas and clean up each item
            food_items = [item.strip() for item in clean_response.split(",")]

            # Filter out empty items
            food_items = [item for item in food_items if item]

            logger.info(f"LLM suggested food items: {food_items}")

            return food_items
        except Exception as e:
            logger.error(f"Error getting food suggestions from LLM: {str(e)}")

            # Fall back to default food items if LLM fails
            default_items = {
                "breakfast": ["eggs", "oatmeal", "greek yogurt", "banana", "berries"],
                "lunch": [
                    "chicken breast",
                    "brown rice",
                    "broccoli",
                    "olive oil",
                    "sweet potato",
                ],
                "dinner": ["salmon", "quinoa", "asparagus", "avocado", "lemon"],
                "default": [
                    "chicken breast",
                    "rice",
                    "vegetables",
                    "olive oil",
                    "nuts",
                ],
            }

            if meal_type in default_items:
                return default_items[meal_type]
            return default_items["default"]

    async def generate_meal_plan(
        self, macros: Dict[str, float], meal_type: str = None, supermarket: str = None
    ) -> Dict[str, Any]:
        """
        Generate a meal plan based on macro requirements

        Args:
            macros: Dictionary with macro requirements (protein, carbs, fat, calories)
            meal_type: Optional meal type (breakfast, lunch, dinner)
            supermarket: Optional supermarket to search in

        Returns:
            A meal plan with recipes and ingredients
        """
        logger.info(f"Generating meal plan for {meal_type} with macros {macros}")

        # Get food suggestions from LLM
        food_items = await self.get_food_suggestions_from_llm(macros, meal_type)

        # Get ingredients for the food items
        ingredients = await self.get_ingredients(food_items, supermarket)

        # Generate recipe instructions using LLM
        recipe_name, instructions = await self.generate_recipe_instructions(
            food_items, meal_type
        )

        # Create the recipe
        recipe = {
            "name": recipe_name,
            "ingredients": ingredients,
            "instructions": instructions,
            "macros": macros,
            "meal_type": meal_type,
        }

        return recipe

    async def generate_recipe_instructions(
        self, food_items: List[str], meal_type: str = None
    ) -> tuple:
        """
        Generate recipe instructions using LLM

        Args:
            food_items: List of food items
            meal_type: Optional meal type (breakfast, lunch, dinner)

        Returns:
            Tuple of (recipe_name, instructions_list)
        """
        food_items_str = ", ".join(food_items)

        prompt = f"""
        Create a simple recipe using these ingredients: {food_items_str}
        
        This is for a {meal_type if meal_type else "balanced"} meal.
        
        Please provide:
        1. A creative name for the recipe
        2. Step-by-step cooking instructions (maximum 5 steps)
        
        Format your response as:
        RECIPE NAME: [Your recipe name here]
        
        INSTRUCTIONS:
        1. [First step]
        2. [Second step]
        ...
        """

        system_role = "You are a professional chef specializing in healthy, macro-friendly recipes."

        try:
            # Get response from LLM
            response = get_llm_response(prompt, system_role)

            # Extract recipe name
            name_match = re.search(
                r"RECIPE NAME:\s*(.*?)(?:\n|$)", response, re.IGNORECASE
            )
            recipe_name = (
                name_match.group(1).strip()
                if name_match
                else f"{meal_type.capitalize() if meal_type else 'Balanced'} Meal"
            )

            # Extract instructions
            instructions_text = re.search(
                r"INSTRUCTIONS:(.*?)(?:\n\n|$)", response, re.DOTALL | re.IGNORECASE
            )
            if instructions_text:
                # Extract instructions
                instructions_text = re.search(
                    r"INSTRUCTIONS:(.*?)(?:\n\n|$)", response, re.DOTALL | re.IGNORECASE
                )
                if instructions_text:
                    # Extract numbered steps
                    steps = re.findall(
                        r"^\s*\d+\.\s*(.*?)$", instructions_text.group(1), re.MULTILINE
                    )
                    instructions = [step.strip() for step in steps if step.strip()]
                else:
                    # Fallback instructions
                    instructions = [
                        "Prepare all ingredients.",
                        "Cook protein source according to package instructions.",
                        "Prepare carbohydrates and vegetables.",
                        "Combine all ingredients and serve.",
                    ]

                return recipe_name, instructions

        except Exception as e:
            logger.error(f"Error generating recipe instructions: {str(e)}")

            # Fallback recipe name and instructions
            default_name = f"{meal_type.capitalize() if meal_type else 'Balanced'} Meal"
            default_instructions = [
                "Prepare all ingredients.",
                "Cook protein source according to package instructions.",
                "Prepare carbohydrates and vegetables.",
                "Combine all ingredients and serve.",
            ]

            return default_name, default_instructions
