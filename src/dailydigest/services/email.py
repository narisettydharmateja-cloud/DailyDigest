"""Email delivery service for sending digests via SMTP."""

import asyncio
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse

import httpx
import structlog

from ..config import get_config
from ..models.db import Digest
from ..services.database import build_engine, create_session_factory, session_scope

logger = structlog.get_logger()
config = get_config()

_OG_IMAGE_CACHE: dict[str, Optional[str]] = {}


def _normalize_url(url: str | None) -> Optional[str]:
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme:
        return url
    if url.startswith("//"):
        return f"https:{url}"
    return f"https://{url}"


def _extract_preview_image(url: str | None) -> Optional[str]:
    if not url:
        return None
    if url in _OG_IMAGE_CACHE:
        return _OG_IMAGE_CACHE[url]

    image_url: Optional[str] = None
    try:
        response = httpx.get(
            url,
            headers={"User-Agent": "DailyDigestBot/0.1 (+https://local.run/dailydigest)"},
            timeout=5.0,
            follow_redirects=True,
        )
        content_type = response.headers.get("content-type", "")
        if response.status_code == 200 and "text/html" in content_type:
            html = response.text
            og_match = re.search(
                r"property=[\"']og:image[\"']\s+content=[\"']([^\"']+)[\"']",
                html,
                re.IGNORECASE,
            )
            if not og_match:
                og_match = re.search(
                    r"name=[\"']twitter:image[\"']\s+content=[\"']([^\"']+)[\"']",
                    html,
                    re.IGNORECASE,
                )
            if og_match:
                image_url = og_match.group(1).strip()
                if image_url and image_url.startswith("/"):
                    image_url = urljoin(url, image_url)
    except Exception:
        image_url = None

    _OG_IMAGE_CACHE[url] = image_url
    return image_url


