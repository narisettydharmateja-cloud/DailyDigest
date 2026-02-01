"""CLI commands for delivering digests via email and Telegram."""

import typer
from rich.console import Console
from typing import Optional

from ..services.email import send_digest_email
from ..services.telegram import send_digest_telegram
from ..models.db import Digest, Subscription
from ..services.database import build_engine, create_session_factory, session_scope
from ..config import get_config

app = typer.Typer(help="Deliver digests via email or Telegram")
console = Console()


@app.command()
def broadcast(
    persona: str = typer.Option(..., "--persona", "-p", help="Persona to broadcast (genai, product)"),
    digest_id: str = typer.Option(None, "--digest-id", help="Specific digest ID to send. Defaults to latest."),
):
    """Broadcast digest to all subscribed users."""
    config = get_config()
    engine = build_engine(config.database_url)
    session_factory = create_session_factory(engine)
    
    # Map persona shortcodes to DB values if needed
    # Assuming frontend sends 'genai', 'product' which match what we expect or we need to map them?
    # Frontend sends: 'genai', 'product', 'tech', 'startup'
    # Our system generates: 'genai_news', 'product_ideas' usually.
    
    target_category = persona
    if persona == "genai":
        target_category = "genai" # frontend sends 'genai'
        persona_db = "genai_news" # DB stores digests as 'genai_news' probably?
    elif persona == "product":
        target_category = "product"
        persona_db = "product_ideas"
    else:
        persona_db = persona # Fallback
    
    with session_scope(session_factory) as session:
        # 1. Get Digest
        if digest_id:
            digest = session.query(Digest).filter(Digest.id == digest_id).first()
        else:
            # Get latest digest for this persona
            # Note: We need to match the persona name used in 'generate' command
            # Let's assume input matches or we handle it. 
            # If user passes 'genai', we might look for 'genai_news' digest?
            # Let's just look for contains.
            digest = session.query(Digest).filter(Digest.persona.ilike(f"%{persona}%")).order_by(Digest.generated_at.desc()).first()
            
        if not digest:
            console.print(f"✗ No digest found for persona containing '{persona}'", style="red")
            raise typer.Exit(1)
            
        console.print(f"Found digest: {digest.id} ({digest.persona}) generated at {digest.generated_at}")
        
        # 2. Get Subscribers
        # We look for subscriptions that have the target_category in their categories array
        subscribers = session.query(Subscription).filter(
            Subscription.is_active == "true",
            Subscription.categories.contains([target_category])
        ).all()
        
        if not subscribers:
            console.print(f"⚠ No active subscribers found for category '{target_category}'", style="yellow")
            return

        console.print(f"📢 Broadcasting to {len(subscribers)} subscribers...", style="bold blue")
        
        success_count = 0
        fail_count = 0
        
        for sub in subscribers:
            try:
                console.print(f"  • Sending to {sub.email}...", end=" ")
                send_digest_email(digest_id=str(digest.id), to_email=sub.email)
                console.print("✓", style="green")
                success_count += 1
            except Exception as e:
                console.print(f"✗ ({e})", style="red")
                fail_count += 1
                
        console.print(f"\nDone! Sent: {success_count}, Failed: {fail_count}", style="bold")


@app.command()
def email(
    digest_id: str = typer.Argument(..., help="Digest ID to send"),
    to_email: str = typer.Argument(..., help="Recipient email address"),
):
    """Send a digest via email."""
    try:
        console.print(f"📧 Sending digest {digest_id[:8]}... to {to_email}")
        send_digest_email(digest_id=digest_id, to_email=to_email)
        console.print("✓ Email sent successfully", style="green")
    except Exception as e:
        console.print(f"✗ Failed to send email: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def telegram(
    digest_id: str = typer.Argument(..., help="Digest ID to send"),
    chat_id: str = typer.Argument(..., help="Telegram chat ID"),
):
    """Send a digest via Telegram."""
    try:
        console.print(f"📱 Sending digest {digest_id[:8]}... to chat {chat_id}")
        send_digest_telegram(digest_id=digest_id, chat_id=chat_id)
        console.print("✓ Telegram message sent successfully", style="green")
    except Exception as e:
        console.print(f"✗ Failed to send Telegram message: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def both(
    digest_id: str = typer.Argument(..., help="Digest ID to send"),
    to_email: str = typer.Option(..., "--email", help="Recipient email address"),
    chat_id: str = typer.Option(..., "--chat-id", help="Telegram chat ID"),
):
    """Send a digest via both email and Telegram."""
    try:
        console.print(f"📧📱 Sending digest {digest_id[:8]}...")
        
        # Send email
        console.print("  📧 Sending email...")
        send_digest_email(digest_id=digest_id, to_email=to_email)
        console.print("  ✓ Email sent", style="green")
        
        # Send Telegram
        console.print("  📱 Sending Telegram...")
        send_digest_telegram(digest_id=digest_id, chat_id=chat_id)
        console.print("  ✓ Telegram sent", style="green")
        
        console.print("✓ Digest delivered via both channels", style="bold green")
    except Exception as e:
        console.print(f"✗ Failed to deliver digest: {e}", style="red")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
