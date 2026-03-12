from logger import log_api_call, print_log_summary
from api_utils import call_with_retry

import os
import csv
import time
import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ─────────────────────────────────────────────────────
# READ — Load all topics from the input CSV
# Returns a list of dictionaries, one per row
# ─────────────────────────────────────────────────────
def read_topics(filepath: str) -> list:
    topics = []

    # Check file exists before trying to open it
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        print("Create a CSV file with 'topic' and 'category' columns.")
        return []
    
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # strip() removes accidental whitespace around values
            topics.append({
                "topic": row ["topic"].strip(),
                "category": row["category"].strip()
            })

    print(f"Loaded {len(topics)} topics from {filepath}")
    return topics


# ─────────────────────────────────────────────────────
# PROCESS — Send one topic to the LLM, get a summary
# This function handles one row at a time
# The loop in run_pipeline calls it for every row
# ─────────────────────────────────────────────────────
def get_summary(topic: str, category: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Assign prompt to a variable so it can be passed to log_api_call
    prompt = f"Topic: {topic}\nCategory: {category}"

    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a concise encyclopedia. "
                    "Write exactly 2 sentences about the given topic. "
                    "Be factual, specific, and informative. "
                    "No fluff, no filler."
                )
            },
            {
                "role": "user",
                "content": prompt  # ← Use the variable here too
            }
        ],
        "max_tokens": 120,
        "temperature": 0.3
    }

    def make_request():
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=body
        )
        response.raise_for_status()
        return response

    start_time = time.time()

    try:
        response    = call_with_retry(make_request, max_retries=4, base_wait=1.0)
        data        = response.json()
        result_text = data["choices"][0]["message"]["content"].strip()
        duration_ms = int((time.time() - start_time) * 1000)

        log_api_call(
            model       = "gpt-4o-mini",
            prompt      = prompt,
            response    = result_text,
            status      = "success",
            duration_ms = duration_ms
        )

        return result_text

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)

        log_api_call(
            model       = "gpt-4o-mini",
            prompt      = prompt,
            response    = None,
            status      = "failed",
            duration_ms = duration_ms,
            error       = str(e)
        )

        raise



# ─────────────────────────────────────────────────────
# WRITE — Save all results to the output CSV
# Called once after all topics are processed
# ─────────────────────────────────────────────────────
def write_results(results: list, filepath: str) -> None:
    fieldnames = ["topic", "category", "summary", "status"]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to {filepath}")


# ─────────────────────────────────────────────────────
# PIPELINE — Orchestrates read → process → write
# This is the automation pattern:
# read every row, process it, collect results, save all
# ─────────────────────────────────────────────────────
def run_pipeline(input_file: str, output_file: str) -> None:
    # Step 1 - Read Input
    topics = read_topics(input_file)

    if not topics:
        return   # Exit early if no topics loaded
    
    results = []
    total = len(topics)

    # Step 2 - Process each topic
    for i, row in enumerate(topics, start=1):
        topic  = row["topic"]
        category = row["category"]

        print(f"[{i}/{total}] Processing: {topic}")

        # try/except around each API call
        # If one topic fails, the pipeline continues with the rest
        # Without this, one bad API call stops everything
        try:
            summary = get_summary(topic, category)
            status = "success"
            print(f"      ✓ Done")

        except Exception as e:
            # Store the error message instead of the summary
            summary = f"Error: {str(e)}"
            status = "failed"
            print(f"      ✗ Failed: {e}")

        results.append({
            "topic":    topic,
            "category": category,
            "summary":  summary,
            "status":   status
        })

        # Rate limiting - pause between API calls
        # OpemAI free tier allows ~3 requests per minute
        # 0.5 seconds between calls keeps you well under limits
        # Remove or reduce this if you have a paid tier
        if i < total:   # No need to wait after the last item
            time.sleep(0.5)

    # Step 3 - Write output
    write_results(results, output_file)

    # Step 4 - Print summary
    successful = sum(1 for r in results if r["status"] == "success")
    failed     = sum(1 for r in results if r["status"] == "failed")

    print(f"\nPipeline complete.")
    print(f"  Successful: {successful}/{total}")
    if failed > 0:
        print(f"  Failed:     {failed}/{total} - check output CSV for details")

    # Show API call log summary
    print_log_summary()


# ─────────────────────────────────────────────────────
# APPEND MODE — Add new topics without reprocessing old ones

# ─────────────────────────────────────────────────────

def append_new_topics(new_topics_file: str, output_file: str) -> None:
    # Read topics that already have summaries
    processed = set()

    if os.path.exists(output_file):
        with open(output_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed.add(row["topic"])

    # Read new topics
    new_topics = read_topics(new_topics_file)

    # Filter to only unprocessed ones
    to_process = [t for t in new_topics if t["topic"] not in processed]

    if not to_process:
        print("All topics already processed. Nothing to add.")
        return

    print(f"Found {len(to_process)} new topics to process.")

    # Process and append
    fieldnames = ["topic", "category", "summary", "status"]

    with open(output_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        for i, row in enumerate(to_process, start=1):
            print(f"[{i}/{len(to_process)}] Processing: {row['topic']}")
            try:
                summary = get_summary(row["topic"], row["category"])
                status  = "success"
            except Exception as e:
                summary = f"Error: {str(e)}"
                status  = "failed"

            writer.writerow({
                "topic":    row["topic"],
                "category": row["category"],
                "summary":  summary,
                "status":   status
            })

            if i < len(to_process):
                time.sleep(0.5)

    print("New topics appended to output file.")



# ─────────────────────────────────────────────────────
# FAILED ROWS - Read the failed rows and retry them

# ─────────────────────────────────────────────────────

def retry_failed(output_file: str) -> None:
    # Read the output file and find failed rows
    rows = []

    with open(output_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    failed = [r for r in rows if r["status"] == "failed"]

    if not failed:
        print("No failed rows to retry.")
        return

    print(f"Retrying {len(failed)} failed rows...")

    # Retry each failed row
    for row in rows:
        if row["status"] == "failed":
            try:
                summary       = get_summary(row["topic"], row["category"])
                row["summary"] = summary
                row["status"]  = "success"
                print(f"  ✓ Retry succeeded: {row['topic']}")
            except Exception as e:
                print(f"  ✗ Retry failed again: {row['topic']} — {e}")

    # Rewrite the entire file with updated rows
    fieldnames = ["topic", "category", "summary", "status"]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Output file updated with retry results.")


# ─────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    run_pipeline(
        input_file="topics.csv",
        output_file="summaries.csv"
    )
# if __name__ == "__main__":
#    retry_failed("summaries.csv")