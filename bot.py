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
CHAT_ID = os.environ["CHAT_ID"]
GNEWS_API_KEY = "db4858b5de9bfdfa000f06505d34df10"
GNEWS_API_URL = "https://gnews.io/api/v4"

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Greeting helper ───────────────────────────────────────────────────────────

def get_greeting() -> str:
    hour = datetime.now(pytz.utc).hour
    if 5 <= hour < 12:
        return "🌅 Good Morning"
    elif 12 <= hour < 17:
        return "☀️ Good Afternoon"
    elif 17 <= hour < 21:
        return "🌆 Good Evening"
    else:
        return "🌙 Good Night"


# ── GNews helpers ─────────────────────────────────────────────────────────────

def fetch_top_headlines(page_size: int = 4) -> list[dict]:
    resp = requests.get(
        f"{GNEWS_API_URL}/top-headlines",
        params={
            "language": "en",
            "max": page_size,
            "apikey": GNEWS_API_KEY,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("articles", [])


def fetch_tech_news(page_size: int = 4) -> list[dict]:
    resp = requests.get(
        f"{GNEWS_API_URL}/search",
        params={
            "q": "technology OR artificial intelligence OR startups OR crypto OR gadgets",
            "max": page_size,
            "language": "en",
            "sortby": "publishedAt",
            "apikey": GNEWS_API_KEY,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("articles", [])


def fetch_search(query: str, page_size: int = 5) -> list[dict]:
    resp = requests.get(
        f"{GNEWS_API_URL}/search",
        params={
            "q": query,
            "max": page_size,
            "language": "en",
            "sortby": "publishedAt",
            "apikey": GNEWS_API_KEY,
        },
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
        image = a.get("image") or a.get("urlToImage") or ""
        results.append({
            "title": title,
            "url": url,
            "source": source,
            "description": description,
            "image": image,
        })
    return results


async def send_articles(bot, chat_id, articles: list[dict]) -> None:
    for a in articles:
        caption = (
            f"📰 *{a['title']}*\n"
            f"_{a['description']}_\n\n"
            f"🗞 {a['source']}  |  🔗 [Read more]({a['url']})\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📡 *THE GLOBAL NEXUS* — Your World. Your Tech."
        )
        try:
            if a["image"]:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=a["image"],
                    caption=caption,
                    parse_mode="Markdown",
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    parse_mode="Markdown",
                    disable_web_page_preview=False,
                )
        except Exception as e:
            logger.error(f"Error sending article: {e}")
            continue


# ── Handlers ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 *Welcome to THE GLOBAL NEXUS Bot!*\n\n"
        "Your #1 source for global news and tech updates. 🌍💻\n\n"
        "*Commands:*\n"
        "/news — top global headlines\n"
        "/tech — latest tech news\n"
        "/search <keyword> — search any topic\n"
        "/postnews — post news to the group\n\n"
        "📅 News drops automatically at 6AM, 12PM, 6PM & 10PM (UTC).",
        parse_mode="Markdown",
    )


async def cmd_news(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("⏳ Fetching top global headlines…")
    try:
        articles = format_articles(fetch_top_headlines())
        if not articles:
            await update.message.reply_text("😕 No articles found.")
            return
        await send_articles(ctx.bot, update.effective_chat.id, articles)
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        await update.message.reply_text("❌ Failed to fetch news. Try again later.")


async def cmd_tech(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("💻 Fetching latest tech news…")
    try:
        articles = format_articles(fetch_tech_news())
        if not articles:
            await update.message.reply_text("😕 No tech articles found.")
            return
        await send_articles(ctx.bot, update.effective_chat.id, articles)
    except Exception as e:
        logger.error(f"Error fetching tech news: {e}")
        await update.message.reply_text("❌ Failed to fetch tech news. Try again later.")


async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not ctx.args:
        await update.message.reply_text("Usage: /search <keyword>  e.g. /search AI")
        return
    query = " ".join(ctx.args)
    await update.message.reply_text(f"🔍 Searching for *{query}*…", parse_mode="Markdown")
    try:
        articles = format_articles(fetch_search(query))
        if not articles:
            await update.message.reply_text("😕 No articles found.")
            return
        await send_articles(ctx.bot, update.effective_chat.id, articles)
    except Exception as e:
        logger.error(f"Search error: {e}")
        await update.message.reply_text("❌ Search failed. Try again later.")


async def cmd_postnews(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("📤 Posting news to The Global Nexus…")
    try:
        global_articles = format_articles(fetch_top_headlines(4))
        tech_articles = format_articles(fetch_tech_news(4))
        greeting = get_greeting()
        await ctx.bot.send_message(
            chat_id=CHAT_ID,
            text=(
                f"{greeting}, Nexus Fam! 🌍\n\n"
                f"Here's your news update from *THE GLOBAL NEXUS* 📡\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🌐 *Global News* + 💻 *Tech Updates*"
            ),
            parse_mode="Markdown",
        )
        await send_articles(ctx.bot, CHAT_ID, global_articles + tech_articles)
        await update.message.reply_text("✅ News posted to The Global Nexus successfully!")
    except Exception as e:
        logger.error(f"Error posting news: {e}")
        await update.message.reply_text("❌ Failed to post news. Try again later.")


async def scheduled_news(bot) -> None:
    try:
        global_articles = format_articles(fetch_top_headlines(2))
        tech_articles = format_articles(fetch_tech_news(2))
        greeting = get_greeting()
        await bot.send_message(
            chat_id=CHAT_ID,
            text=(
                f"{greeting}, Nexus Fam! 🌍\n\n"
                f"Here's your news update from *THE GLOBAL NEXUS* 📡\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🌐 *Global News* + 💻 *Tech Updates*"
            ),
            parse_mode="Markdown",
        )
        await send_articles(bot, CHAT_ID, global_articles + tech_articles)
        logger.info("Scheduled news posted successfully!")
    except Exception as e:
        logger.error(f"Scheduled news error: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("news", cmd_news))
    app.add_handler(CommandHandler("tech", cmd_tech))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("postnews", cmd_postnews))

    # Scheduler — UTC time (works globally)
    scheduler = AsyncIOScheduler(timezone=pytz.utc)
    scheduler.add_job(scheduled_news, "cron", hour=6, minute=0, args=[app.bot])
    scheduler.add_job(scheduled_news, "cron", hour=12, minute=0, args=[app.bot])
    scheduler.add_job(scheduled_news, "cron", hour=18, minute=0, args=[app.bot])
    scheduler.add_job(scheduled_news, "cron", hour=22, minute=0, args=[app.bot])
    scheduler.start()

    logger.info("Bot is running with scheduler…")
    app.run_polling()


if __name__ == "__main__":
    main()