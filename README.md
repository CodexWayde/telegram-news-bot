# The Global Nexus: Telegram News Bot

> A Telegram bot that gathers news from several sources and posts it automatically four times a day.

Built with **Python · Telegram Bot API · NewsAPI · NewsData.io · Railway**

---

## What it does

- Collects news from several sources (NewsAPI and NewsData.io)
- Posts automatically on a fixed schedule, four times a day
- Works in Telegram group chats
- Handles errors so one failed fetch doesn't stop the bot
- Deployed on Railway

## Posting schedule

Times are Nigerian time (WAT):

| Post | Time |
|---|---|
| Morning | 7:00 AM |
| Afternoon | 1:00 PM |
| Evening | 7:00 PM |
| Night | 11:00 PM |

## Tech stack

| Layer | Tool |
|---|---|
| Language | Python |
| Bot platform | Telegram Bot API |
| News sources | NewsAPI, NewsData.io |
| Hosting | Railway |
| Configuration | Environment variables |

---

## Setup

### Prerequisites

- Python 3.9 or newer
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- API keys from [NewsAPI](https://newsapi.org) and [NewsData.io](https://newsdata.io)

### 1. Clone and install

```bash
git clone https://github.com/CodexWayde/<repo-name>.git
cd <repo-name>
pip install -r requirements.txt
```

### 2. Set environment variables

Never put keys directly in the code. Set them as environment variables:

| Variable | What it is |
|---|---|
| `BOT_TOKEN` | Bot token from @BotFather |
| `CHAT_ID` | The Telegram chat or channel to post to |
| `NEWSAPI_KEY` | Your NewsAPI key |
| `NEWSDATA_KEY` | Your NewsData.io key |

### 3. Run locally

```bash
python main.py
```

### 4. Deploy on Railway

1. Push the project to GitHub
2. Create a new Railway project from the repo
3. Add the environment variables above in Railway's settings
4. Deploy

---

## Author

**Isaac Desmond** · AI Automation & Full-Stack Developer in training

- Portfolio: [codexwayde.github.io/portfolio](https://codexwayde.github.io/portfolio)
- GitHub: [@CodexWayde](https://github.com/CodexWayde)
- LinkedIn: [isaac-desmond](https://www.linkedin.com/in/isaac-desmond-b23a213a7)
