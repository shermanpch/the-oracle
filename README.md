# The Oracle -  I Ching Interpreter

A modern API and web application for I Ching interpretation using AI.

## Overview

This application provides I Ching readings based on three numbers provided by the user. It uses OpenAI's GPT models to generate interpretations based on traditional I Ching texts. User readings are stored in a Supabase database.

The application consists of:
- A FastAPI backend that serves as an API for the frontend
- A Streamlit web interface for user interaction
- A Supabase database for storing I Ching texts and user readings
- A data directory containing I Ching texts and images

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│  FastAPI    │────▶│  Oracle     │
│  (Streamlit)│◀────│   Backend   │◀────│  Logic      │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  OpenAI API │     │  Supabase   │
                    │  (GPT-4)    │     │  Database   │
                    └─────────────┘     └─────────────┘
```

## Features

- RESTful API for I Ching readings
- Web interface for easy interaction
- User authentication and reading history
- Structured output format for consistent readings
- Docker support for easy deployment
- Environment variable configuration

## Getting Started

### Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.9+ (if running without Docker)
- OpenAI API key
- Supabase account and project

### Data Generation

Before setting up the database, you need to generate the I Ching data that will be stored in Supabase. The project includes a web scraper that collects hexagram information and images:

1. Ensure you've installed all dependencies from requirements.txt:
   ```
   pip install -r requirements.txt
   ```
   Note: All necessary dependencies for the scraper (requests, beautifulsoup4, tqdm) are already included in the requirements.txt file.

2. Run the scraper to populate the data directory:
   ```
   python -m src.utils.scraper
   ```

This will create a structured `data/` directory containing I Ching hexagram texts and images that will be used in the migration process.

### Supabase Setup

1. Create a new Supabase project at [https://supabase.com](https://supabase.com)
2. Get your Supabase URL and keys from the project settings
3. Add the following to your `.env` file:
   ```
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_API_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_KEY=your_supabase_service_role_key
   ```
4. Ensure you've generated the data using the scraper (see Data Generation section)
5. Run the database setup scripts:
   ```
   python scripts/generate_supabase_setup.py
   python scripts/migrate_to_supabase.py
   ```
6. Verify your setup by running the application and testing the connection

### Running with Docker

1. Clone the repository
2. Create a `.env` file with your OpenAI API key and Supabase credentials (use `.env.example` as a template)
3. Run the application:
   ```
   docker-compose -f docker/docker-compose.yml up -d
   ```
4. Access the web interface at http://localhost:8501
5. Access the API at http://localhost:8000

### Running without Docker

1. Clone the repository
2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your OpenAI API key and Supabase credentials (use `.env.example` as a template)
4. Run the application using the main.py script:
   ```
   # Run both API and web interface
   python main.py --app both
   
   # Or run just the API
   python main.py --app api
   
   # Or run just the web interface
   python main.py --app web
   ```

## Streamlit Configuration

The Streamlit web interface is configured directly within the code, eliminating the need for an external config.toml file. This makes the application more self-contained and easier to deploy.

Configuration is handled through:

1. Custom CSS in the `add_custom_styles()` function
2. Page settings in `st.set_page_config()`
3. Logging configuration at the top of the `streamlit_app.py` file

To customize the appearance of the application, you can modify these sections directly in the `src/app/web/streamlit_app.py` file.

## API Endpoints

- `GET /`: Root endpoint to check if the API is running
- `GET /health`: Health check endpoint
- `GET /languages`: Get available languages
- `POST /oracle`: Get an I Ching reading
- `GET /user/readings`: Get a user's reading history (requires authentication)

### Authentication

User authentication is handled through Supabase. The API endpoints that require authentication expect a Bearer token in the Authorization header:

```
Authorization: Bearer your_jwt_token
```

### Example API Request

```json
POST /oracle
{
  "question": "What should I focus on in my career?",
  "first_number": 7,
  "second_number": 3,
  "third_number": 5,
  "language": "English"
}
```

## Project Structure

The project follows a modular structure:
```
oracle/
├── src/
│   ├── __init__.py
│   ├── app/
│   │   ├── api/           # FastAPI backend
│   │   ├── core/          # Core oracle logic
│   │   │   ├── coordinate.py
│   │   │   ├── hexagram.py
│   │   │   ├── oracle.py
│   │   │   └── output.py
│   │   └── web/           # Streamlit frontend
│   └── utils/             # Utility functions
│       └── scraper.py     # Web scraper for I Ching data
├── docker/                # Docker configuration
│   ├── Dockerfile
│   ├── Dockerfile.streamlit
│   └── docker-compose.yml
├── scripts/               # Database setup scripts
│   ├── generate_supabase_setup.py
│   ├── migrate_to_supabase.py
│   └── sql/
├── data/                  # I Ching texts and images (generated by scraper)
├── main.py                # Main entry point
├── requirements.txt
├── .env.example           # Example environment variables
└── README.md
```

## Command-Line Interface

The application provides a command-line interface through main.py:

```bash
# Run both the API server and Streamlit web application
python main.py --app both

# Run only the API server
python main.py --app api

# Run only the Streamlit web application
python main.py --app web

# Additional options
python main.py --help
```

## Database Schema

### iching_texts

Stores the I Ching hexagram texts and line change interpretations.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| path | TEXT | Logical path to the content |
| parent_coord | TEXT | Primary coordinate (e.g., hexagram number) |
| child_coord | TEXT | Secondary coordinate (e.g., line position) |
| content | TEXT | JSON string containing the textual content |
| created_at | TIMESTAMP | Creation timestamp |

### user_readings

Stores user reading history and predictions.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | User ID (from Supabase Auth) |
| question | TEXT | User's question |
| first_number | INTEGER | First input number |
| second_number | INTEGER | Second input number |
| third_number | INTEGER | Third input number |
| language | TEXT | Reading language |
| prediction | JSONB | Structured prediction output |
| created_at | TIMESTAMP | Creation timestamp |

## Utilities

### Web Scraper

The `src/utils/scraper.py` utility is used to scrape I Ching hexagram information from various sources. It:

1. Fetches hexagram data from predefined URLs
2. Parses the HTML content to extract titles, descriptions, and images
3. Saves the content to a structured directory format in the `data/` folder
4. Downloads and saves associated hexagram images

This utility is a prerequisite for the database migration process, as it generates the data that will be loaded into Supabase.

Example of generated directory structure:
```
data/
├── 1-1/             # Hexagram number format
│   ├── images/      # Contains hexagram images
│   └── 0/           # Line position
│       ├── html/    # Contains text content
│       └── images/  # Contains line-specific images
├── 1-2/
└── ...
```

## Dependencies

The project relies on the following main dependencies:
- FastAPI: Web framework for the API
- Streamlit: Frontend framework
- OpenAI: AI model for generating interpretations
- Supabase: Database and authentication
- Pydantic: Data validation and settings management
- Uvicorn: ASGI server for running the API

## License

MIT 