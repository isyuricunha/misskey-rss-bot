# misskey rss bot

a small python bot that watches rss/atom feeds and posts new items to a misskey instance.

it’s simple on purpose: one script, a tiny sqlite db to avoid duplicates, and a couple of knobs you can tune in `bot.py`.

## what it does

- monitors multiple feeds defined in `FEEDS`
- converts html to plain text using `html2text`
- truncates long posts to `MAX_POST_LENGTH`
- skips items already posted (hash stored in sqlite `posted_hashes.db`)
- handles http 429 from misskey with a cooldown and retries

## requirements

- python 3.8+
- packages in `requirements.txt`

install deps:

```bash
pip install -r requirements.txt
```

## configuration (edit `bot.py`)

set your misskey url and api token:

```python
MISSKEY_INSTANCE = "https://your.misskey.domain"
MISSKEY_TOKEN = "your_api_token"
```

define feeds:

```python
FEEDS = [
    "https://hnrss.org/frontpage",
    "https://www.theverge.com/rss/index.xml",
    # add your feeds here
]
```

tune timings and limits if you want:

```python
CHECK_INTERVAL = 300   # seconds between full checks
POST_DELAY = 5         # delay between posts
COOLDOWN_DELAY = 60    # wait after http 429
MAX_POST_LENGTH = 3000 # max characters per post
```

notes:

- the script currently builds posts in `format_post()` with a title, cleaned summary/content, and the link. if you don’t want any decorations, edit that function accordingly.
- keep your api token private. don’t commit your token.

## how to run

```bash
python bot.py
```

the loop is straightforward:

1. parse each feed with `feedparser`
2. compute a sha256 from title+link(+summary)
3. skip if the hash exists in sqlite
4. format text and call `POST /api/notes/create` on misskey
5. wait `POST_DELAY` and continue
6. sleep `CHECK_INTERVAL` and repeat

the sqlite db file is created automatically as `posted_hashes.db` in the project root.

## run it 24/7 (linux)

systemd unit example (adjust paths/users):

```ini
[Unit]
Description=misskey rss bot
After=network.target

[Service]
User=YOUR_USERNAME
WorkingDirectory=/path/to/misskey-rss-bot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

enable + start:

```bash
sudo systemctl enable misskeyrssbot
sudo systemctl start misskeyrssbot
```

## run it on windows

- simplest path: keep a terminal open and run `python bot.py`
- if you want it as a service, use something like nssm to wrap the script, or schedule it via task scheduler (run at startup, keep running on failure)

## project layout

```
misskey-rss-bot/
├── bot.py              # main script
├── requirements.txt    # python deps
└── README.md           # this file
```

## customization

- change post format: edit `format_post()` in `bot.py`
- change dedup logic: edit `hash_entry()` (currently title+link+summary sha256)
- change storage: update `init_db()/has_posted()/mark_posted()` if you want a different db
- timeouts/retries: see `post_to_misskey()` (requests timeout=10, cooldown on 429)

## troubleshooting

- nothing posts
  - check `MISSKEY_INSTANCE` and `MISSKEY_TOKEN`
  - verify your token has permission to create notes
  - try a minimal feed you trust (e.g. `https://hnrss.org/frontpage`)

- rate limit / 429
  - the bot waits `COOLDOWN_DELAY` seconds and tries later. you can raise the delay or lower `POST_DELAY`

- duplicates show up
  - `posted_hashes.db` stores a hash per item. if feeds change titles/summaries after publish, hashes may differ. you can adjust `hash_entry()` to be stricter (e.g., only link) or looser

- formatting looks weird
  - `html2text` strips html and links/images by default. tweak `clean_html()` to include links or adjust width

## security

- don’t commit your real token to git
- if you need env-based config, wire `os.environ.get()` into `bot.py` (the current code reads constants only)

## license

this project is under the mit license. see `LICENSE`.
