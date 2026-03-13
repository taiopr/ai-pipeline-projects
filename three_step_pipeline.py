import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from api_utils import call_with_retry
from logger import log_api_call, print_log_summary

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OUTPUT_FILE    = "pipeline_results.json"


# ─────────────────────────────────────────────────────
# STEP 1 — VALIDATE INPUT
#
# Takes raw user input and returns clean usable string.
# Returns None if input is invalid — caller handles this.
# Keeps validation logic separate from business logic.
# ─────────────────────────────────────────────────────
def validate_input(raw_input: str) -> str | None:
    # Remove leading and trailing whitespace
    cleaned = raw_input.strip()

    # Empty input check — user just pressed Enter
    if not cleaned:
        print("Error: Input cannot be empty.")
        return None

    # Too short — not enough to generate meaningful content
    if len(cleaned) < 3:
        print("Error: Input too short. Please enter at least 3 characters.")
        return None

    # Too long — LLMs work better with focused prompts
    if len(cleaned) > 200:
        print("Error: Input too long. Please keep it under 200 characters.")
        return None

    return cleaned


# ─────────────────────────────────────────────────────
# STEP 2 — LLM PROCESSING
#
# Takes clean topic string.
# Calls OpenAI with retry logic.
# Logs the call.
# Returns the raw LLM response text.
# ─────────────────────────────────────────────────────
def process_with_llm(topic: str, output_format: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # System prompt changes based on format choice
    # This shows how the same pipeline can produce different outputs
    # by changing only the instruction — not the architecture
    format_instructions = {
        "summary":    "Write a clear 3-sentence summary.",
        "bullets":    "Write exactly 5 bullet points. Start each with '•'.",
        "eli5":       "Explain this like I am 5 years old. Use simple words and one analogy.",
        "technical":  "Write a technical explanation for an experienced software engineer.",
    }

    # Default to summary if format not recognised
    instruction = format_instructions.get(output_format, format_instructions["summary"])

    prompt = f"Topic: {topic}"

    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are a knowledgeable assistant. "
                    f"{instruction} "
                    f"Be specific and accurate. No filler phrases."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 300,
        "temperature": 0.4
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

        # Re-raise so the orchestrator can handle it
        raise


# ─────────────────────────────────────────────────────
# STEP 3 — FORMAT AND SAVE
#
# Takes topic + raw LLM text.
# Structures it with metadata.
# Appends to JSON output file.
# Prints formatted result to terminal.
# ─────────────────────────────────────────────────────
def format_and_save(topic: str, output_format: str, result_text: str) -> dict:
    # Build a structured entry with metadata
    # This is richer than a plain text file — every field is queryable
    entry = {
        "timestamp":    datetime.now().isoformat(),
        "topic":        topic,
        "format":       output_format,
        "result":       result_text,
        "word_count":   len(result_text.split()),
        "char_count":   len(result_text)
    }

    # Load existing entries from file — or start fresh if file doesn't exist
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            try:
                all_entries = json.load(f)
            except json.JSONDecodeError:
                # File exists but is corrupted or empty — start fresh
                all_entries = []
    else:
        all_entries = []

    # Append new entry
    all_entries.append(entry)

    # Write all entries back — this preserves history across runs
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2, ensure_ascii=False)

    # Print formatted output to terminal
    # Separator width matches the topic line for clean alignment
    width = 56
    print(f"\n{'─' * width}")
    print(f"  TOPIC:   {topic}")
    print(f"  FORMAT:  {output_format}")
    print(f"  WORDS:   {entry['word_count']}")
    print(f"{'─' * width}")
    print(f"\n{result_text}\n")
    print(f"{'─' * width}")
    print(f"  Saved to {OUTPUT_FILE} — entry {len(all_entries)} of {len(all_entries)}")
    print(f"{'─' * width}\n")

    return entry


# ─────────────────────────────────────────────────────
# ORCHESTRATOR — Wires the three steps together
#
# This function knows nothing about HOW each step works.
# It only knows the order and what to pass between steps.
# If any step fails, it handles it cleanly.
# ─────────────────────────────────────────────────────
def run_pipeline(topic: str, output_format: str) -> dict | None:
    print(f"\nRunning pipeline for: '{topic}' [{output_format}]")

    # ── Step 1 ────────────────────────────────────────
    clean_topic = validate_input(topic)

    if clean_topic is None:
        # validate_input already printed the error message
        return None

    # ── Step 2 ────────────────────────────────────────
    try:
        result_text = process_with_llm(clean_topic, output_format)
    except Exception as e:
        print(f"Pipeline failed at Step 2 (LLM): {e}")
        return None

    # ── Step 3 ────────────────────────────────────────
    try:
        entry = format_and_save(clean_topic, output_format, result_text)
    except Exception as e:
        print(f"Pipeline failed at Step 3 (Save): {e}")
        return None

    return entry


# ─────────────────────────────────────────────────────
# INTERACTIVE MODE — Runs the pipeline repeatedly
# Lets you test multiple inputs without restarting
# ─────────────────────────────────────────────────────
def run_interactive():
    print("\n" + "═" * 56)
    print("  THREE-STEP AI PIPELINE")
    print("  Type 'quit' to exit | Type 'log' to see call summary")
    print("═" * 56)

    # Available formats shown to user
    formats = ["summary", "bullets", "eli5", "technical"]
    format_display = " | ".join(formats)

    while True:
        print(f"\nFormats available: {format_display}")

        # Get topic
        topic = input("Enter topic (or 'quit'): ").strip()

        if topic.lower() == "quit":
            print("\nExiting. Final log summary:")
            print_log_summary()
            break

        if topic.lower() == "log":
            print_log_summary()
            continue

        # Get format
        fmt = input(f"Enter format [{format_display}]: ").strip().lower()

        # Default to summary if invalid format entered
        if fmt not in formats:
            print(f"Format '{fmt}' not recognised — using 'summary'")
            fmt = "summary"

        # Run the pipeline
        result = run_pipeline(topic, fmt)

        if result:
            another = input("Run again? (y/n): ").strip().lower()
            if another != "y":
                print("\nFinal log summary:")
                print_log_summary()
                break


# ─────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    run_interactive()