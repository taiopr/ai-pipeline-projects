import time
import requests


# ─────────────────────────────────────────────────────
# RETRY WITH EXPONENTIAL BACKOFF
#
# Wraps any function that makes an API call.
# If it fails with a retryable error, waits and tries again.
# Gives up after max_retries attempts.
# ─────────────────────────────────────────────────────
def call_with_retry(func, *args, max_retries=4, base_wait=1.0, **kwargs):
    """
    Call a function with automatic retry on failure.
    func        — the function to call
    *args       — positional arguments to pass to func
    max_retries — maximum number of retry attempts
    base_wait   — starting wait time in seconds (doubles each retry)
    **kwargs    — keyword arguments to pass to func
    """

    # Status codes worth retrying — server issues and rate limits
    # 400, 401, 404 are NOT here — those need code fixes, not retries
    RETRYABLE_CODES = {429, 500, 502, 503, 504}

    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            # Call the function with whatever arguments were passed
            result = func(*args, **kwargs)
            return result # Success - return immediatly
        
        except requests.exceptions.HTTPError as e:
            last_exception = e
            status_code = e.response.status_code

            # If it's not a retryable code, fail immediatly
            # Retrying a 401 or 404 will never succeed
            if status_code not in RETRYABLE_CODES:
                print(f"Non-retryable error {status_code} - failing immediatly.")
                raise
            # Calculate wait time - doubles each attempt
            # attempt 1: 1s, attempt 2: 2s, attempt 3: 4s, attempt 4: 8s
            wait_time = base_wait * (2 ** (attempt - 1))

            if attempt < max_retries:
                print(f"Attempt {attempt} failed with {status_code}. "
                      f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                print(f"All {max_retries} attempts failed.")

        except requests.exceptions.ConnectionError as e:
            # Network error - no internet, DNS failure, etc.
            last_exception = e
            wait_time = base_wait * (2 **(attempt - 1))

            if attempt < max_retries:
                print(f"Connection error on attempt {attempt}. "
                      f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                print(f"All {max_retries} attempts failed with connection error.")

        except requests.exceptions.Timeout as e:
            # Request took tooo long
            last_exception = e
            wait_time = base_wait * (2 ** (attempt - 1))

            if attempt < max_retries:
                print(f"Timeout on attempt {attempt}. "
                      f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                print(f"All {max_retries} attempts failed with timeout.")

    # If we get here, all retries were exhausted
    raise last_exception