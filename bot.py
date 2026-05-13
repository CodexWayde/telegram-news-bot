import os
import logging
import requests
import pytz
from datetime import datetime

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ["BOT_TOKEN"]
NEWS_API_KEY = os.environ["NEWS_API_KEY"]
NEWS_API_URL = "https://newsapi.org/v2"

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ── NewsAPI helpers ───────────────────────────────────────────────────────────

def fetch_top_headlines(page_size: int = 7) -> list[dict]:
    resp = requests.get(
        f"{NEWS_API_URL}/top-headlines",
        params={"language": "en", "pageSize": page_size, "apiKey": NEWS_API_KEY},
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


def format_articles(articles: list[dict]) -> list[dict]:
    if not articles:
        return []
    results = []
    for a in articles:
        title = a.get("title") or "No title"
        url = a.get("url") or ""
        source = (a.get("source") or {}).get("name", "Unknown")
        description = a.get("description") or ""
        image = a.get("urlToImage") or ""
        results.append({
            "title": title,
            "url": url,
            "source": source,
            "description": description,
            "image": image,
        })
    return results


# ── Handlers ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 *Welcome to NewsBot!*\n\n"
        "Commands:\n"
        "/news — top headlines right now\n"
        "/search <keyword> — search by topic\n"
        "/postnews — post news to the group\n\n"
        "📅 News is also posted automatically at 7AM, 12PM, 6PM and 10PM (WAT).",
        parse_mode="Markdown",
    )


async def cmd_news(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("⏳ Fetching top headlines…")
    try:
        articles = fetch_top_headlines()
        formatted = format_articles(articles)
        if not formatted:
            await update.message.reply_text("😕 No articles found.")
            return
        for a in formatted:
            caption = (
                f"📰 *{a['title']}*\n"
                f"_{a['description']}_\n\n"
                f"🗞 {a['source']}  |  🔗 [Read more]({a['url']})"
            )
            if a["image"]:
                await update.message.reply_photo(
                    photo=a["image"],
                    caption=caption,
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(caption, parse_mode="Markdown", disable_web_page_preview=False)
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
        formatted = format_articles(articles)
        if not formatted:
            await update.message.reply_text("😕 No articles found.")
            return
        for a in formatted:
            caption = (
                f"📰 *{a['title']}*\n"
                f"_{a['description']}_\n\n"
                f"🗞 {a['source']}  |  🔗 [Read more]({a['url']})"
            )
            if a["image"]:
                await update.message.reply_photo(
                    photo=a["image"],
                    caption=caption,
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(caption, parse_mode="Markdown", disable_web_page_preview=False)
    except Exception as e:
        logger.error(f"Search error: {e}")
        await update.message.reply_text("❌ Search failed. Try again later.")


async def cmd_postnews(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    CHAT_ID = os.environ["CHAT_ID"]
    await update.message.reply_text("📤 Posting news to the group…")
    try:
        articles = fetch_top_headlines()
        formatted = format_articles(articles)
        if not formatted:
            await update.message.reply_text("😕 No articles found.")
            return
        for a in formatted:
            caption = (
                f"📰 *{a['title']}*\n"
                f"_{a['description']}_\n\n"
                f"🗞 {a['source']}  |  🔗 [Read more]({a['url']})"
            )
            try:
                if a["image"]:
                    await ctx.bot.send_photo(
                        chat_id=CHAT_ID,
                        photo=a["image"],
                        caption=caption,
                        parse_mode="Markdown",
                    )
                else:
                    await ctx.bot.send_message(
                        chat_id=CHAT_ID,
                        text=caption,
                        parse_mode="Markdown",
                        disable_web_page_preview=False,
                    )
            except Exception as e:
                logger.error(f"Error sending article: {e}")
                continue
        await update.message.reply_text("✅ News posted to the group successfully!")
    except Exception as e:
        logger.error(f"Error posting news: {e}")
        await update.message.reply_text("❌ Failed to post news. Try again later.")


async def scheduled_news(bot) -> None:
    CHAT_ID = os.environ["CHAT_ID"]
    try:
        articles = fetch_top_headlines()
        formatted = format_articles(articles)
        if not formatted:
            return
        await bot.send_message(chat_id=CHAT_ID, text="🗞 *News Update!*", parse_mode="Markdown")
        for a in formatted:
            caption = (
                f"📰 *{a['title']}*\n"
                f"_{a['description']}_\n\n"
                f"🗞 {a['source']}  |  🔗 [Read more]({a['url']})"
            )
            if a["image"]:
                await bot.send_photo(
                    chat_id=CHAT_ID,
                    photo=a["image"],
                    caption=caption,
                    parse_mode="Markdown",
                )
            else:
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=caption,
                    parse_mode="Markdown",
                    disable_web_page_preview=False,
                )
    except Exception as e:
        logger.error(f"Scheduled news error: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("news", cmd_news))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("postnews", cmd_postnews))

    # Scheduler
    tz = pytz.timezone("Africa/Lagos")
    scheduler = AsyncIOScheduler(timezone=tz)
    scheduler.add_job(scheduled_news, "cron", hour=7, minute=0, args=[app.bot])
    scheduler.add_job(scheduled_news, "cron", hour=12, minute=0, args=[app.bot])
    scheduler.add_job(scheduled_news, "cron", hour=18, minute=0, args=[app.bot])
    scheduler.add_job(scheduled_news, "cron", hour=22, minute=0, args=[app.bot])
    scheduler.start()

    logger.info("Bot is running with scheduler…")
    app.run_polling()


if __name__ == "__main__":
    main()