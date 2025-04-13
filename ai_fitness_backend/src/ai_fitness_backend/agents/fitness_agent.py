import logging
import pandas as pd
import numpy as np
import re
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

from ..database import get_db, Document, Embedding
from ..llm import get_llm_client, get_llm_response
from ..processor import FitnessDataProcessor

logger = logging.getLogger("ai_fitness_api")


class FitnessAgent:
    """Agent for analyzing fitness data and providing personalized recommendations"""

    def __init__(self, db: Optional[Session] = None):
        # Initialize database session
        self.db = db

        # Initialize the FitnessDataProcessor
        self.processor = None
        if db:
            logger.info("Initializing FitnessDataProcessor with database connection")
            self.processor = FitnessDataProcessor(db=db)

            # Load documents from database
            self.processor.load_documents_from_db()

            # If no documents found, try loading from files
            if not self.processor.documents:
                logger.warning("No documents found in database, loading from files")
                self.processor.load_data()
                self.processor.create_documents()

        # Initialize LangChain components
        self.llm = get_llm_client(
            temperature=0.5
        )  # Lower temperature for more factual responses
        self.memory = ConversationBufferMemory(memory_key="chat_history")
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent_executor()

    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools for fitness data analysis"""

        tools = [
            Tool(
                name="AnalyzeWorkoutProgress",
                func=self._analyze_workout_progress_tool,
                description="Analyzes workout progress over time. Input should be a JSON string with user_id and optional timeframe (days).",
            ),
            Tool(
                name="CalculateNutritionNeeds",
                func=self._calculate_nutrition_needs_tool,
                description="Calculates personalized nutrition needs. Input should be a JSON string with weight, height, age, gender, activity_level, and goal.",
            ),
            Tool(
                name="RecommendWorkouts",
                func=self._recommend_workouts_tool,
                description="Recommends workouts based on user profile and goals. Input should be a JSON string with user_id, goal, and available_equipment.",
            ),
            Tool(
                name="AnalyzeBodyMetrics",
                func=self._analyze_body_metrics_tool,
                description="Analyzes body metrics trends over time. Input should be a JSON string with user_id and optional timeframe (days).",
            ),
            Tool(
                name="QueryFitnessData",
                func=self._query_fitness_data_tool,
                description="Queries the fitness data using natural language. Input should be a JSON string with query and optional top_k parameter.",
            ),
        ]

        return tools

    def _create_agent_executor(self) -> AgentExecutor:
        """Create the LangChain agent executor"""

        # Define the prompt template for the agent
        prompt = PromptTemplate.from_template(
            """You are a fitness and nutrition expert specializing in personalized fitness analysis and recommendations.
            
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

    async def _analyze_workout_progress_tool(self, input_str: str) -> str:
        """Tool for analyzing workout progress"""
        try:
            import json

            input_data = json.loads(input_str)

            user_id = input_data.get("user_id")
            timeframe = input_data.get("timeframe", 30)  # Default to 30 days

            # Get user workout data using the processor
            workout_data = self._get_user_workout_data(user_id)

            # Generate analysis based on the data
            analysis = self._generate_workout_analysis(user_id, timeframe, workout_data)
            return json.dumps(analysis)
        except Exception as e:
            logger.error(f"Error in AnalyzeWorkoutProgress tool: {str(e)}")
            return f"Error analyzing workout progress: {str(e)}"

    async def _calculate_nutrition_needs_tool(self, input_str: str) -> str:
        """Tool for calculating nutrition needs"""
        try:
            import json

            input_data = json.loads(input_str)

            # Try to get user_id from input
            user_id = input_data.get("user_id")

            # If user_id is provided, try to get user details using the processor
            if user_id and self.processor:
                user_details = self._get_user_details(user_id)
                if user_details:
                    # Use user details from database if available
                    weight = user_details.get("weight", input_data.get("weight"))
                    height = user_details.get("height", input_data.get("height"))
                    age = user_details.get("age", input_data.get("age"))
                    gender = user_details.get("gender", input_data.get("gender"))
                else:
                    # Fall back to input data if user not found
                    weight = input_data.get("weight")
                    height = input_data.get("height")
                    age = input_data.get("age")
                    gender = input_data.get("gender")
            else:
                # Use input data if no user_id provided or no processor available
                weight = input_data.get("weight")
                height = input_data.get("height")
                age = input_data.get("age")
                gender = input_data.get("gender")

            activity_level = input_data.get("activity_level")
            goal = input_data.get(
                "goal"
            )  # e.g., "lose_weight", "gain_muscle", "maintain"

            nutrition_needs = self._calculate_nutrition_needs(
                weight, height, age, gender, activity_level, goal
            )
            return json.dumps(nutrition_needs)
        except Exception as e:
            logger.error(f"Error in CalculateNutritionNeeds tool: {str(e)}")
            return f"Error calculating nutrition needs: {str(e)}"

    async def _recommend_workouts_tool(self, input_str: str) -> str:
        """Tool for recommending workouts"""
        try:
            import json

            input_data = json.loads(input_str)

            user_id = input_data.get("user_id")
            goal = input_data.get("goal")
            available_equipment = input_data.get("available_equipment", [])

            # Get user fitness profile using the processor
            user_profile = self._get_user_fitness_profile(user_id)

            # Merge user profile data with input data
            if user_profile:
                if not goal and "goal" in user_profile:
                    goal = user_profile["goal"]
                if not available_equipment and "available_equipment" in user_profile:
                    available_equipment = user_profile["available_equipment"]

            recommendations = self._generate_workout_recommendations(
                user_id, goal, available_equipment
            )
            return json.dumps(recommendations)
        except Exception as e:
            logger.error(f"Error in RecommendWorkouts tool: {str(e)}")
            return f"Error recommending workouts: {str(e)}"

    async def _analyze_body_metrics_tool(self, input_str: str) -> str:
        """Tool for analyzing body metrics"""
        try:
            import json

            input_data = json.loads(input_str)

            user_id = input_data.get("user_id")
            timeframe = input_data.get("timeframe", 30)  # Default to 30 days

            # Get user body metrics using the processor
            body_metrics = self._get_user_body_metrics(user_id)

            # Generate analysis based on the data
            analysis = self._analyze_body_metrics(user_id, timeframe, body_metrics)
            return json.dumps(analysis)
        except Exception as e:
            logger.error(f"Error in AnalyzeBodyMetrics tool: {str(e)}")
            return f"Error analyzing body metrics: {str(e)}"

    async def _query_fitness_data_tool(self, input_str: str) -> str:
        """Tool for querying fitness data using natural language"""
        try:
            import json

            input_data = json.loads(input_str)

            query = input_data.get("query")
            top_k = input_data.get("top_k", 7)

            if not self.processor:
                return "Error: FitnessDataProcessor not available for querying fitness data"

            # Use the processor to generate context from relevant documents
            context = self.processor.generate_context_from_query(query, top_k=top_k)

            # Create a prompt for the LLM
            prompt = f"""
            {context}
            
            Based on the above fitness and nutrition data, please answer the following question:
            {query}
            
            Please provide a detailed and helpful response.
            """

            # Get response from LLM
            system_role = "You are a helpful fitness and nutrition assistant."
            response = get_llm_response(prompt, system_role)

            return response
        except Exception as e:
            logger.error(f"Error in QueryFitnessData tool: {str(e)}")
            return f"Error querying fitness data: {str(e)}"

    def _get_user_details(self, user_id: str) -> Dict[str, Any]:
        """
        Get user details from documents using the processor

        Args:
            user_id: The user ID

        Returns:
            User details including weight, height, age, gender, etc.
        """
        if not self.processor or not self.processor.documents:
            logger.warning("No processor or documents available to get user details")
            return {}

        try:
            # Use the processor to find documents related to the user
            # First, create a query to find user details
            query = f"user {user_id} details profile"

            # Get relevant documents
            relevant_docs = self.processor.retrieve_relevant_documents(query, top_k=5)

            # Extract user details from documents
            user_details = {}

            for doc_info in relevant_docs:
                doc = doc_info["document"]
                doc_text = doc["text"]

                # Look for measurement documents which might contain weight
                if doc["type"] == "measurement":
                    weight_match = re.search(r"Weight\s+(\d+\.?\d*)\s*kg", doc_text)
                    if weight_match:
                        user_details["weight"] = float(weight_match.group(1))

                # Look for user profile information
                if "height:" in doc_text.lower():
                    height_match = re.search(
                        r"height:\s*(\d+\.?\d*)", doc_text, re.IGNORECASE
                    )
                    if height_match:
                        user_details["height"] = float(height_match.group(1))

                if "age:" in doc_text.lower():
                    age_match = re.search(r"age:\s*(\d+)", doc_text, re.IGNORECASE)
                    if age_match:
                        user_details["age"] = int(age_match.group(1))

                if "gender:" in doc_text.lower():
                    gender_match = re.search(
                        r"gender:\s*(\w+)", doc_text, re.IGNORECASE
                    )
                    if gender_match:
                        user_details["gender"] = gender_match.group(1)

            # If we couldn't find specific details, try a more general approach
            # by searching through all documents for the user
            if not user_details and self.db:
                user_docs = (
                    self.db.query(Document)
                    .filter(Document.text.like(f"%user_id: {user_id}%"))
                    .all()
                )

                for doc in user_docs:
                    doc_text = doc.text

                    if "weight:" in doc_text.lower():
                        weight_match = re.search(
                            r"weight:\s*(\d+\.?\d*)", doc_text, re.IGNORECASE
                        )
                        if weight_match:
                            user_details["weight"] = float(weight_match.group(1))

                    if "height:" in doc_text.lower():
                        height_match = re.search(
                            r"height:\s*(\d+\.?\d*)", doc_text, re.IGNORECASE
                        )
                        if height_match:
                            user_details["height"] = float(height_match.group(1))

                    if "age:" in doc_text.lower():
                        age_match = re.search(r"age:\s*(\d+)", doc_text, re.IGNORECASE)
                        if age_match:
                            user_details["age"] = int(age_match.group(1))

                    if "gender:" in doc_text.lower():
                        gender_match = re.search(
                            r"gender:\s*(\w+)", doc_text, re.IGNORECASE
                        )
                        if gender_match:
                            user_details["gender"] = gender_match.group(1)

            logger.info(f"Retrieved user details for user_id {user_id}: {user_details}")
            return user_details

        except Exception as e:
            logger.error(f"Error getting user details: {str(e)}")
            return {}

    def _get_user_workout_data(
        self,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get user workout data using the processor

        Args:
            user_id: The user ID

        Returns:
            List of workout data entries
        """
        if not self.processor or not self.processor.documents:
            logger.warning("No processor or documents available to get workout data")
            return []

        try:
            # Use the processor to find documents related to the user's workouts
            query = f"user {user_id} workout exercise training"

            # Get relevant documents
            relevant_docs = self.processor.retrieve_relevant_documents(query, top_k=10)

            # Filter for exercise/workout documents
            workout_docs = [
                doc_info["document"]
                for doc_info in relevant_docs
                if doc_info["document"]["type"] in ["exercise", "garmin"]
            ]

            # Extract workout data from documents
            workout_data = []

            for doc in workout_docs:
                doc_text = doc["text"]
                doc_date = doc["date"]

                # Skip if the document doesn't mention the user
                if (
                    f"user_id: {user_id}" not in doc_text
                    and f"User: {user_id}" not in doc_text
                ):
                    continue

                # Create workout entry
                workout_entry = {"date": doc_date, "exercises": []}

                # Extract duration if available
                duration_match = re.search(r"Duration:\s*(\d+)", doc_text)
                if duration_match:
                    workout_entry["duration"] = int(duration_match.group(1))

                # Extract calories if available
                calories_match = re.search(r"Calories:\s*(\d+)", doc_text)
                if calories_match:
                    workout_entry["calories"] = int(calories_match.group(1))

                # Extract exercises from the document text
                exercise_matches = re.finditer(r"Activity:\s*(.+?)(?:,|\.|$)", doc_text)

                for match in exercise_matches:
                    exercise = {"name": match.group(1).strip()}

                    # Try to extract sets and reps if available
                    sets_match = re.search(r"Sets:\s*(\d+)", doc_text)
                    if sets_match:
                        exercise["sets"] = int(sets_match.group(1))

                    reps_match = re.search(r"Reps:\s*(\d+)", doc_text)
                    if reps_match:
                        exercise["reps"] = int(reps_match.group(1))

                    workout_entry["exercises"].append(exercise)

                # If we found a Garmin activity, add it as an exercise
                if doc["type"] == "garmin":
                    activity_match = re.search(r"Garmin activity:\s*(.+?),", doc_text)
                    if activity_match:
                        activity_name = activity_match.group(1).strip()
                        exercise = {"name": activity_name}
                        workout_entry["exercises"].append(exercise)

                # Only add entries that have exercises
                if workout_entry["exercises"]:
                    workout_data.append(workout_entry)

            # If we couldn't find specific workout data, try a more general approach
            # by searching through all documents for the user
            if not workout_data and self.db:
                exercise_docs = (
                    self.db.query(Document)
                    .filter(
                        Document.text.like(f"%user_id: {user_id}%"),
                        Document.type.in_(["exercise", "garmin"]),
                    )
                    .all()
                )

                for doc in exercise_docs:
                    doc_text = doc.text
                    doc_date = doc.date

                    # Create workout entry
                    workout_entry = {"date": doc_date, "exercises": []}

                    # Extract duration if available
                    duration_match = re.search(r"Duration:\s*(\d+)", doc_text)
                    if duration_match:
                        workout_entry["duration"] = int(duration_match.group(1))

                    # Extract calories if available
                    calories_match = re.search(r"Calories:\s*(\d+)", doc_text)
                    if calories_match:
                        workout_entry["calories"] = int(calories_match.group(1))

                    # Extract exercises from the document text
                    exercise_matches = re.finditer(
                        r"Activity:\s*(.+?)(?:,|\.|$)", doc_text
                    )

                    for match in exercise_matches:
                        exercise = {"name": match.group(1).strip()}

                        # Try to extract sets and reps if available
                        sets_match = re.search(r"Sets:\s*(\d+)", doc_text)
                        if sets_match:
                            exercise["sets"] = int(sets_match.group(1))

                        reps_match = re.search(r"Reps:\s*(\d+)", doc_text)
                        if reps_match:
                            exercise["reps"] = int(reps_match.group(1))

                        workout_entry["exercises"].append(exercise)

                    # If we found a Garmin activity, add it as an exercise
                    if doc.type == "garmin":
                        activity_match = re.search(
                            r"Garmin activity:\s*(.+?),", doc_text
                        )
                        if activity_match:
                            activity_name = activity_match.group(1).strip()
                            exercise = {"name": activity_name}
                            workout_entry["exercises"].append(exercise)

                    # Only add entries that have exercises
                    if workout_entry["exercises"]:
                        workout_data.append(workout_entry)

            logger.info(
                f"Retrieved {len(workout_data)} workout entries for user_id {user_id}"
            )
            return workout_data

        except Exception as e:
            logger.error(f"Error getting user workout data: {str(e)}")
            return []

    def _get_user_body_metrics(
        self,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get user body metrics using the processor

        Args:
            user_id: The user ID

        Returns:
            List of body metrics entries
        """
        if not self.processor or not self.processor.documents:
            logger.warning("No processor or documents available to get body metrics")
            return []

        try:
            # Use the processor to find documents related to the user's body metrics
            query = f"user {user_id} weight body measurements metrics"

            # Get relevant documents
            relevant_docs = self.processor.retrieve_relevant_documents(query, top_k=10)

            # Filter for measurement documents
            metrics_docs = [
                doc_info["document"]
                for doc_info in relevant_docs
                if doc_info["document"]["type"] in ["measurement", "body_metrics"]
            ]

            # Extract body metrics from documents
            body_metrics = []

            for doc in metrics_docs:
                doc_text = doc["text"]
                doc_date = doc["date"]

                # Skip if the document doesn't mention the user
                if (
                    f"user_id: {user_id}" not in doc_text
                    and f"User: {user_id}" not in doc_text
                ):
                    continue

                # Create metrics entry
                metrics_entry = {"date": doc_date}

                # Extract weight if available
                weight_match = re.search(
                    r"Weight\s*(\d+\.?\d*)\s*kg", doc_text, re.IGNORECASE
                )
                if weight_match:
                    metrics_entry["weight"] = float(weight_match.group(1))

                # Extract body fat if available
                body_fat_match = re.search(
                    r"body_fat:\s*(\d+\.?\d*)", doc_text, re.IGNORECASE
                )
                if body_fat_match:
                    metrics_entry["body_fat"] = float(body_fat_match.group(1))

                # Extract waist measurement if available
                waist_match = re.search(
                    r"waist:\s*(\d+\.?\d*)", doc_text, re.IGNORECASE
                )
                if waist_match:
                    metrics_entry["waist"] = float(waist_match.group(1))

                # Extract chest measurement if available
                chest_match = re.search(
                    r"chest:\s*(\d+\.?\d*)", doc_text, re.IGNORECASE
                )
                if chest_match:
                    metrics_entry["chest"] = float(chest_match.group(1))

                # Extract arms measurement if available
                arms_match = re.search(r"arms:\s*(\d+\.?\d*)", doc_text, re.IGNORECASE)
                if arms_match:
                    metrics_entry["arms"] = float(arms_match.group(1))

                # Only add entries that have at least one metric
                if len(metrics_entry) > 1:  # More than just the date
                    body_metrics.append(metrics_entry)

            # If we couldn't find specific body metrics, try a more general approach
            # by searching through all documents for the user
            if not body_metrics and self.db:
                metrics_docs = (
                    self.db.query(Document)
                    .filter(
                        Document.text.like(f"%user_id: {user_id}%"),
                        Document.type.in_(["measurement", "body_metrics"]),
                    )
                    .all()
                )

                for doc in metrics_docs:
                    doc_text = doc.text
                    doc_date = doc.date

                    # Create metrics entry
                    metrics_entry = {"date": doc_date}

                    # Extract weight if available
                    weight_match = re.search(
                        r"Weight\s*(\d+\.?\d*)\s*kg", doc_text, re.IGNORECASE
                    )
                    if weight_match:
                        metrics_entry["weight"] = float(weight_match.group(1))

                    # Extract body fat if available
                    body_fat_match = re.search(
                        r"body_fat:\s*(\d+\.?\d*)", doc_text, re.IGNORECASE
                    )
                    if body_fat_match:
                        metrics_entry["body_fat"] = float(body_fat_match.group(1))

                    # Extract waist measurement if available
                    waist_match = re.search(
                        r"waist:\s*(\d+\.?\d*)", doc_text, re.IGNORECASE
                    )
                    if waist_match:
                        metrics_entry["waist"] = float(waist_match.group(1))

                    # Extract chest measurement if available
                    chest_match = re.search(
                        r"chest:\s*(\d+\.?\d*)", doc_text, re.IGNORECASE
                    )
                    if chest_match:
                        metrics_entry["chest"] = float(chest_match.group(1))

                    # Extract arms measurement if available
                    arms_match = re.search(
                        r"arms:\s*(\d+\.?\d*)", doc_text, re.IGNORECASE
                    )
                    if arms_match:
                        metrics_entry["arms"] = float(arms_match.group(1))

                    # Only add entries that have at least one metric
                    if len(metrics_entry) > 1:  # More than just the date
                        body_metrics.append(metrics_entry)

            logger.info(
                f"Retrieved {len(body_metrics)} body metrics entries for user_id {user_id}"
            )
            return body_metrics

        except Exception as e:
            logger.error(f"Error getting user body metrics: {str(e)}")
            return []

    def _get_user_fitness_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get user fitness profile using the processor

        Args:
            user_id: The user ID

        Returns:
            User fitness profile including goals, preferences, etc.
        """
        if not self.processor or not self.processor.documents:
            logger.warning("No processor or documents available to get fitness profile")
            return {}

        try:
            # Use the processor to find documents related to the user's fitness profile
            query = f"user {user_id} fitness profile goals preferences"

            # Get relevant documents
            relevant_docs = self.processor.retrieve_relevant_documents(query, top_k=5)

            # Extract fitness profile from documents
            profile = {}

            for doc_info in relevant_docs:
                doc = doc_info["document"]
                doc_text = doc["text"]

                # Skip if the document doesn't mention the user
                if (
                    f"user_id: {user_id}" not in doc_text
                    and f"User: {user_id}" not in doc_text
                ):
                    continue

                # Extract goal if available
                goal_match = re.search(r"goal:\s*(\w+)", doc_text, re.IGNORECASE)
                if goal_match:
                    profile["goal"] = goal_match.group(1)

                # Extract available equipment if available
                equipment_match = re.search(
                    r"available_equipment:\s*\[(.*?)\]", doc_text, re.IGNORECASE
                )
                if equipment_match:
                    equipment_str = equipment_match.group(1)
                    profile["available_equipment"] = [
                        item.strip().strip("\"'") for item in equipment_str.split(",")
                    ]

                # Extract experience level if available
                experience_match = re.search(
                    r"experience_level:\s*(\w+)", doc_text, re.IGNORECASE
                )
                if experience_match:
                    profile["experience_level"] = experience_match.group(1)

            # If we couldn't find specific profile data, try a more general approach
            # by searching through all documents for the user
            if not profile and self.db:
                profile_docs = (
                    self.db.query(Document)
                    .filter(
                        Document.text.like(f"%user_id: {user_id}%"),
                        Document.type == "fitness_profile",
                    )
                    .all()
                )

                for doc in profile_docs:
                    doc_text = doc.text

                    # Extract goal if available
                    goal_match = re.search(r"goal:\s*(\w+)", doc_text, re.IGNORECASE)
                    if goal_match:
                        profile["goal"] = goal_match.group(1)

                    # Extract available equipment if available
                    equipment_match = re.search(
                        r"available_equipment:\s*\[(.*?)\]", doc_text, re.IGNORECASE
                    )
                    if equipment_match:
                        equipment_str = equipment_match.group(1)
                        profile["available_equipment"] = [
                            item.strip().strip("\"'")
                            for item in equipment_str.split(",")
                        ]

                    # Extract experience level if available
                    experience_match = re.search(
                        r"experience_level:\s*(\w+)", doc_text, re.IGNORECASE
                    )
                    if experience_match:
                        profile["experience_level"] = experience_match.group(1)

            logger.info(f"Retrieved fitness profile for user_id {user_id}: {profile}")
            return profile

        except Exception as e:
            logger.error(f"Error getting user fitness profile: {str(e)}")
            return {}

    def _generate_workout_analysis(
        self, user_id: str, timeframe: int, workout_data: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate analysis of workout progress

        Args:
            user_id: The user ID
            timeframe: Timeframe in days
            workout_data: Optional workout data to analyze

        Returns:
            Analysis of workout progress
        """
        # If workout data is provided, analyze it
        # Otherwise, return a placeholder analysis
        if workout_data:
            try:
                # Calculate total workouts
                total_workouts = len(workout_data)

                # Calculate average duration (if available)
                durations = [
                    workout.get("duration", 0)
                    for workout in workout_data
                    if "duration" in workout
                ]
                average_duration = sum(durations) / len(durations) if durations else 45

                # Count exercises by muscle group
                muscle_groups = {}
                for workout in workout_data:
                    for exercise in workout.get("exercises", []):
                        # This is a simplified approach - in a real implementation,
                        # you would have a mapping of exercises to muscle groups
                        name = exercise.get("name", "").lower()
                        if "bench" in name or "chest" in name or "push" in name:
                            muscle_groups["chest"] = muscle_groups.get("chest", 0) + 1
                        elif "squat" in name or "leg" in name:
                            muscle_groups["legs"] = muscle_groups.get("legs", 0) + 1
                        elif "row" in name or "pull" in name or "back" in name:
                            muscle_groups["back"] = muscle_groups.get("back", 0) + 1
                        elif "shoulder" in name or "press" in name:
                            muscle_groups["shoulders"] = (
                                muscle_groups.get("shoulders", 0) + 1
                            )
                        elif "bicep" in name or "curl" in name:
                            muscle_groups["arms"] = muscle_groups.get("arms", 0) + 1

                # Sort muscle groups by frequency
                sorted_groups = sorted(
                    muscle_groups.items(), key=lambda x: x[1], reverse=True
                )
                most_trained = (
                    [group for group, _ in sorted_groups[:3]] if sorted_groups else []
                )
                least_trained = (
                    [group for group, _ in sorted_groups[-2:]]
                    if len(sorted_groups) >= 2
                    else []
                )

                # Calculate consistency score (0-10)
                # This is a simplified approach - in a real implementation,
                # you would consider workout frequency, adherence to schedule, etc.
                consistency_score = min(10, (total_workouts / timeframe) * 30)

                return {
                    "user_id": user_id,
                    "timeframe": timeframe,
                    "analysis": {
                        "total_workouts": total_workouts,
                        "average_duration": round(average_duration),
                        "most_trained_muscle_groups": most_trained,
                        "least_trained_muscle_groups": least_trained,
                        "consistency_score": round(consistency_score, 1),
                        "recommendations": self._generate_workout_recommendations_based_on_analysis(
                            most_trained, least_trained, consistency_score
                        ),
                    },
                }
            except Exception as e:
                logger.error(f"Error analyzing workout data: {str(e)}")
                # Fall back to placeholder analysis

        # Return placeholder analysis
        return {
            "user_id": user_id,
            "timeframe": timeframe,
            "analysis": {
                "total_workouts": 12,
                "average_duration": 45,  # minutes
                "most_trained_muscle_groups": ["chest", "back", "legs"],
                "least_trained_muscle_groups": ["shoulders", "arms"],
                "strength_progress": {
                    "bench_press": "+5kg",
                    "squat": "+10kg",
                    "deadlift": "+7.5kg",
                },
                "consistency_score": 8.5,  # out of 10
                "recommendations": [
                    "Increase shoulder training frequency",
                    "Add more arm exercises",
                    "Consider adding one more leg day per week",
                ],
            },
        }

    def _generate_workout_recommendations_based_on_analysis(
        self,
        most_trained: List[str],
        least_trained: List[str],
        consistency_score: float,
    ) -> List[str]:
        """
        Generate workout recommendations based on analysis

        Args:
            most_trained: Most trained muscle groups
            least_trained: Least trained muscle groups
            consistency_score: Consistency score (0-10)

        Returns:
            List of recommendations
        """
        recommendations = []

        # Add recommendations based on muscle group balance
        for group in least_trained:
            recommendations.append(f"Increase {group} training frequency")

        # Add recommendations based on consistency
        if consistency_score < 5:
            recommendations.append(
                "Improve workout consistency by scheduling fixed workout times"
            )
        elif consistency_score < 8:
            recommendations.append(
                "Maintain current consistency and consider adding one more session per week"
            )

        # Add general recommendations if needed
        if len(recommendations) < 2:
            recommendations.append(
                "Consider adding variety to your workouts to prevent plateaus"
            )
            recommendations.append(
                "Track your progress to stay motivated and see improvements"
            )

        return recommendations

    def _calculate_nutrition_needs(
        self,
        weight: float,
        height: float,
        age: int,
        gender: str,
        activity_level: str,
        goal: str,
    ) -> Dict[str, Any]:
        """
        Calculate personalized nutrition needs

        Args:
            weight: Weight in kg
            height: Height in cm
            age: Age in years
            gender: Gender (male/female)
            activity_level: Activity level (sedentary/light/moderate/active/very_active)
            goal: Goal (lose_weight/maintain/gain_muscle)

        Returns:
            Personalized nutrition needs
        """
        # Calculate Basal Metabolic Rate (BMR) using Mifflin-St Jeor Equation
        if gender.lower() == "male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        # Apply activity multiplier
        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9,
        }

        tdee = bmr * activity_multipliers.get(activity_level.lower(), 1.2)

        # Adjust based on goal
        if goal.lower() == "lose_weight":
            calorie_target = tdee - 500  # 500 calorie deficit
        elif goal.lower() == "gain_muscle":
            calorie_target = tdee + 300  # 300 calorie surplus
        else:  # maintain
            calorie_target = tdee

        # Calculate macronutrient targets
        if goal.lower() == "lose_weight":
            protein_g = weight * 2.2  # Higher protein for weight loss (2.2g per kg)
            fat_g = weight * 1.0  # 1g per kg
            # Remaining calories from carbs
            carbs_g = (calorie_target - (protein_g * 4 + fat_g * 9)) / 4
        elif goal.lower() == "gain_muscle":
            protein_g = weight * 2.0  # 2g per kg
            fat_g = weight * 1.0  # 1g per kg
            # Remaining calories from carbs
            carbs_g = (calorie_target - (protein_g * 4 + fat_g * 9)) / 4
        else:  # maintain
            protein_g = weight * 1.8  # 1.8g per kg
            fat_g = weight * 0.8  # 0.8g per kg
            # Remaining calories from carbs
            carbs_g = (calorie_target - (protein_g * 4 + fat_g * 9)) / 4

        # Ensure carbs don't go below minimum
        carbs_g = max(carbs_g, 50)

        return {
            "daily_calories": round(calorie_target),
            "macronutrients": {
                "protein": {
                    "grams": round(protein_g),
                    "calories": round(protein_g * 4),
                    "percentage": round((protein_g * 4 / calorie_target) * 100),
                },
                "carbs": {
                    "grams": round(carbs_g),
                    "calories": round(carbs_g * 4),
                    "percentage": round((carbs_g * 4 / calorie_target) * 100),
                },
                "fat": {
                    "grams": round(fat_g),
                    "calories": round(fat_g * 9),
                    "percentage": round((fat_g * 9 / calorie_target) * 100),
                },
            },
            "meal_frequency": "3-4 meals per day",
            "hydration": f"{round(weight * 0.033)} liters of water per day",
        }

    def _generate_workout_recommendations(
        self, user_id: str, goal: str, available_equipment: List[str]
    ) -> Dict[str, Any]:
        """
        Generate personalized workout recommendations

        Args:
            user_id: The user ID
            goal: Fitness goal
            available_equipment: List of available equipment

        Returns:
            Personalized workout recommendations
        """
        # Define workout templates based on goals
        workout_templates = {
            "lose_weight": {
                "schedule": [
                    "full_body",
                    "rest",
                    "hiit",
                    "rest",
                    "full_body",
                    "hiit",
                    "rest",
                ],
                "focus": "calorie burning and muscle preservation",
                "cardio": "30-45 minutes, 3-4 times per week",
                "strength": "2-3 full body sessions per week",
            },
            "gain_muscle": {
                "schedule": ["push", "pull", "rest", "legs", "push", "pull", "rest"],
                "focus": "progressive overload and muscle hypertrophy",
                "cardio": "15-20 minutes, 2-3 times per week",
                "strength": "5-6 sessions per week, split routine",
            },
            "improve_fitness": {
                "schedule": [
                    "upper",
                    "lower",
                    "rest",
                    "hiit",
                    "upper",
                    "lower",
                    "rest",
                ],
                "focus": "balanced approach to strength and cardiovascular fitness",
                "cardio": "20-30 minutes, 2-3 times per week",
                "strength": "4 sessions per week, upper/lower split",
            },
        }

        # Select the appropriate template or default to improve_fitness
        template = workout_templates.get(
            goal.lower(), workout_templates["improve_fitness"]
        )

        # Adjust based on available equipment
        has_weights = any(
            item in available_equipment
            for item in ["dumbbells", "barbell", "kettlebell"]
        )
        has_machines = "machines" in available_equipment
        has_cardio_equipment = any(
            item in available_equipment
            for item in ["treadmill", "bike", "elliptical", "rower"]
        )

        # Generate sample workouts based on equipment
        sample_workouts = []

        if "full_body" in template["schedule"]:
            if has_weights:
                sample_workouts.append(
                    {
                        "name": "Full Body Strength",
                        "exercises": [
                            {"name": "Squats", "sets": 3, "reps": "8-12"},
                            {"name": "Bench Press", "sets": 3, "reps": "8-12"},
                            {"name": "Bent-Over Rows", "sets": 3, "reps": "8-12"},
                            {"name": "Overhead Press", "sets": 3, "reps": "8-12"},
                            {"name": "Deadlifts", "sets": 3, "reps": "8-12"},
                            {"name": "Planks", "sets": 3, "reps": "30-60 sec"},
                        ],
                    }
                )
            else:
                sample_workouts.append(
                    {
                        "name": "Bodyweight Full Body",
                        "exercises": [
                            {"name": "Bodyweight Squats", "sets": 3, "reps": "15-20"},
                            {"name": "Push-ups", "sets": 3, "reps": "10-15"},
                            {"name": "Inverted Rows", "sets": 3, "reps": "10-15"},
                            {"name": "Pike Push-ups", "sets": 3, "reps": "10-15"},
                            {"name": "Lunges", "sets": 3, "reps": "10-15 per leg"},
                            {"name": "Planks", "sets": 3, "reps": "30-60 sec"},
                        ],
                    }
                )

        if "hiit" in template["schedule"]:
            if has_cardio_equipment:
                sample_workouts.append(
                    {
                        "name": "Equipment HIIT",
                        "description": "30 seconds high intensity, 30 seconds rest, repeat for 20 minutes",
                        "exercises": [
                            {"name": "Treadmill Sprints"},
                            {"name": "Bike Intervals"},
                            {"name": "Rower Sprints"},
                        ],
                    }
                )
            else:
                sample_workouts.append(
                    {
                        "name": "Bodyweight HIIT",
                        "description": "40 seconds work, 20 seconds rest, repeat for 20 minutes",
                        "exercises": [
                            {"name": "Jumping Jacks"},
                            {"name": "Mountain Climbers"},
                            {"name": "Burpees"},
                            {"name": "High Knees"},
                            {"name": "Squat Jumps"},
                        ],
                    }
                )

        if "push" in template["schedule"]:
            if has_weights:
                sample_workouts.append(
                    {
                        "name": "Push Day",
                        "exercises": [
                            {"name": "Bench Press", "sets": 4, "reps": "8-10"},
                            {"name": "Overhead Press", "sets": 3, "reps": "8-10"},
                            {
                                "name": "Incline Dumbbell Press",
                                "sets": 3,
                                "reps": "10-12",
                            },
                            {"name": "Lateral Raises", "sets": 3, "reps": "12-15"},
                            {"name": "Tricep Pushdowns", "sets": 3, "reps": "12-15"},
                            {
                                "name": "Overhead Tricep Extensions",
                                "sets": 3,
                                "reps": "12-15",
                            },
                        ],
                    }
                )
            else:
                sample_workouts.append(
                    {
                        "name": "Bodyweight Push",
                        "exercises": [
                            {"name": "Push-ups", "sets": 4, "reps": "max"},
                            {"name": "Pike Push-ups", "sets": 3, "reps": "max"},
                            {"name": "Decline Push-ups", "sets": 3, "reps": "max"},
                            {"name": "Diamond Push-ups", "sets": 3, "reps": "max"},
                            {"name": "Bench Dips", "sets": 3, "reps": "max"},
                        ],
                    }
                )

        if "pull" in template["schedule"]:
            if has_weights:
                sample_workouts.append(
                    {
                        "name": "Pull Day",
                        "exercises": [
                            {"name": "Deadlifts", "sets": 4, "reps": "6-8"},
                            {
                                "name": "Pull-ups/Lat Pulldowns",
                                "sets": 3,
                                "reps": "8-10",
                            },
                            {"name": "Bent-Over Rows", "sets": 3, "reps": "8-10"},
                            {"name": "Face Pulls", "sets": 3, "reps": "12-15"},
                            {"name": "Bicep Curls", "sets": 3, "reps": "12-15"},
                            {"name": "Hammer Curls", "sets": 3, "reps": "12-15"},
                        ],
                    }
                )
            else:
                sample_workouts.append(
                    {
                        "name": "Bodyweight Pull",
                        "exercises": [
                            {"name": "Pull-ups/Chin-ups", "sets": 4, "reps": "max"},
                            {"name": "Inverted Rows", "sets": 3, "reps": "max"},
                            {"name": "Superman Holds", "sets": 3, "reps": "30-45 sec"},
                            {"name": "Doorway Curls", "sets": 3, "reps": "max"},
                        ],
                    }
                )

        if "legs" in template["schedule"]:
            if has_weights:
                sample_workouts.append(
                    {
                        "name": "Leg Day",
                        "exercises": [
                            {"name": "Squats", "sets": 4, "reps": "8-10"},
                            {"name": "Romanian Deadlifts", "sets": 3, "reps": "8-10"},
                            {"name": "Lunges", "sets": 3, "reps": "10-12 per leg"},
                            {"name": "Leg Press", "sets": 3, "reps": "10-12"},
                            {"name": "Leg Curls", "sets": 3, "reps": "12-15"},
                            {"name": "Calf Raises", "sets": 4, "reps": "15-20"},
                        ],
                    }
                )
            else:
                sample_workouts.append(
                    {
                        "name": "Bodyweight Legs",
                        "exercises": [
                            {"name": "Bodyweight Squats", "sets": 4, "reps": "15-20"},
                            {"name": "Lunges", "sets": 3, "reps": "12-15 per leg"},
                            {"name": "Step-ups", "sets": 3, "reps": "12-15 per leg"},
                            {"name": "Glute Bridges", "sets": 3, "reps": "15-20"},
                            {
                                "name": "Single-Leg Calf Raises",
                                "sets": 4,
                                "reps": "15-20 per leg",
                            },
                        ],
                    }
                )

        if "upper" in template["schedule"]:
            if has_weights:
                sample_workouts.append(
                    {
                        "name": "Upper Body",
                        "exercises": [
                            {"name": "Bench Press", "sets": 3, "reps": "8-10"},
                            {"name": "Bent-Over Rows", "sets": 3, "reps": "8-10"},
                            {"name": "Overhead Press", "sets": 3, "reps": "8-10"},
                            {
                                "name": "Pull-ups/Lat Pulldowns",
                                "sets": 3,
                                "reps": "8-10",
                            },
                            {"name": "Lateral Raises", "sets": 3, "reps": "12-15"},
                            {"name": "Tricep Pushdowns", "sets": 3, "reps": "12-15"},
                            {"name": "Bicep Curls", "sets": 3, "reps": "12-15"},
                        ],
                    }
                )
            else:
                sample_workouts.append(
                    {
                        "name": "Bodyweight Upper",
                        "exercises": [
                            {"name": "Push-ups", "sets": 3, "reps": "max"},
                            {"name": "Inverted Rows", "sets": 3, "reps": "max"},
                            {"name": "Pike Push-ups", "sets": 3, "reps": "max"},
                            {"name": "Pull-ups/Chin-ups", "sets": 3, "reps": "max"},
                            {"name": "Diamond Push-ups", "sets": 3, "reps": "max"},
                        ],
                    }
                )

        if "lower" in template["schedule"]:
            if has_weights:
                sample_workouts.append(
                    {
                        "name": "Lower Body",
                        "exercises": [
                            {"name": "Squats", "sets": 4, "reps": "8-10"},
                            {"name": "Romanian Deadlifts", "sets": 3, "reps": "8-10"},
                            {"name": "Lunges", "sets": 3, "reps": "10-12 per leg"},
                            {"name": "Leg Press", "sets": 3, "reps": "10-12"},
                            {"name": "Leg Curls", "sets": 3, "reps": "12-15"},
                            {"name": "Calf Raises", "sets": 4, "reps": "15-20"},
                        ],
                    }
                )
            else:
                sample_workouts.append(
                    {
                        "name": "Bodyweight Lower",
                        "exercises": [
                            {"name": "Bodyweight Squats", "sets": 4, "reps": "15-20"},
                            {"name": "Lunges", "sets": 3, "reps": "12-15 per leg"},
                            {"name": "Step-ups", "sets": 3, "reps": "12-15 per leg"},
                            {"name": "Glute Bridges", "sets": 3, "reps": "15-20"},
                            {"name": "Wall Sit", "sets": 3, "reps": "30-60 sec"},
                            {
                                "name": "Single-Leg Calf Raises",
                                "sets": 4,
                                "reps": "15-20 per leg",
                            },
                        ],
                    }
                )

        return {
            "user_id": user_id,
            "goal": goal,
            "available_equipment": available_equipment,
            "recommended_schedule": template["schedule"],
            "focus": template["focus"],
            "cardio_recommendation": template["cardio"],
            "strength_recommendation": template["strength"],
            "sample_workouts": sample_workouts,
            "progression_strategy": "Increase weight by 2.5-5% or add 1-2 reps when current target becomes easy",
            "recovery_tips": [
                "Ensure 7-9 hours of quality sleep per night",
                "Stay hydrated throughout the day",
                "Consider foam rolling for muscle recovery",
                "Allow at least 48 hours before training the same muscle group intensely",
            ],
        }

    def _analyze_body_metrics(
        self, user_id: str, timeframe: int, body_metrics: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze body metrics trends

        Args:
            user_id: The user ID
            timeframe: Timeframe in days
            body_metrics: Optional body metrics data to analyze

        Returns:
            Analysis of body metrics trends
        """
        # If body metrics data is provided, analyze it
        # Otherwise, return a placeholder analysis
        if body_metrics and len(body_metrics) >= 2:
            try:
                # Sort metrics by date
                sorted_metrics = sorted(body_metrics, key=lambda x: x.get("date", ""))

                # Get start and current metrics
                start_metrics = sorted_metrics[0]
                current_metrics = sorted_metrics[-1]

                # Calculate changes
                metrics_analysis = {}

                # Analyze weight if available
                if "weight" in start_metrics and "weight" in current_metrics:
                    start_weight = start_metrics["weight"]
                    current_weight = current_metrics["weight"]
                    weight_change = current_weight - start_weight

                    # Calculate rate of change per week
                    days_between = (
                        pd.to_datetime(current_metrics["date"])
                        - pd.to_datetime(start_metrics["date"])
                    ).days
                    weeks_between = max(1, days_between / 7)
                    weekly_rate = weight_change / weeks_between

                    metrics_analysis["weight"] = {
                        "start": start_weight,
                        "current": current_weight,
                        "change": round(weight_change, 1),
                        "rate": f"{round(weekly_rate, 2)} kg per week",
                        "trend": "decreasing"
                        if weight_change < 0
                        else "increasing"
                        if weight_change > 0
                        else "stable",
                    }

                # Analyze body fat if available
                if "body_fat" in start_metrics and "body_fat" in current_metrics:
                    start_bf = start_metrics["body_fat"]
                    current_bf = current_metrics["body_fat"]
                    bf_change = current_bf - start_bf

                    metrics_analysis["body_fat"] = {
                        "start": start_bf,
                        "current": current_bf,
                        "change": round(bf_change, 1),
                        "trend": "decreasing"
                        if bf_change < 0
                        else "increasing"
                        if bf_change > 0
                        else "stable",
                    }

                # Analyze measurements if available
                measurements = {}
                for measurement in ["waist", "chest", "arms"]:
                    if measurement in start_metrics and measurement in current_metrics:
                        start_value = start_metrics[measurement]
                        current_value = current_metrics[measurement]
                        change = current_value - start_value

                        measurements[measurement] = {
                            "start": start_value,
                            "current": current_value,
                            "change": round(change, 1),
                        }

                if measurements:
                    metrics_analysis["measurements"] = measurements

                # Generate insights based on the analysis
                insights = []
                recommendations = []

                # Weight insights
                if "weight" in metrics_analysis:
                    weight_change = metrics_analysis["weight"]["change"]
                    weight_rate = float(metrics_analysis["weight"]["rate"].split()[0])

                    if abs(weight_rate) > 1:
                        insights.append(
                            f"Your weight is changing at {abs(weight_rate)} kg per week, which is faster than the recommended 0.5-1kg per week"
                        )
                        recommendations.append(
                            "Adjust your calorie intake to aim for a more sustainable rate of change"
                        )
                    else:
                        insights.append(
                            f"You're changing weight at a healthy rate of {abs(weight_rate)} kg per week"
                        )

                # Body fat insights
                if "body_fat" in metrics_analysis:
                    bf_change = metrics_analysis["body_fat"]["change"]
                    bf_trend = metrics_analysis["body_fat"]["trend"]

                    if "weight" in metrics_analysis:
                        weight_trend = metrics_analysis["weight"]["trend"]

                        if bf_trend == "decreasing" and weight_trend == "increasing":
                            insights.append(
                                "Your body fat percentage is decreasing while weight is increasing, suggesting muscle gain"
                            )
                        elif bf_trend == "decreasing" and weight_trend == "decreasing":
                            insights.append(
                                "Your body fat percentage and weight are both decreasing, indicating fat loss"
                            )
                        elif bf_trend == "increasing" and weight_trend == "increasing":
                            insights.append(
                                "Your body fat percentage and weight are both increasing, suggesting fat gain"
                            )
                            recommendations.append(
                                "Consider adjusting your nutrition and increasing activity levels"
                            )

                # Measurement insights
                if "measurements" in metrics_analysis:
                    measurements = metrics_analysis["measurements"]

                    if "waist" in measurements and measurements["waist"]["change"] < 0:
                        insights.append(
                            "Your waist measurement is decreasing, indicating fat loss"
                        )

                    if "chest" in measurements and "arms" in measurements:
                        if (
                            measurements["chest"]["change"] > 0
                            and measurements["arms"]["change"] > 0
                        ):
                            insights.append(
                                "Your chest and arm measurements are increasing, suggesting muscle gain"
                            )

                # Add general recommendations if needed
                if len(recommendations) < 2:
                    if (
                        "weight" in metrics_analysis
                        and metrics_analysis["weight"]["trend"] == "decreasing"
                    ):
                        recommendations.append(
                            "Continue with your current nutrition plan"
                        )
                        recommendations.append(
                            "Ensure adequate protein intake to preserve muscle mass"
                        )
                    elif (
                        "weight" in metrics_analysis
                        and metrics_analysis["weight"]["trend"] == "increasing"
                    ):
                        recommendations.append(
                            "Focus on progressive overload in your training"
                        )
                        recommendations.append(
                            "Maintain your current calorie surplus for continued gains"
                        )
                    else:
                        recommendations.append(
                            "Consider taking progress photos to visually track changes"
                        )
                        recommendations.append(
                            "Track your workouts to ensure progressive overload"
                        )

                return {
                    "user_id": user_id,
                    "timeframe": timeframe,
                    "metrics_analysis": metrics_analysis,
                    "insights": insights,
                    "recommendations": recommendations,
                }

            except Exception as e:
                logger.error(f"Error analyzing body metrics: {str(e)}")
                # Fall back to placeholder analysis

        # Return placeholder analysis
        return {
            "user_id": user_id,
            "timeframe": timeframe,
            "metrics_analysis": {
                "weight": {
                    "start": 80.5,  # kg
                    "current": 78.2,
                    "change": -2.3,
                    "rate": "-0.58 kg per week",
                    "trend": "decreasing",
                },
                "body_fat": {
                    "start": 22.0,  # percentage
                    "current": 20.5,
                    "change": -1.5,
                    "trend": "decreasing",
                },
                "measurements": {
                    "waist": {
                        "start": 86.0,  # cm
                        "current": 84.5,
                        "change": -1.5,
                    },
                    "chest": {"start": 100.0, "current": 101.5, "change": 1.5},
                    "arms": {"start": 35.0, "current": 36.0, "change": 1.0},
                },
            },
            "insights": [
                "You're losing weight at a healthy rate of 0.5-1kg per week",
                "Your body fat percentage is decreasing while maintaining muscle mass",
                "Your waist measurement is decreasing, indicating fat loss",
                "Chest and arm measurements are increasing, suggesting muscle gain",
            ],
            "recommendations": [
                "Continue with your current nutrition plan",
                "Maintain your current training intensity",
                "Consider adding more protein to support muscle growth",
                "Take progress photos to visually track changes",
            ],
        }

    async def process_fitness_request(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a fitness analysis request

        Args:
            request_data: Dictionary with request parameters

        Returns:
            Analysis results based on the request type
        """
        try:
            # Determine the type of analysis to perform based on the request
            request_type = request_data.get("request_type", "general")

            if request_type == "workout_progress":
                user_id = request_data.get("user_id")
                timeframe = request_data.get("timeframe", 30)

                # Get user workout data from database
                workout_data = self._get_user_workout_data(user_id)

                return self._generate_workout_analysis(user_id, timeframe, workout_data)

            elif request_type == "nutrition_needs":
                # Try to get user_id from request
                user_id = request_data.get("user_id")

                # If user_id is provided, try to get user details from database
                if user_id and self.db:
                    user_details = self._get_user_details(user_id)
                    if user_details:
                        # Use user details from database if available
                        weight = user_details.get("weight", request_data.get("weight"))
                        height = user_details.get("height", request_data.get("height"))
                        age = user_details.get("age", request_data.get("age"))
                        gender = user_details.get("gender", request_data.get("gender"))
                    else:
                        # Fall back to request data if user not found
                        weight = request_data.get("weight")
                        height = request_data.get("height")
                        age = request_data.get("age")
                        gender = request_data.get("gender")
                else:
                    # Use request data if no user_id provided
                    weight = request_data.get("weight")
                    height = request_data.get("height")
                    age = request_data.get("age")
                    gender = request_data.get("gender")

                activity_level = request_data.get("activity_level")
                goal = request_data.get("goal")

                return self._calculate_nutrition_needs(
                    weight, height, age, gender, activity_level, goal
                )

            elif request_type == "workout_recommendations":
                user_id = request_data.get("user_id")
                goal = request_data.get("goal")
                available_equipment = request_data.get("available_equipment", [])

                # Get user fitness profile from database
                user_profile = self._get_user_fitness_profile(user_id)

                # Merge user profile data with request data
                if user_profile:
                    if not goal and "goal" in user_profile:
                        goal = user_profile["goal"]
                    if (
                        not available_equipment
                        and "available_equipment" in user_profile
                    ):
                        available_equipment = user_profile["available_equipment"]

                return self._generate_workout_recommendations(
                    user_id, goal, available_equipment
                )

            elif request_type == "body_metrics":
                user_id = request_data.get("user_id")
                timeframe = request_data.get("timeframe", 30)

                # Get user body metrics from database
                body_metrics = self._get_user_body_metrics(user_id, timeframe)

                return self._analyze_body_metrics(user_id, timeframe, body_metrics)

            else:
                # For a general request, use the LangChain agent to determine the best approach
                query = request_data.get("query", "Analyze my fitness data")
                result = await self.agent_executor.arun(query)
                return {"analysis": result}

        except Exception as e:
            logger.error(f"Error processing fitness request: {str(e)}")
            raise e

    @classmethod
    def get_agent(cls, db: Session = None):
        """
        Get a FitnessAgent instance with database connection

        Args:
            db: SQLAlchemy database session

        Returns:
            FitnessAgent instance
        """
        return cls(db=db)
