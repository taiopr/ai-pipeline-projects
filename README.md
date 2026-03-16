# AI Pipeline Projects

A collection of Python scripts built while learning AI API integration,
automation patterns, and production engineering practices.

---

## three_apis.py

A Python script that calls three external APIs and combines their outputs
into a single AI-generated response.

### What it does

1. Fetches a random programming joke from JokeAPI
2. Fetches real-time weather for Barcelona from Open-Meteo
3. Combines both into a prompt sent to OpenAI GPT-4o-mini
4. Returns an AI-generated sentence that combines the weather and joke

### APIs used

- JokeAPI — https://jokeapi.dev (no auth required)
- Open-Meteo — https://open-meteo.com (no auth required)
- OpenAI — https://platform.openai.com (API key required)

### Setup

1. Clone the repo
2. Install dependencies: `pip install requests python-dotenv`
3. Create a `.env` file with your `OPENAI_API_KEY`
4. Run: `python three_apis.py`

### What I learned

- GET vs POST requests and when to use each
- How to authenticate with API keys via headers
- How to navigate nested JSON responses
- How to chain API outputs as context for subsequent calls

---

## joke_expander.py

Takes a user-input topic, finds a relevant joke using JokeAPI,
then uses OpenAI GPT-4o-mini to expand it into a longer, funnier version.

### What I learned

- How to handle API-level errors (error field in JSON response)
- How to use the temperature parameter in LLM calls
- How to use system prompts to shape model behavior
- Full Git branch workflow: create, commit, merge, delete

---

## csv_pipeline.py

Reads a list of topics from a CSV file, sends each one to OpenAI GPT-4o-mini,
and saves the AI-generated summaries to a new CSV file.

### What it does

1. Reads `topics.csv` — a table of topics and categories
2. For each row, sends the topic to OpenAI and requests a 2-sentence summary
3. Collects all results in memory
4. Writes everything to `summaries.csv` in one operation when all topics are done
5. Supports appending new topics without reprocessing existing ones
6. Supports retrying failed rows independently

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
- `time.sleep(0.5)` between calls prevents hitting OpenAI rate limits
- `results.append()` sits outside the try/except block — it runs whether the
  call succeeded or failed, so every row is always written to the output
- Integrates with `api_utils.py` for automatic retry on failed calls
- Integrates with `logger.py` to record every API call to `api_calls.json`

### What I learned

- How to read and write CSV files with csv.DictReader and csv.DictWriter
- Why `newline=""` and `encoding="utf-8"` are required for CSV file operations
- The difference between write mode `"w"` and append mode `"a"`
- How try/except inside a loop lets a pipeline survive individual failures
- Why indentation in Python is logic, not style — append inside except
  means it only runs on failure, which was a real bug in this script

---

## api_utils.py

A reusable utility module that adds automatic retry logic to any API call.
Import it into any script instead of rewriting retry logic every time.

### What it does

Wraps any function that makes an HTTP request. If the call fails with a
retryable error, it waits and tries again — up to a configurable maximum.
Each retry waits longer than the previous one using exponential backoff.

### Exponential backoff pattern
```
Attempt 1 fails → wait 1 second
Attempt 2 fails → wait 2 seconds
Attempt 3 fails → wait 4 seconds
Attempt 4 fails → wait 8 seconds → raise error
```

The wait doubles each attempt. This gives the server time to recover
without hammering it with repeated requests in quick succession.

### Which errors trigger a retry
```
429 — Too Many Requests   (rate limit hit — wait and retry)
500 — Internal Server Error  (server failed — wait and retry)
502 — Bad Gateway            (server failed — wait and retry)
503 — Service Unavailable    (server failed — wait and retry)
504 — Gateway Timeout        (server failed — wait and retry)
```

Errors that do NOT retry — because retrying will never fix them:
```
400 — Bad Request      (your code is wrong — fix it)
401 — Unauthorized     (API key is wrong — fix it)
404 — Not Found        (wrong URL — fix it)
```

### Usage
```python
from api_utils import call_with_retry

def make_request():
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    return response

result = call_with_retry(make_request, max_retries=4, base_wait=1.0)
```

### What I learned

- The difference between 4xx errors (your fault) and 5xx errors (their fault)
- Which status codes are worth retrying and which require a code fix
- How exponential backoff prevents overwhelming a struggling server
- How to write a reusable utility function that wraps any callable
- How to distinguish between HTTPError, ConnectionError, and Timeout

