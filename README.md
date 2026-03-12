# Three API Pipeline

A Python script that calls three external APIs and combines their outputs into a single AI-generated response.

## What it does

1. Fetches a random programming joke from JokeAPI
2. Fetches real-time weather for Barcelona from Open-Meteo
3. Combines both into a prompt sent to OpenAI GPT-4o-mini
4. Returns an AI-generated sentence that combines the weather and joke

## APIs used

- JokeAPI — https://jokeapi.dev (no auth required)
- Open-Meteo — https://open-meteo.com (no auth required)
- OpenAI — https://platform.openai.com (API key required)

## Setup

1. Clone the repo
2. Install dependencies: pip install requests python-dotenv
3. Create a .env file with your OPENAI_API_KEY
4. Run: python three_apis.py

## What I learned

- GET vs POST requests and when to use each
- How to authenticate with API keys via headers
- How to navigate nested JSON responses
- How to chain API outputs as context for subsequent calls

## joke_expander.py

Takes a user-input topic, finds a relevant joke using JokeAPI,
then uses OpenAI GPT-4o-mini to expand it into a longer,
funnier version.

### What I learned
- How to handle API-level errors (error field in JSON response)
- How to use the temperature parameter in LLM calls
- How to use system prompts to shape model behavior
- Full Git branch workflow: create, commit, merge, delete

## csv_pipeline.py

Reads a list of topics from a CSV file, sends each one to OpenAI GPT-4o-mini,
and saves the AI-generated summaries to a new CSV file.

### What it does

1. Reads topics.csv — a table of topics and categories
2. For each row, sends the topic to OpenAI and requests a 2-sentence summary
3. Collects all results in memory
4. Writes everything to summaries.csv in one operation when all topics are done

### Input format (topics.csv)
```csv
topic,category
machine learning,technology
Barcelona,travel
```

### Output format (summaries.csv)
```csv
topic,category,summary,status
machine learning,technology,Machine learning is a subset of AI...,success
Barcelona,travel,Barcelona is the capital of Catalonia...,success
```

### The automation pattern

This script is a batch processing pipeline. The structure is:
```
Input file (CSV)
      ↓
Read all rows into memory
      ↓
Loop — for each row:
    Call external API
    Collect result
      ↓
Write all results to output file
```

This pattern appears everywhere in real automation:
- Rewriting 500 product descriptions from a spreadsheet
- Classifying 1000 support tickets by category
- Summarising a list of documents for a client report

The input is always a structured list. The processing is always one API call
per item. The output is always the original data plus the new AI-generated column.

### Key implementation details

- Each API call is wrapped in try/except — one failure does not stop the pipeline
- Failed rows are written to the output CSV with status "failed" and the error
  message in the summary column — so you can see exactly what went wrong
- time.sleep(0.5) between calls prevents hitting OpenAI rate limits
- results.append() sits outside the try/except block — it runs whether the
  call succeeded or failed, so every row is always written to the output

### What I learned

- How to read and write CSV files with csv.DictReader and csv.DictWriter
- Why newline="" and encoding="utf-8" are required for CSV file operations
- The difference between write mode "w" and append mode "a"
- How try/except inside a loop lets a pipeline survive individual failures
- Why indentation in Python is logic, not style — append inside except
  means it only runs on failure, which was a real bug in this script