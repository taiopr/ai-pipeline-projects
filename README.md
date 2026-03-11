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