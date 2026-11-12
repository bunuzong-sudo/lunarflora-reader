#!/usr/bin/env python3
"""Read today's top plant posts. Personal, non-commercial, read-only."""

import json
import os
import sys
import time

import requests

USER_AGENT = "lunarflora-reader/0.1 by u/Ok_Western9786"
SUBREDDITS = (
    "botany",
    "SavageGarden",
    "orchids",
    "whatsthisplant",
    "succulents",
    "rareplants",
)
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API_ROOT = "https://oauth.reddit.com"
MIN_INTERVAL = 1.0
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".gif", ".webp")


def require_env(name):
    value = os.environ.get(name, "").strip()
    if not value:
        print(f"missing environment variable {name}", file=sys.stderr)
        sys.exit(1)
    return value


def pace(response):
    """Wait at least one second, longer when Reddit's budget is spent."""
    wait = MIN_INTERVAL
    remaining = response.headers.get("X-Ratelimit-Remaining")
    reset = response.headers.get("X-Ratelimit-Reset")
    try:
        if remaining is not None and float(remaining) < 1 and reset is not None:
            wait = max(wait, float(reset))
    except ValueError:
        pass
    if wait > 0:
        time.sleep(wait)


def image_url(post):
    url = post.get("url") or ""
    path = url.lower().split("?", 1)[0]
    if path.endswith(IMAGE_SUFFIXES) or "i.redd.it/" in path or "i.imgur.com/" in path:
        return url

    preview = (post.get("preview") or {}).get("images") or []
    if preview:
        source = (preview[0].get("source") or {}).get("url")
        if source:
            return source

    items = (post.get("gallery_data") or {}).get("items") or []
    meta = post.get("media_metadata") or {}
    if items:
        media = meta.get(items[0].get("media_id"), {})
        source = (media.get("s") or {}).get("u")
        if source:
            return source

    thumbnail = post.get("thumbnail") or ""
    if thumbnail.startswith("http"):
        return thumbnail
    return None


def fetch_token(session):
    response = session.post(
        TOKEN_URL,
        auth=(require_env("REDDIT_CLIENT_ID"), require_env("REDDIT_CLIENT_SECRET")),
        data={
            "grant_type": "password",
            "username": require_env("REDDIT_USERNAME"),
            "password": require_env("REDDIT_PASSWORD"),
        },
        timeout=30,
    )
    response.raise_for_status()
    token = response.json().get("access_token")
    if not token:
        print("reddit did not return an access token", file=sys.stderr)
        sys.exit(1)
    return token, response


def main():
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    token, token_response = fetch_token(session)
    session.headers["Authorization"] = f"bearer {token}"
    previous = token_response

    for name in SUBREDDITS:
        pace(previous)
        response = session.get(
            f"{API_ROOT}/r/{name}/top",
            params={"t": "day", "limit": 25, "raw_json": 1},
            timeout=30,
        )
        response.raise_for_status()
        previous = response

        children = (response.json().get("data") or {}).get("children") or []
        for child in children:
            post = child.get("data") or {}
            permalink = post.get("permalink") or ""
            print(
                json.dumps(
                    {
                        "title": post.get("title"),
                        "subreddit": post.get("subreddit"),
                        "score": post.get("score"),
                        "permalink": f"https://www.reddit.com{permalink}" if permalink else None,
                        "image_url": image_url(post),
                    },
                    ensure_ascii=False,
                )
            )


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as exc:
        detail = exc.response.text[:300] if exc.response is not None else str(exc)
        print(f"reddit request failed: {detail}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as exc:
        print(f"reddit request failed: {exc}", file=sys.stderr)
        sys.exit(1)
