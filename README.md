# AI Fitness Analyzer

![AI Fitness Demo](./images/query-vid.gif)

## Overview

AI Fitness Analyzer is a web application that uses artificial intelligence to analyze your fitness and nutrition data. It combines data from MyFitnessPal (MFP) and Garmin Connect to provide personalized insights and recommendations for improving your diet and exercise habits.

The application uses a Retrieval-Augmented Generation (RAG) approach, where it:
1. Processes your historical fitness data
2. Creates vector embeddings of this data
3. Retrieves relevant information based on your questions
4. Generates personalized recommendations using a language model

The project includes a FastAPI backend for data processing and a SvelteKit frontend that provides a user-friendly interface for interacting with the AI fitness analysis capabilities.

## Features

- **Data Integration**: Combines nutrition, exercise, weight measurements, and activity data
- **Natural Language Queries**: Ask questions about your fitness data in plain English
- **Personalized Analysis**: Get insights specific to your data and patterns
- **Structured Recommendations**: Receive clear observations, dietary suggestions, and summaries
- **Interactive Chat Interface**: Conversational UI for asking questions about your fitness data
- **Multiple AI Models**: Choose from various language models with different capabilities and speeds
- **File Upload**: Easy upload of fitness data files from MyFitnessPal and Garmin Connect

## Project Structure

The project consists of two main components:

1. **FastAPI Backend**: The core AI fitness analysis engine
2. **SvelteKit Frontend**: A web interface for interacting with the analysis engine

```bash
ai-fitness/
├── ai_fitness_backend/
│   ├── src/
│   │   └── ai_fitness_backend/
│   │       ├── main.py
│   │       ├── database.py
│   │       └── routers/
│   └── ...
├── ai_fitness_ui/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/
│   │   │   ├── stores/
│   │   │   └── api.js
│   │   └── routes/
│   │       ├── +page.svelte
│   │       ├── +layout.svelte
│   │       └── upload/
│   │           └── +page.svelte
│   └── ...
└── data/
    ├── mfp/
    │   ├── Nutrition-Summary-YYYY-MM-DD-to-YYYY-MM-DD.csv
    │   ├── Exercise-Summary-YYYY-MM-DD-to-YYYY-MM-DD.csv
    │   └── Measurement-Summary-YYYY-MM-DD-to-YYYY-MM-DD.csv
    └── garmin/
        └── Activities.csv
```

## Requirements

### Backend
- Python 3.10 or higher
- FastAPI
- Uvicorn
- Database dependencies
- Hugging Face API token (if used)

### Frontend
- Node.js and npm
- SvelteKit

## Installation

### Backend

1. Clone this repository:
```bash
git clone https://github.com/calshius/ai-fitness.git
cd ai-fitness
```

2. Install the backend dependencies:
```bash
cd ai_fitness_backend
pip install -e .
```

3. For development tools (optional):
```bash
pip install -e ".[dev]"
```

### Frontend

1. Navigate to the frontend directory:
```bash
cd ai_fitness_ui
```

2. Install npm dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

## Data Setup

The application expects your fitness data to be organized in a specific folder structure as shown in the Project Structure section.

### Exporting Your Data

#### MyFitnessPal Data
1. Log in to your MyFitnessPal account on the website
2. Go to "Reports" in the main menu
3. Select the date range you want to export
4. Click on "Export Data" at the bottom of the page
5. Save the CSV files for Nutrition, Exercise, and Measurements

#### Garmin Connect Data
1. Log in to Garmin Connect on the website
2. Click on your profile icon in the top right
3. Select "Settings" then "Account Information"
4. Scroll down to "Data Management" and click "Export Data"
5. Select "Activities" and choose CSV format
6. Click "Export" and save the file

## Environment Setup

Create a `.env` file in the root directory of the backend with the following variables:

```
DATABASE_URL=your_database_url
HUGGINGFACE_API_TOKEN=your_token_here  # If using Hugging Face
```

## Usage

### Database Setup

The application uses PostgreSQL as its database. You can run it using Docker Compose:

1. Navigate to the backend directory:
```bash
cd ai_fitness_backend
```

2. Start the PostgreSQL database using Docker Compose:
```bash
docker-compose up -d
```

This will start a PostgreSQL instance with the following configuration:
- Username: postgres
- Password: postgres
- Database: ai_fitness
- Port: 5432

You can verify the database is running with:
```bash
docker ps
```

To stop the database when you're done:
```bash
docker-compose down
```

### Running the Backend

Start the FastAPI server:
```bash
cd ai_fitness_backend
python run.py
```

The API will be available at http://localhost:8000 with documentation at http://localhost:8000/docs

### Running the Frontend

Start the SvelteKit development server:
```bash
cd ai_fitness_ui
npm run dev
```

The web application will be available at http://localhost:5173

### Using the Application

1. Upload your fitness data files through the upload page
2. Navigate to the chat interface
3. Ask questions about your fitness and nutrition data
4. Receive personalized insights and recommendations

Example questions you can ask:
- "What are my best dietary habits based on days when I lost weight?"
- "What's the relationship between my protein intake and exercise performance?"
- "What meal patterns are associated with my most active days?"
- "How does my calorie intake compare to my exercise calories burned?"
- "What dietary changes should I make to improve my fitness results?"

## How It Works

1. **Data Upload**: Upload your fitness data files through the web interface
2. **Data Processing**: The backend processes and stores your data
3. **Chat Interface**: Ask questions about your fitness data through the chat UI
4. **RAG Implementation**: When you ask a question, it:
   - Retrieves relevant information from your fitness data
   - Generates a personalized response based on your data
5. **Response Display**: The answer is displayed in the chat interface

## API Endpoints

- `GET /api/query`: Query your fitness data with natural language
- `POST /api/upload`: Upload fitness data files

## Limitations

- The quality of recommendations depends on the completeness and accuracy of your fitness data
- The application works best with consistent data over longer periods

## License

[MIT License](LICENSE)

## Acknowledgements

- Backend powered by FastAPI
- Frontend built with SvelteKit
- Data analysis powered by pandas and numpy
- Vector embeddings and language models for AI analysis
