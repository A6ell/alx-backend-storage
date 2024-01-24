# web.py
import requests
import redis
from functools import wraps

# Initialize Redis connection
redis_client = redis.Redis()


def track_access_count(func):
    """
    Decorator to track the access count for a URL.
    """
    @wraps(func)
    def wrapper(url, *args, **kwargs):
        # Increment access count for the URL
        count_key = f"count:{url}"
        redis_client.incr(count_key)

        # Call the original function
        result = func(url, *args, **kwargs)

        return result

    return wrapper


def cache_result(expiration=10):
    """
    Decorator to cache the result of a function with expiration time.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(url, *args, **kwargs):
            # Generate a cache key based on the function name and URL
            cache_key = f"{func.__name__}:{url}"

            # Check if the result is already in the cache
            cached_result = redis_client.get(cache_key)
            if cached_result is not None:
                return cached_result.decode('utf-8')

            # Call the original function if not in the cache
            result = func(url, *args, **kwargs)

            # Cache the result with expiration time
            redis_client.setex(cache_key, expiration, result)

            return result

        return wrapper

    return decorator


@track_access_count
@cache_result(expiration=10)
def get_page(url: str) -> str:
    """
    Get the HTML content of a URL.
    """
    response = requests.get(url)
    return response.text


if __name__ == "__main__":
    # Example usage
    slow_url = "http://slowwly.robertomurray.co.uk/delay/10000/url/http://www.example.com"
    fast_url = "http://www.example.com"

    # Access slow URL multiple times (simulating different users accessing the same slow URL)
    for _ in range(3):
        content = get_page(slow_url)
        print(f"Content for slow URL: {content}")

    # Access fast URL
    content = get_page(fast_url)
    print(f"Content for fast URL: {content}")

    # Check access count for both URLs
    slow_url_count = redis_client.get(f"count:{slow_url}")
    fast_url_count = redis_client.get(f"count:{fast_url}")

    print(f"Access count for slow URL: {slow_url_count.decode('utf-8')}")
    print(f"Access count for fast URL: {fast_url_count.decode('utf-8')}")

