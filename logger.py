import json
import os
from datetime import datetime


# ─────────────────────────────────────────────────────
# API CALL LOGGER
#
# Records every API call to a JSON file.
# Each entry captures: when, what was sent, what came back,
# whether it succeeded, and how long it took.
# ─────────────────────────────────────────────────────

LOG_FILE = "api_calls.json"


def load_log() -> list:
    """
    Load existing log entries from the JSON file.
    Returns empty list if file doesn't exist yet.
    """
    if not os.path.exists(LOG_FILE):
        return[]
    
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # File exists but is empty or corrupted
            # Return empty list rather than crashing
            return []
        

def save_log(entries: list) -> None:
    """
    Write all log entries back to the JSON file.
    indent=2 makes it human-readable in any text editor.
    """
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def log_api_call(
    model:      str,
    prompt:     str,
    response:   str,
    status:     str,
    duration_ms: int,
    error:      str = None
) -> None:
    """
    Record one API call to the log file.

    model       — which model was called (gpt-4o-mini, claude-3 etc)
    prompt      — what was sent to the model
    response    — what came back (or None if it failed)
    status      — "success" or "failed"
    duration_ms — how long the call took in milliseconds
    error       — error message if failed (optional)
    """

    # Build the log entry as a dictionary
    entry = {
        "timestamp":   datetime.now().isoformat(),  # "2024-01-15T14:32:01.456789"
        "model":       model,
        "prompt":      prompt,
        "response":    response,
        "status":      status,
        "duration_ms": duration_ms,
        "error":       error
    }

    # Load existing entries, append new one, save back
    # This preserves the full history rather than overwriting
    entries = load_log()
    entries.append(entry)
    save_log(entries)


def print_log_summary() -> None:
    """
    Print a summary of all logged API calls.
    Useful for understanding usage and cost at a glance.
    """
    entries = load_log()

    if not entries:
        print("No API calls logged yet.")
        return

    total      = len(entries)
    successful = sum(1 for e in entries if e["status"] == "success")
    failed     = sum(1 for e in entries if e["status"] == "failed")
    avg_ms     = sum(e["duration_ms"] for e in entries) / total

    print(f"\n{'='*50}")
    print(f"  API CALL LOG SUMMARY")
    print(f"{'='*50}")
    print(f"  Total calls:    {total}")
    print(f"  Successful:     {successful}")
    print(f"  Failed:         {failed}")
    print(f"  Avg duration:   {avg_ms:.0f}ms")
    print(f"{'='*50}")

    # Show the last 3 entries
    print(f"\n  LAST 3 CALLS:")
    for entry in entries[-3:]:
        print(f"\n  [{entry['timestamp']}]")
        print(f"  Model:    {entry['model']}")
        print(f"  Status:   {entry['status']}")
        print(f"  Duration: {entry['duration_ms']}ms")
        print(f"  Prompt:   {entry['prompt'][:60]}...")