"""CLI commands for delivering digests via email and Telegram."""

import typer
from rich.console import Console
from typing import Optional

from ..services.email import send_digest_email
from ..services.telegram import send_digest_telegram

app = typer.Typer(help="Deliver digests via email or Telegram")
console = Console()


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
