import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ─────────────────────────────────────────────────────
# STEP 1 — Fetch a joke about a specific topic
# JokeAPI supports category search — we use the
# /joke/Any endpoint with a "contains" search parameter
# ─────────────────────────────────────────────────────
def fetch_joke(topic: str) -> str:
    response = requests.get(
        "https://v2.jokeapi.dev/joke/Any",
        params={
            "contains": topic,  # Search jokes that contain this word
            "type": "single",   # Single-line joke, not setup/punchline format
        }
    )

    response.raise_for_status()
    data = response.json()

    # JokeAPI returns an "error" field set to True if no joke found for topic
    # This is different from an HTTP error - the request succeded (200)
    # but the result is logically empty. Always check API-specific error fields.
    if data.get("error"):
        # Fall back to a programming joke if topic search fails
        print(f"No joke found for '{topic}' - fetching a programming joke instead.")
        fallback = requests.get(
            "https://v2.jokeapi.dev/joke/Programming",
            params={"type": "single"}
        )
        fallback.raise_for_status()
        return fallback.json()["joke"]
    
    return data["joke"]


# ─────────────────────────────────────────────────────
# STEP 2 — Send the joke to an LLM to expand it
# The joke becomes part of the prompt — same chaining
# pattern as before but with a specific creative task
# ─────────────────────────────────────────────────────
def expand_joke(joke: str, topic:str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # The system prompt defines the persona for this specific task
    # A comedy writer has different instincts than a default assistant
    system_prompt = (
        "You are a professional comedy writer. "
        "Your job is to take a short joke and expand it into something "
        "funnier, more detailed, and more surprising - while keeping "
        "the original punchline intact. Add setup, build tension, "
        "add a callback if you can. Keep it under 150 words."
    )

    # The joke is injected into the user message as context
    # topic is included so the LLM cal lean into domain-specific humor
    user_message = (
        f"Here is a joke about {topic}:\n\n"
        f"{joke}\n\n"
        f"Expand this into a funnier, more elaborate version."
    )

    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 250,
        # temperature controls randomness - 0.0 is deterministic, 2.0 is chaotic
        # 0.9 gives creative variety while staying coherent
        # you read about this in the OpenAI docs today
        "temperature": 0.9
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=body
    )

    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


# ─────────────────────────────────────────────────────
# PIPELINE — Wire the two calls together
# ─────────────────────────────────────────────────────
def run_joke_expander(topic: str) -> None:
    print(f"\n{'='*55}")
    print(f" JOKE EXPANDER / Topic: {topic}")
    print(f"{'='*55}")

    # Call 1 - fetch a joke
    print("\nFetching joke...\n")
    original_joke = fetch_joke(topic)

    print(f"ORIGINAL_JOKE:\n{original_joke}")

    # Call 2 - original_joke flows into expand_joke as context
    print("\nExpanding joke with AI...\n")
    expanded = expand_joke(original_joke, topic)

    print(f"EXPANDED VERSION:\n{expanded}")
    print(f"\n{'='*55}\n")


# ─────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    topic = input("Enter a topic to find and expand a joke about: ")
    run_joke_expander(topic)