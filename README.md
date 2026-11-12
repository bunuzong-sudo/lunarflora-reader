# lunarflora-reader

Personal, non-commercial script. Once a day it reads the top posts from a few plant subreddits and prints them for the owner's own notes. It only reads: no posting, voting, messaging, or user data collection. A normal run stays under 100 requests.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export REDDIT_CLIENT_ID=...
export REDDIT_CLIENT_SECRET=...
export REDDIT_USERNAME=...
export REDDIT_PASSWORD=...

python3 fetch_plants.py
```

Use a Reddit script app. Each output line is one post as JSON: title, subreddit, score, permalink, and image URL.
