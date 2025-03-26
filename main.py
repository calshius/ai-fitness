import json
import os
import textwrap
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load environment variables
load_dotenv()


class FitnessDataProcessor:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.nutrition_data = None
        self.exercise_data = None
        self.measurement_data = None
        self.garmin_activities = None
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.document_embeddings = None
        self.documents = None

    def load_data(self):
        """Load all CSV data files"""
        # Load nutrition data
        nutrition_path = os.path.join(
            self.data_dir, "mfp", "Nutrition-Summary-2024-11-11-to-2025-03-26.csv"
        )
        self.nutrition_data = pd.read_csv(nutrition_path)
        self.nutrition_data["Date"] = pd.to_datetime(self.nutrition_data["Date"])

        # Load exercise data
        exercise_path = os.path.join(
            self.data_dir, "mfp", "Exercise-Summary-2024-11-11-to-2025-03-26.csv"
        )
        self.exercise_data = pd.read_csv(exercise_path)
        self.exercise_data["Date"] = pd.to_datetime(self.exercise_data["Date"])

        # Load measurement data
        measurement_path = os.path.join(
            self.data_dir, "mfp", "Measurement-Summary-2024-11-11-to-2025-03-26.csv"
        )
        self.measurement_data = pd.read_csv(measurement_path)
        self.measurement_data["Date"] = pd.to_datetime(self.measurement_data["Date"])

        # Load Garmin activities
        garmin_path = os.path.join(self.data_dir, "garmin", "Activities.csv")
        self.garmin_activities = pd.read_csv(garmin_path)
        self.garmin_activities["Date"] = pd.to_datetime(self.garmin_activities["Date"])

        print("All data loaded successfully!")

    def create_documents(self):
        """Create text documents from the data for embedding"""
        documents = []

        # Create nutrition documents
        for date, group in self.nutrition_data.groupby("Date"):
            date_str = date.strftime("%Y-%m-%d")
            daily_calories = group["Calories"].sum()
            daily_protein = group["Protein (g)"].sum()
            daily_carbs = group["Carbohydrates (g)"].sum()
            daily_fat = group["Fat (g)"].sum()

            doc = (
                f"Date: {date_str}. Nutrition summary: Total calories: {daily_calories:.1f}, "
                f"Protein: {daily_protein:.1f}g, Carbs: {daily_carbs:.1f}g, Fat: {daily_fat:.1f}g. "
            )

            # Add meal details
            for _, row in group.iterrows():
                doc += (
                    f"{row['Meal']}: Calories {row['Calories']:.1f}, Protein {row['Protein (g)']:.1f}g, "
                    f"Carbs {row['Carbohydrates (g)']:.1f}g, Fat {row['Fat (g)']:.1f}g. "
                )

            documents.append({"text": doc, "type": "nutrition", "date": date_str})

        # Create exercise documents
        for date, group in self.exercise_data.groupby("Date"):
            date_str = date.strftime("%Y-%m-%d")
            total_calories = group["Exercise Calories"].sum()
            total_minutes = group["Exercise Minutes"].sum()
            steps = group["Steps"].sum()

            doc = (
                f"Date: {date_str}. Exercise summary: Burned {total_calories:.1f} calories, "
                f"Exercised for {total_minutes} minutes, Steps: {steps}. "
            )

            # Add exercise details
            for _, row in group.iterrows():
                if pd.notna(row["Exercise"]):
                    doc += (
                        f"Activity: {row['Exercise']}, Duration: {row['Exercise Minutes']} minutes, "
                        f"Calories: {row['Exercise Calories']}. "
                    )

            documents.append({"text": doc, "type": "exercise", "date": date_str})

        # Create measurement documents
        for _, row in self.measurement_data.iterrows():
            date_str = row["Date"].strftime("%Y-%m-%d")
            doc = f"Date: {date_str}. Measurement: Weight {row['Weight']} kg."
            documents.append({"text": doc, "type": "measurement", "date": date_str})

        # Create Garmin activity documents
        for _, row in self.garmin_activities.iterrows():
            date_str = row["Date"].strftime("%Y-%m-%d %H:%M:%S")
            doc = (
                f"Date: {date_str}. Garmin activity: {row['Activity Type']}, "
                f"Duration: {row['Total Time']}, Calories: {row['Calories']}"
            )

            if pd.notna(row["Distance"]) and float(row["Distance"]) > 0:
                doc += f", Distance: {row['Distance']} km"

            if pd.notna(row["Avg HR"]):
                doc += f", Average HR: {row['Avg HR']}"

            if pd.notna(row["Max HR"]):
                doc += f", Max HR: {row['Max HR']}"

            documents.append({"text": doc, "type": "garmin", "date": date_str})

        # Add summary documents
        avg_daily_calories = (
            self.nutrition_data.groupby("Date")["Calories"].sum().mean()
        )
        avg_daily_protein = (
            self.nutrition_data.groupby("Date")["Protein (g)"].sum().mean()
        )
        avg_daily_carbs = (
            self.nutrition_data.groupby("Date")["Carbohydrates (g)"].sum().mean()
        )
        avg_daily_fat = self.nutrition_data.groupby("Date")["Fat (g)"].sum().mean()

        summary_doc = (
            f"Nutrition summary for the entire period: Average daily calories: {avg_daily_calories:.1f}, "
            f"Average daily protein: {avg_daily_protein:.1f}g, Average daily carbs: {avg_daily_carbs:.1f}g, "
            f"Average daily fat: {avg_daily_fat:.1f}g."
        )
        documents.append({"text": summary_doc, "type": "summary", "date": "all"})

        # Weight trend
        if not self.measurement_data.empty:
            initial_weight = self.measurement_data.iloc[0]["Weight"]
            final_weight = self.measurement_data.iloc[-1]["Weight"]
            weight_change = final_weight - initial_weight

            weight_doc = (
                f"Weight trend: Started at {initial_weight} kg and ended at {final_weight} kg. "
                f"Total change: {weight_change:.1f} kg over the period."
            )
            documents.append({"text": weight_doc, "type": "summary", "date": "all"})

        self.documents = documents
        print(f"Created {len(documents)} documents from the data")
        return documents

    def create_embeddings(self):
        """Create embeddings for all documents"""
        if self.documents is None:
            self.create_documents()

        texts = [doc["text"] for doc in self.documents]
        self.document_embeddings = self.model.encode(texts)
        print("Created embeddings for all documents")
        return self.document_embeddings

    def retrieve_relevant_documents(self, query, top_k=5):
        """Retrieve the most relevant documents for a query"""
        if self.document_embeddings is None:
            self.create_embeddings()

        # Encode the query
        query_embedding = self.model.encode([query])[0]

        # Calculate similarities
        similarities = cosine_similarity([query_embedding], self.document_embeddings)[0]

        # Get top k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        # Return top k documents and their similarity scores
        results = []
        for idx in top_indices:
            results.append(
                {"document": self.documents[idx], "similarity": similarities[idx]}
            )

        return results

    def generate_context_from_query(self, query, top_k=5):
        """Generate a context string from relevant documents for a query"""
        relevant_docs = self.retrieve_relevant_documents(query, top_k)

        context = f"Based on the following fitness and nutrition data:\n\n"
        for i, doc in enumerate(relevant_docs):
            context += f"{i+1}. {doc['document']['text']}\n"

        return context