def format_digest_topic_email(
    digest: Digest,
    section: dict,
    index: int,
    preview_image_url: Optional[str] = None,
    preview_title: Optional[str] = None,
) -> str:
    """Format a single digest topic as HTML email with at most one link."""
    content = digest.content_json
    top_url = None
    top_title = None
    if section.get("articles"):
        first_article = section["articles"][0]
        top_url = _normalize_url(first_article.get("url"))
        top_title = first_article.get("title")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #111; max-width: 700px; margin: 0 auto; padding: 20px; }}
            h1 {{ font-size: 28px; margin-bottom: 4px; }}
            .date {{ color: #555; font-style: italic; margin-bottom: 20px; }}
            h2 {{ font-size: 18px; margin: 0 0 6px 0; }}
            .meta {{ color: #666; font-size: 13px; margin-bottom: 10px; }}
            a {{ color: #0b5fff; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .preview {{ border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; margin-top: 12px; }}
            .preview-img {{ width: 100%; height: auto; display: block; }}
            .preview-body {{ padding: 12px; }}
            .preview-title {{ font-size: 14px; font-weight: 600; margin: 0 0 6px 0; color: #111; }}
            .footer {{ color: #777; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>{digest.persona.replace('_', ' ').title()} Digest</h1>
        <div class="date">{digest.generated_at.strftime('%B %d, %Y')}</div>
        <p>{content['intro']}</p>

        <h2>Topic {index}: {section['theme']}</h2>
        <div class="meta">{section['article_count']} articles, avg score: {section['avg_score']:.2f}</div>
        <p>{section['summary']}</p>
    """

    if top_url:
        link_text = top_title or "Read source"
        if preview_image_url:
            html += f"""
            <div class="preview">
                <a href="{top_url}" target="_blank">
                    <img class="preview-img" src="{preview_image_url}" alt="Article preview">
                </a>
                <div class="preview-body">
                    <a href="{top_url}" target="_blank">Open article →</a>
                </div>
            </div>
            """
        else:
            html += f"""<p><a href="{top_url}" target="_blank">{link_text}</a></p>"""

    html += f"""
        <div class="footer">
            <p><strong>Total:</strong> {content['total_articles']} articles across {content['total_clusters']} topics</p>
            <p><em>Powered by DailyDigest</em></p>
        </div>
    </body>
    </html>
    """

    return html


def format_welcome_email(categories: list[str], frequency: str) -> str:
    """Format a welcome email for new subscribers."""
    categories_text = ", ".join(categories) if categories else "your selected topics"
    freq_text = (frequency or "daily").capitalize()

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #111; max-width: 700px; margin: 0 auto; padding: 20px; }}
            h1 {{ font-size: 28px; margin-bottom: 8px; }}
            .subtitle {{ color: #555; margin-bottom: 20px; }}
            .box {{ border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px; background: #fafafa; }}
            .footer {{ color: #777; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>Welcome to DailyDigest</h1>
        <div class="subtitle">Your subscription is active.</div>
        <div class="box">
            <p><strong>Topics:</strong> {categories_text}</p>
            <p><strong>Frequency:</strong> {freq_text}</p>
        </div>
        <p>Your first digest will arrive soon.</p>
        <div class="footer">
            <em>Powered by DailyDigest</em>
        </div>
    </body>
    </html>
    """


def send_welcome_email(to_email: str, categories: list[str], frequency: str) -> None:
    """Send a welcome email to a new subscriber."""
    html_content = format_welcome_email(categories, frequency)
    subject = "Welcome to DailyDigest"
    send_email(to_email=to_email, subject=subject, html_content=html_content)


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_username: Optional[str] = None,
    smtp_password: Optional[str] = None,
    from_email: Optional[str] = None,
) -> None:
    """Send email via SMTP."""
    # Use provided values or fall back to settings
    smtp_host = smtp_host or config.smtp_host
    smtp_port = smtp_port or config.smtp_port
    smtp_username = smtp_username or config.smtp_username
    smtp_password = (smtp_password or config.smtp_password).replace(" ", "")
    from_email = from_email or config.smtp_from_email
    
    if not all([smtp_host, smtp_port, smtp_username, smtp_password, from_email]):
        raise ValueError("SMTP configuration incomplete. Check .env file.")
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    
    # Attach HTML content
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    # Send email
    try:
        if config.smtp_use_tls:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
        
        logger.info("email_sent", to=to_email, subject=subject)
    except Exception as e:
        logger.error("email_send_failed", error=str(e), to=to_email)
        raise


def send_digest_email(digest_id: str, to_email: str, max_topics: int = 5) -> None:
    """Send a digest via email with all topics in one email (max 5 topics)."""
    engine = build_engine(config.database_url)
    session_factory = create_session_factory(engine)
    
    with session_scope(session_factory) as session:
        digest = session.query(Digest).filter(Digest.id == digest_id).first()
        
        if not digest:
            raise ValueError(f"Digest not found: {digest_id}")
        
        content = digest.content_json
        sections = content["sections"][:max_topics]  # Limit to max_topics
        
        html_content = format_digest_email(digest, sections)
        subject = (
            f"{digest.persona.replace('_', ' ').title()} Digest - "
            f"{len(sections)} Topics ({digest.generated_at.strftime('%b %d, %Y')})"
        )

        send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
        )

        logger.info(
            "digest_emailed",
            digest_id=digest_id,
            persona=digest.persona,
            topics=len(sections),
            to=to_email,
        )


def format_digest_email(digest: Digest, sections: list) -> str:
    """Format a complete digest with multiple topics as HTML email."""
    content = digest.content_json
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #111; max-width: 700px; margin: 0 auto; padding: 20px; }}
            h1 {{ font-size: 28px; margin-bottom: 4px; }}
            .date {{ color: #555; font-style: italic; margin-bottom: 20px; }}
            h2 {{ font-size: 18px; margin: 24px 0 6px 0; color: #0b5fff; }}
            .meta {{ color: #666; font-size: 13px; margin-bottom: 10px; }}
            a {{ color: #0b5fff; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .topic {{ border-bottom: 1px solid #e5e7eb; padding-bottom: 16px; margin-bottom: 16px; }}
            .topic:last-child {{ border-bottom: none; }}
            .read-link {{ display: inline-block; margin-top: 8px; padding: 6px 12px; background: #0b5fff; color: #fff !important; border-radius: 4px; font-size: 13px; }}
            .footer {{ color: #777; font-size: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb; }}
        </style>
    </head>
    <body>
        <h1>{digest.persona.replace('_', ' ').title()} Digest</h1>
        <div class="date">{digest.generated_at.strftime('%B %d, %Y')}</div>
        <p>{content['intro']}</p>
    """
    
    for index, section in enumerate(sections, 1):
        top_url = None
        top_title = None
        
        if section.get("articles"):
            first_article = section["articles"][0]
            top_url = _normalize_url(first_article.get("url"))
            top_title = first_article.get("title")
        
        html += f"""
        <div class="topic">
            <h2>Topic {index}: {section['theme']}</h2>
            <div class="meta">{section['article_count']} articles, avg score: {section['avg_score']:.2f}</div>
            <p>{section['summary']}</p>
        """
        
        if top_url:
            link_text = top_title or "Read article"
            html += f"""<a class="read-link" href="{top_url}" target="_blank">{link_text} →</a>"""
        
        html += "</div>"
    
    html += f"""
        <div class="footer">
            <p><strong>Total:</strong> {content['total_articles']} articles across {content['total_clusters']} topics</p>
            <p><em>Powered by DailyDigest</em></p>
        </div>
    </body>
    </html>
    """
    
    return html
