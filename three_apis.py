# Updated on feature branch - testing Git workflow
import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ─────────────────────────────────────────────────────
# API 1 — Joke API
# GET request, no auth, simplest possible call
# ─────────────────────────────────────────────────────
def get_joke() -> str:
    # requests.get() sends a GET request to the URL
    # params= is how you pass query parameters in requests
    # instead of manually building ?type=single into the URL
    response = requests.get(
        "https://v2.jokeapi.dev/joke/Programming",
        params={"type": "single"}
    )

    # .raise_for_status() throws an error if status code is 4xx or 5xx
    # Without this, a failed request looks like success until you try to use the data
    response.raise_for_status()

    # .json() parses the response body from a JSON string into a Python dictionary
    data = response.json()

    # Navigate the nested dictionary to get the joke text
    return data["joke"]


# ─────────────────────────────────────────────────────
# API 2 — Weather API
# GET request, no auth, query parameters
# ─────────────────────────────────────────────────────
def get_weather(city: str = "Barcelona") -> str:
    # Barcelona coordinates — hardcoded for now
    # Later you could add a geocoding API call to make city dynamic
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": 41.3874,
            "longitude": 2.1686,
            "current": "temperature_2m,wind_speed_10m"
        }
    )

    response.raise_for_status()
    data = response.json()

    # Navigate the nested structure you saw in Postman
    temp = data["current"]["temperature_2m"]
    wind = data["current"]["wind_speed_10m"]

    # Return a clean formatted string — not raw data
    return f"{temp}°C with wind speed {wind} km/h in {city}"


# ─────────────────────────────────────────────────────
# API 3 — OpenAI API
# POST request, authentication header, request body
# ─────────────────────────────────────────────────────
def get_ai_response(prompt: str) -> str:
    # headers= is how you pass HTTP headers in requests
    # This is where authentication lives for most APIs
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # json= is how you pass the request body as JSON in requests
    # requests automatically sets Content-Type to application/json when you use json=
    # (but we're setting it manually in headers to be explicit and learn the pattern)
    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 150
    }

    # requests.post() for POST requests — notice json=body not params=
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=body
    )

    response.raise_for_status()
    data = response.json()

    # The path you found in Postman: choices[0].message.content
    return data["choices"][0]["message"]["content"]


# ─────────────────────────────────────────────────────
# COMBINE — Use all three outputs together
# This is where the results become a pipeline
# ─────────────────────────────────────────────────────
def run_combined_pipeline() -> None:
    print("\nFetching data from 3 APIs...\n")

    # Call all three independently
    joke    = get_joke()
    weather = get_weather()

    # Use joke and weather as CONTEXT for the AI call
    # This is the same chaining pattern from Friday's task
    # but now across three different external services
    prompt = (
        f"The current weather in Barcelona is: {weather}.\n"
        f"Here is a programming joke: {joke}\n\n"
        f"Write a single fun sentence that combines the weather "
        f"and the joke into one coherent thought."
    )

    ai_response = get_ai_response(prompt)

    # Print each piece clearly
    print(f"JOKE:\n{joke}\n")
    print(f"WEATHER:\n{weather}\n")
    print(f"AI COMBINED RESPONSE:\n{ai_response}\n")


# ─────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    run_combined_pipeline()