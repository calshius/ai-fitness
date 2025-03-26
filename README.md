# AI Fitness Analyzer

## Overview

AI Fitness Analyzer is a Python application that uses artificial intelligence to analyze your fitness and nutrition data. It combines data from MyFitnessPal (MFP) and Garmin Connect to provide personalized insights and recommendations for improving your diet and exercise habits.

The application uses a Retrieval-Augmented Generation (RAG) approach, where it:
1. Processes your historical fitness data
2. Creates vector embeddings of this data
3. Retrieves relevant information based on your questions
4. Generates personalized recommendations using a language model

## Features

- **Data Integration**: Combines nutrition, exercise, weight measurements, and activity data
- **Natural Language Queries**: Ask questions about your fitness data in plain English
- **Personalized Analysis**: Get insights specific to your data and patterns
- **Structured Recommendations**: Receive clear observations, dietary suggestions, and summaries
- **Interactive Interface**: Simple command-line interface for asking multiple questions

## Requirements

- Python 3.10 or higher
- Hugging Face API token
- Exported data from MyFitnessPal and Garmin Connect

## Installation

1. Clone this repository:
git clone https://github.com/yourusername/ai-fitness.git cd ai-fitness
2. Install the required dependencies:
```bash
pip install -e .
```
3. For development tools (optional):
```bash
pip install -e ".[dev]"
```

## Data Setup

The application expects your fitness data to be organized in a specific folder structure:
```bash
ai-fitness/
└── data/
    ├── mfp/
    │   ├── Nutrition-Summary-YYYY-MM-DD-to-YYYY-MM-DD.csv
    │   ├── Exercise-Summary-YYYY-MM-DD-to-YYYY-MM-DD.csv
    │   └── Measurement-Summary-YYYY-MM-DD-to-YYYY-MM-DD.csv
    └── garmin/
        └── Activities.csv
```


### Exporting Your Data

#### MyFitnessPal Data
1. Log in to your MyFitnessPal account
2. Go to "Reports" > "Export Data"
3. Select the date range you want to analyze
4. Download the CSV files for Nutrition, Exercise, and Measurements
5. Place these files in the `data/mfp/` directory

#### Garmin Connect Data
1. Log in to Garmin Connect
2. Go to "Activities" > "All Activities"
3. Click on the gear icon and select "Export CSV"
4. Place the downloaded CSV file in the `data/garmin/` directory

## Hugging Face API Setup

The application uses Hugging Face's Inference API to access language models. You'll need to:

1. Create a free account at [Hugging Face](https://huggingface.co/)
2. Generate an API token from your account settings
3. Create a `.env` file in the root directory of the project
4. Add your API token to the `.env` file:
```bash
HUGGINGFACE_API_TOKEN=your_token_here
```

## Usage

Run the application:
```bash
python main.py
```

You'll be presented with a prompt where you can ask questions about your fitness and nutrition data. For example:

- "What are my best dietary habits based on days when I lost weight?"
- "What's the relationship between my protein intake and exercise performance?"
- "What meal patterns are associated with my most active days?"
- "How does my calorie intake compare to my exercise calories burned?"
- "What dietary changes should I make to improve my fitness results?"

The application will analyze your data and provide structured responses with:
- **Observations**: Key patterns and trends in your data
- **Dietary Suggestions**: Specific recommendations for improving your diet
- **Summary**: A concise overview of the main points

Type 'exit' to quit the application.

## How It Works

1. **Data Loading**: The application loads your CSV files into pandas DataFrames
2. **Document Creation**: It converts your data into text documents that can be embedded
3. **Vector Embeddings**: Uses a SentenceTransformer model to create vector embeddings
4. **RAG Implementation**: When you ask a question, it:
   - Embeds your question into the same vector space
   - Retrieves the most relevant documents using cosine similarity
   - Combines these documents into a context
   - Sends the context and question to the language model
5. **Response Formatting**: Structures the response into clear sections for better readability

## Limitations

- The free tier of Hugging Face's Inference API has limitations on model size and request frequency
- The quality of recommendations depends on the completeness and accuracy of your fitness data
- The application works best with consistent data over longer periods

## License

[MIT License](LICENSE)

## Acknowledgements

- This project uses the Sentence Transformers library for creating embeddings
- Language model access is provided by Hugging Face's Inference API
- Data analysis is powered by pandas and numpy
