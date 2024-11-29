import os
import time
import asyncio

import httpx

from function.utils import logger

GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


async def fetch_from_github(url, session):
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    response = None
    try:
        response = await session.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if response.status_code == 403:
            reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
            sleep_time = max(0, reset_time - int(time.time()))
            logger.info(f"Rate limit exceeded. Sleeping for {sleep_time} seconds.")
            await asyncio.sleep(sleep_time)
            return await fetch_from_github(url, session)
        logger.error(f"HTTP status error {e.response.status_code} while fetching from {url}: {e}")
    except httpx.RequestError as e:
        logger.error(f"HTTP request error while fetching from {url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while fetching from {url}: {e}")
    return
