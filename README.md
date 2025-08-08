# Misskey RSS Bot

A Python bot that monitors RSS feeds and automatically posts new articles to your **Misskey** server.

## Features
- Monitors multiple RSS/Atom feeds in real-time
- Prevents duplicate posts using an SQLite database
- Limits post length to avoid truncation
- Automatically formats and cleans HTML content
- Handles Misskey API rate limits gracefully

## Requirements
- Python 3.8+
- Dependencies listed in `requirements.txt`

Install dependencies with:
```bash
pip install -r requirements.txt
````

## Configuration

Edit the `bot.py` file to set your Misskey instance URL and API token:

```python
MISSKEY_INSTANCE = "https://your.misskey.domain"
MISSKEY_TOKEN = "YOUR_API_TOKEN"
```

Modify the list of RSS feeds in the `FEEDS` array to add or remove sources:

```python
FEEDS = [
    "https://hnrss.org/frontpage",
    "https://www.theverge.com/rss/index.xml",
    # Add your preferred feeds here
]
```

##  How to Run

Run the bot with:

```bash
python bot.py
```

The bot will:

1. Fetch all configured RSS feeds
2. Detect new articles not previously posted
3. Post new articles to your Misskey instance
4. Wait for the configured interval before repeating

## Running Continuously

To keep the bot running 24/7 on a Linux server, create a `systemd` service:

### Create the service file:

```bash
sudo nano /etc/systemd/system/misskeyrssbot.service
```

### Paste the following content (update paths and username):

```ini
[Unit]
Description=Misskey RSS Bot
After=network.target

[Service]
User=YOUR_USERNAME
WorkingDirectory=/path/to/misskey-rss-bot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Enable and start the service:

```bash
sudo systemctl enable misskeyrssbot
sudo systemctl start misskeyrssbot
```

### Check status:

```bash
sudo systemctl status misskeyrssbot
```

## Project Structure

```
misskey-rss-bot/
├── bot.py              # Main bot script
├── requirements.txt    # Python dependencies
└── README.md           # This documentation
```

## License

MIT License (or replace with your preferred license).

---

## Configuration Parameters (in `bot.py`)

| Variable           | Description                                  | Default Value                                                         |
| ------------------ | -------------------------------------------- | --------------------------------------------------------------------- |
| `MISSKEY_INSTANCE` | URL of your Misskey server                   | e.g. [https://misskey.yourdomain.com](https://misskey.yourdomain.com) |
| `MISSKEY_TOKEN`    | Your Misskey API token                       | Your token string                                                     |
| `FEEDS`            | List of RSS feed URLs to monitor             | See default list                                                      |
| `CHECK_INTERVAL`   | Seconds between feed checks                  | 300 (5 minutes)                                                       |
| `POST_DELAY`       | Seconds delay between posting each article   | 5                                                                     |
| `COOLDOWN_DELAY`   | Seconds to wait after hitting API rate limit | 60                                                                    |
| `MAX_POST_LENGTH`  | Maximum characters allowed in a post         | 3000                                                                  |

---

If you encounter issues or want to contribute, feel free to open an issue or pull request.

Happy posting, or feeding, idk!