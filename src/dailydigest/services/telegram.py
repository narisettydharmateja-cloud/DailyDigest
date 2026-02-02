"""Telegram bot delivery service for sending digests."""

import asyncio
import html as html_lib
import re
from urllib.parse import urlparse
from typing import Optional

import structlog
from telegram import Bot
from telegram.error import TelegramError
from telegram.constants import ParseMode

from ..config import settings
from ..models.db import Digest
from ..services.database import build_engine, create_session_factory, session_scope

logger = structlog.get_logger()


def _strip_html(text: str) -> str:
    text = html_lib.unescape(text or "")
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split())


def _normalize_url(url: str | None) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.scheme:
        return url
    if url.startswith("//"):
        return f"https:{url}"
    return f"https://{url}"


def format_digest_telegram(digest: Digest) -> str:
    """Format digest content for Telegram (Markdown)."""
    content = digest.content_json
    
    # Build message
    message = f"*{digest.persona.replace('_', ' ').title()} Digest*\n"
    message += f"_{digest.generated_at.strftime('%B %d, %Y')}_\n\n"
    
    # Intro
    message += f"{content['intro']}\n\n"
    
    # Clusters
    message += "---\n\n"
    
    for i, section in enumerate(content['sections'], 1):
        message += f"*Topic {i}: {section['theme']}*\n"
        message += f"{section['article_count']} articles, avg score: {section['avg_score']:.2f}\n\n"
        message += f"{section['summary']}\n\n"
        
        message += "*Articles:*\n"
        for article in section['articles']:
            # Escape special characters for Telegram Markdown V2
            title = article['title'].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')
            message += f"• [{title}]({_normalize_url(article.get('url'))})\n"
        
        message += "\n---\n\n"
    
    # Footer
    message += f"*Total:* {content['total_articles']} articles across {content['total_clusters']} topics\n"
    message += f"_Powered by DailyDigest_"
    
    return message


async def send_telegram_message_async(
    chat_id: str,
    message: str,
    bot_token: Optional[str] = None,
) -> None:
    """Send message via Telegram bot (async)."""
    bot_token = bot_token or settings.telegram_bot_token
    
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not configured. Check .env file.")
    
    bot = Bot(token=bot_token)
    
    try:
        # Split message if too long (Telegram limit is 4096 characters)
        max_length = 4000
        if len(message) > max_length:
            # Split by topic separators
            parts = message.split("---")
            current_part = parts[0]
            
            for part in parts[1:]:
                if len(current_part) + len(part) + 3 < max_length:
                    current_part += "---" + part
                else:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=current_part,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True,
                    )
                    current_part = part
            
            # Send last part
            if current_part:
                await bot.send_message(
                    chat_id=chat_id,
                    text=current_part,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
        
        logger.info("telegram_sent", chat_id=chat_id)
    except TelegramError as e:
        logger.error("telegram_send_failed", error=str(e), chat_id=chat_id)
        raise


def send_telegram_message(chat_id: str, message: str, bot_token: Optional[str] = None) -> None:
    """Send message via Telegram bot (sync wrapper)."""
    asyncio.run(send_telegram_message_async(chat_id, message, bot_token))


async def send_digest_telegram_async(digest_id: str, chat_id: str) -> None:
    """Send a digest via Telegram as separate messages for each article."""
    engine = build_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    
    with session_scope(session_factory) as session:
        digest = session.query(Digest).filter(Digest.id == digest_id).first()
        
        if not digest:
            raise ValueError(f"Digest not found: {digest_id}")
        
        content = digest.content_json
        bot_token = settings.telegram_bot_token
        
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not configured. Check .env file.")
        
        bot = Bot(token=bot_token)
        
        try:
            # Send each article as a separate message with only title, description, and link
            for section in content['sections']:
                for article in section['articles']:
                    title = _strip_html(article.get('title', ''))
                    description = _strip_html(article.get('llm_summary', '')) or _strip_html(article.get('summary', ''))
                    url = _normalize_url(article.get('url'))

                    article_message = f"{title}\n\n"
                    article_message += f"{description}\n\n"
                    article_message += f"{url}"

                    await bot.send_message(
                        chat_id=chat_id,
                        text=article_message,
                        disable_web_page_preview=False,
                    )
            
            logger.info("digest_telegrammed", digest_id=digest_id, persona=digest.persona, chat_id=chat_id, articles_sent=content['total_articles'])
            
        except TelegramError as e:
            logger.error("telegram_send_failed", error=str(e), chat_id=chat_id)
            raise


def send_digest_telegram(digest_id: str, chat_id: str) -> None:
    """Send a digest via Telegram (sync wrapper)."""
    asyncio.run(send_digest_telegram_async(digest_id, chat_id))
