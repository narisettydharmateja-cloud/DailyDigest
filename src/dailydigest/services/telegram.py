"""Telegram bot delivery service for sending digests."""

import asyncio
from typing import Optional

import structlog
from telegram import Bot
from telegram.error import TelegramError
from telegram.constants import ParseMode

from ..config import settings
from ..models.db import Digest
from ..services.database import build_engine, create_session_factory, session_scope

logger = structlog.get_logger()


def format_digest_telegram(digest: Digest) -> str:
    """Format digest content for Telegram (Markdown)."""
    content = digest.content_json
    
    # Emoji based on persona
    emoji = "🤖" if digest.persona == "genai" else "🚀"
    
    # Build message
    message = f"{emoji} *{digest.persona.replace('_', ' ').title()} Digest*\n"
    message += f"_{digest.generated_at.strftime('%B %d, %Y')}_\n\n"
    
    # Intro
    message += f"{content['intro']}\n\n"
    
    # Clusters
    message += "━━━━━━━━━━━━━━━\n\n"
    
    for i, section in enumerate(content['sections'], 1):
        message += f"*Topic {i}: {section['theme']}*\n"
        message += f"📊 {section['article_count']} articles • ⭐ {section['avg_score']:.2f} avg score\n\n"
        message += f"{section['summary']}\n\n"
        
        message += "*Articles:*\n"
        for article in section['articles']:
            # Escape special characters for Telegram Markdown V2
            title = article['title'].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')
            message += f"• [{title}]({article['url']})\n"
        
        message += "\n━━━━━━━━━━━━━━━\n\n"
    
    # Footer
    message += f"📈 *Total:* {content['total_articles']} articles across {content['total_clusters']} topics\n"
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
            parts = message.split("━━━━━━━━━━━━━━━")
            current_part = parts[0]
            
            for part in parts[1:]:
                if len(current_part) + len(part) + 15 < max_length:
                    current_part += "━━━━━━━━━━━━━━━" + part
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


def send_digest_telegram(digest_id: str, chat_id: str) -> None:
    """Send a digest via Telegram."""
    engine = build_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    
    with session_scope(session_factory) as session:
        digest = session.query(Digest).filter(Digest.id == digest_id).first()
        
        if not digest:
            raise ValueError(f"Digest not found: {digest_id}")
        
        # Format message
        message = format_digest_telegram(digest)
        
        # Send message
        send_telegram_message(chat_id=chat_id, message=message)
        
        logger.info("digest_telegrammed", digest_id=digest_id, persona=digest.persona, chat_id=chat_id)
