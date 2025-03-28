import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_llm_response(
    prompt,
    system_role="You are a helpful fitness and nutrition assistant.",
    model_url="https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
):
    """Get a response from a free LLM model via Hugging Face"""
    api_token = os.getenv("HUGGINGFACE_API_TOKEN")
    if not api_token:
        print("Please set your HUGGINGFACE_API_TOKEN in a .env file")
        return "Error: No API token found"

    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Add system role to the prompt
    full_prompt = f"{system_role}\n\n{prompt}"

    try:
        response = requests.post(
            model_url,
            headers=headers,
            json={"inputs": full_prompt, "parameters": {"max_length": 1024}},
        )

        if response.status_code == 200:
            return response.json()[0]["generated_text"]
        else:
            return f"Error: {response.status_code} - {response.text}"

    except Exception as e:
        return f"Error connecting to LLM: {e}"

def analyze_fitness_data(processor, query, system_role="You are a helpful fitness and nutrition assistant.", top_k=7):
    """Analyze fitness data using RAG approach"""
    # Generate context from relevant documents
    context = processor.generate_context_from_query(query, top_k=top_k)

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
    response = get_llm_response(prompt, system_role)

    return response
