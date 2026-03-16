# Sends test payloads to an n8n webhook
# Run this while n8n is listening to test your workflow
 
import os
import json
import requests
from dotenv import load_dotenv
 
load_dotenv()
 
# ─── CONFIGURATION ──────────────────────────────────────────────
# Paste your n8n webhook TEST URL here
# Get it from the Webhook node settings in n8n
WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
 
# If not in .env, set it directly for testing:
# WEBHOOK_URL = "https://yourname.app.n8n.cloud/webhook-test/abc123"
 
 
# ─── SINGLE REQUEST ─────────────────────────────────────────────
def trigger_webhook(payload: dict) -> dict:
    """
    Send a POST request to the n8n webhook.
    payload: the JSON data to send — becomes $json in n8n
    Returns the response from n8n.
    """
    if not WEBHOOK_URL:
        print("Error: WEBHOOK_URL not set. Add N8N_WEBHOOK_URL to your .env file")
        return {}
 
    print(f"\nSending to webhook: {WEBHOOK_URL[:50]}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
 
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,              # sends as JSON body
            headers={
                "Content-Type": "application/json"
            },
            timeout=30                 # wait up to 30 seconds for n8n to respond
        )
 
        print(f"\nHTTP Status: {response.status_code}")
 
        # n8n with "Respond: Immediately" returns 200 with a simple body
        # Try to parse as JSON, fall back to text
        try:
            result = response.json()
            print(f"n8n response: {json.dumps(result, indent=2)}")
        except Exception:
            print(f"n8n response: {response.text}")
 
        response.raise_for_status()
        return response.json() if response.content else {}
 
    except requests.exceptions.ConnectionError:
        print("Connection error — is n8n running and listening?")
        return {}
    except requests.exceptions.Timeout:
        print("Timeout — n8n took too long to respond")
        return {}
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
        return {}
 
 
# ─── TEST PAYLOADS ──────────────────────────────────────────────
TEST_PAYLOADS = [
    {
        "topic":     "machine learning",
        "category":  "technology",
        "source":    "webhook_trigger.py",
        "test_id":   1
    },
    {
        "topic":     "Barcelona",
        "category":  "travel",
        "source":    "webhook_trigger.py",
        "test_id":   2
    },
    {
        "topic":     "REST APIs",
        "category":  "technology",
        "source":    "webhook_trigger.py",
        "test_id":   3
    },
]
 
 
# ─── ENTRY POINT ────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
 
    # Run a single test or all tests based on argument
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        # python webhook_trigger.py all
        print(f"Running all {len(TEST_PAYLOADS)} test payloads...")
        print("Remember: click Listen for test event in n8n before each!")
        for i, payload in enumerate(TEST_PAYLOADS, start=1):
            print(f"\n--- Test {i}/{len(TEST_PAYLOADS)} ---")
            trigger_webhook(payload)
            if i < len(TEST_PAYLOADS):
                input("\nPress Enter to send next payload...")
    else:
        # python webhook_trigger.py
        # Sends just the first test payload
        trigger_webhook(TEST_PAYLOADS[0])