def get_llm_response(
    prompt,
    model_url="https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
):
    """Get a response from a free LLM model via Hugging Face"""
    api_token = os.getenv("HUGGINGFACE_API_TOKEN")
    if not api_token:
        print("Please set your HUGGINGFACE_API_TOKEN in a .env file")
        return "Error: No API token found"

    headers = {"Authorization": f"Bearer {api_token}"}

    try:
        response = requests.post(
            model_url,
            headers=headers,
            json={"inputs": prompt, "parameters": {"max_length": 1024}},
        )

        if response.status_code == 200:
            return response.json()[0]["generated_text"]
        else:
            return f"Error: {response.status_code} - {response.text}"

    except Exception as e:
        return f"Error connecting to LLM: {e}"


def analyze_fitness_data(processor, query):
    """Analyze fitness data using RAG approach"""
    # Generate context from relevant documents
    context = processor.generate_context_from_query(query, top_k=7)

    # Create the full prompt with structured output instructions
    prompt = f"""
    {context}
    
    Based on the above fitness and nutrition data, please answer the following question:
    {query}
    
    Please structure your response in the following format:
    
    OBSERVATIONS:
    - List key observations from the data
    - Include patterns, trends, and notable points
    - Highlight correlations between diet, exercise, and measurements
    
    DIETARY SUGGESTIONS:
    - Provide specific dietary recommendations
    - Include macronutrient targets if relevant
    - Suggest meal timing and composition
    - List foods to include or avoid
    
    SUMMARY:
    A brief conclusion summarizing the key points and most important recommendations.
    
    Make sure each section is clearly labeled and separated.
    """

    # Get response from LLM
    response = get_llm_response(prompt)

    return response


def format_output(response):
    """Format the LLM response for better readability"""
    # Check if response is an error message
    if response.startswith("Error:"):
        return response

    # Split the response into sections
    sections = {"OBSERVATIONS": "", "DIETARY SUGGESTIONS": "", "SUMMARY": ""}

    current_section = None
    lines = response.split("\n")

    for line in lines:
        # Check if line contains a section header
        for section in sections.keys():
            if section in line.upper():
                current_section = section
                break

        # Add line to current section if we're in a section
        if current_section:
            sections[current_section] += line + "\n"

    # Format the output with colors and styling
    formatted_output = ""

    # If the response doesn't have our expected structure, return it as is
    if all(v == "" for v in sections.values()):
        return response

    # Format each section
    for section, content in sections.items():
        if content:
            # Add section header with styling
            formatted_output += f"\n\033[1;36m{section}\033[0m\n"
            formatted_output += "=" * len(section) + "\n"

            # Add section content with bullet points highlighted
            for line in content.split("\n"):
                if line.strip().startswith("-"):
                    # Highlight bullet points
                    formatted_output += f"\033[1;33m{line}\033[0m\n"
                elif line.strip().startswith("•"):
                    # Highlight bullet points (alternative symbol)
                    formatted_output += f"\033[1;33m{line}\033[0m\n"
                else:
                    formatted_output += line + "\n"

    return formatted_output


def main():
    print("Welcome to AI Fitness - Dietary and Exercise Analysis!")

    # Initialize data processor
    processor = FitnessDataProcessor()

    try:
        # Load data
        processor.load_data()

        # Create documents and embeddings
        processor.create_documents()
        processor.create_embeddings()

        # Main interaction loop
        while True:
            print("\n" + "=" * 50)
            print("What would you like to know about your fitness and nutrition data?")
            print("(Type 'exit' to quit)")

            query = input("> ")

            if query.lower() in ["exit", "quit", "q"]:
                break

            print("\nAnalyzing your data...")
            response = analyze_fitness_data(processor, query)

            print("\nAI Analysis:")
            print("-" * 50)
            # Format the response with proper structure
            formatted_response = format_output(response)
            print(formatted_response)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