---

## logger.py

A reusable logging module that records every API call to a JSON file.
Captures what was sent, what came back, whether it succeeded, and how
long it took.

### What it does

Every time an API call is made through a script that imports this module,
a structured record is appended to `api_calls.json`. The log persists
across runs — every call ever made is preserved in the file.

### Log entry structure

Each entry in `api_calls.json` looks like this:
```json
{
  "timestamp": "2024-01-15T14:32:01.456789",
  "model": "gpt-4o-mini",
  "prompt": "Topic: Barcelona\nCategory: travel",
  "response": "Barcelona is the capital of Catalonia...",
  "status": "success",
  "duration_ms": 843,
  "error": null
}
```

### Usage
```python
from logger import log_api_call, print_log_summary

# Record a call
log_api_call(
    model       = "gpt-4o-mini",
    prompt      = "your prompt here",
    response    = "the response text",
    status      = "success",
    duration_ms = 843
)

# Print a summary of all calls so far
print_log_summary()
```

### What print_log_summary shows
```
==================================================
  API CALL LOG SUMMARY
==================================================
  Total calls:    8
  Successful:     8
  Failed:         0
  Avg duration:   921ms
==================================================
```

### Why this matters in production

- Debugging — when something breaks you can see exactly what was sent
- Cost tracking — every call is recorded so you can audit token usage
- Performance monitoring — duration_ms shows which calls are slow
- Audit trail — a permanent record of every action the pipeline took

### What I learned

- How to read and write JSON files with json.load and json.dump
- Why indent=2 in json.dump makes log files human-readable
- How to append to a JSON array without loading the whole file into memory
- How datetime.now().isoformat() produces a standard timestamp string
- Why loggers are built as separate modules — so any script can import
  them without duplicating code


## three_step_pipeline.py

An interactive 3-step pipeline that processes user input through an LLM
and saves formatted results to a JSON file.

### The three steps

1. Validate — cleans and validates user input before any API call is made
2. Process — sends the topic to OpenAI with a format-specific system prompt
3. Format and save — structures the result with metadata and appends to JSON

### Formats available

- summary    — 3-sentence factual summary
- bullets    — 5 bullet points
- eli5       — explain like I'm 5, with analogy
- technical  — explanation for an experienced engineer

### Output file — pipeline_results.json

Every successful run appends one entry to pipeline_results.json:
timestamp, topic, format, result text, word count, character count.

### What I learned

- How to design a pipeline architecture before writing code
- Separation of concerns — each function has exactly one job
- How format-specific system prompts change output without changing architecture
- How validation at Step 1 prevents unnecessary API calls
- How to append to a JSON array across multiple script runs


## webhook_trigger.py
 
Python script that sends test payloads to an n8n webhook.
Used to trigger and test the n8n Webhook → LLM → Discord workflow.
 
### What the n8n workflow does
1. Receives a JSON payload via HTTP POST (Webhook node)
2. Sends the topic to OpenAI GPT-4o-mini for a 2-sentence summary (OpenAI node)
3. Posts the summary to a Discord channel (Discord node)
 
### Usage
```
# Single test (first payload)
python webhook_trigger.py
 
# Run all 3 test payloads interactively
python webhook_trigger.py all
```
 
### What I learned
- n8n node structure: trigger → processing → output
- Webhook triggers: test URL vs production URL
- n8n expressions: {{ $json.field }} for data injection between nodes
- How to inspect node output panels to find correct data paths
- The visual pipeline equivalent of every Python pipeline pattern

---

## Setup for all scripts
```bash
# Clone the repo
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate      # Mac/Linux
.venv\Scripts\activate         # Windows

# Install dependencies
pip install requests python-dotenv

# Create .env file
echo "OPENAI_API_KEY=your-key-here" > .env
```

## Project structure
```
├── three_apis.py       — Three API pipeline with combined AI output
├── joke_expander.py    — Topic → joke → AI expansion pipeline
├── csv_pipeline.py     — Batch processing pipeline with CSV I/O
├── api_utils.py        — Reusable retry logic with exponential backoff
├── logger.py           — Reusable API call logger to JSON
├── topics.csv          — Input data for csv_pipeline.py
├── summaries.csv       — Output data from csv_pipeline.py
├── api_calls.json      — Persistent log of all API calls made
└── .env                — API keys (never commit this file)
```