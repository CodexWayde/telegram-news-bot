import os
import logging
import requests
from datetime import datetime

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ["BOT_TOKEN"]
NEWS_API_KEY = os.environ["NEWS_API_KEY"]
NEWS_API_URL = "https://newsapi.org/v2"

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ── NewsAPI helpers ───────────────────────────────────────────────────────────

def fetch_top_headlines(page_size: int = 5) -> list[dict]:
    resp = requests.get(
        f"{NEWS_API_URL}/top-headlines",
        params={"country": "us", "pageSize": page_size, "apiKey": NEWS_API_KEY},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("articles", [])


def fetch_search(query: str, page_size: int = 5) -> list[dict]:
    resp = requests.get(
        f"{NEWS_API_URL}/everything",
        params={"q": query, "pageSize": page_size, "sortBy": "publishedAt", "apiKey": NEWS_API_KEY},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("articles", [])


def format_articles(articles: list[dict]) -> str:
    if not articles:
        return "😕 No articles found."
    lines = []
    for i, a in enumerate(articles, 1):
        title = a.get("title") or "No title"
        url = a.get("url") or ""
        source = (a.get("source") or {}).get("name", "Unknown")
        lines.append(f"{i}. *{title}*\n   📰 {source}\n   🔗 {url}")
    return "\n\n".join(lines)


# ── Handlers ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 *Welcome to NewsBot!*\n\n"
        "Commands:\n"
        "/news — top headlines right now\n"
        "/search <keyword> — search by topic",
        parse_mode="Markdown",
    )


async def cmd_news(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("⏳ Fetching top headlines…")
    try:
        articles = fetch_top_headlines()
        text = (
            f"📰 *Top Headlines* — {datetime.utcnow().strftime('%b %d, %H:%M UTC')}\n\n"
            + format_articles(articles)
        )
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        await update.message.reply_text("❌ Failed to fetch news. Try again later.")


async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not ctx.args:
        await update.message.reply_text("Usage: /search <keyword>  e.g. /search AI")
        return
    query = " ".join(ctx.args)
    await update.message.reply_text(f"🔍 Searching for *{query}*…", parse_mode="Markdown")
    try:
        articles = fetch_search(query)
        text = f"🔍 *Results for '{query}'*\n\n" + format_articles(articles)
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Search error: {e}")
        await update.message.reply_text("❌ Search failed. Try again later.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("news", cmd_news))
    app.add_handler(CommandHandler("search", cmd_search))
    logger.info("Bot is running…")
    app.run_polling()


if __name__ == "__main__":
    main()