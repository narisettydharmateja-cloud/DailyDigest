"""CLI commands for generating persona-based digests."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import structlog
import typer
from rich.console import Console
from rich.markdown import Markdown

from dailydigest.config import get_config
from dailydigest.logging import configure_logging
from dailydigest.models.db import Digest, IngestedItem
from dailydigest.services.clustering import cluster_articles, rank_clusters_by_importance
from dailydigest.services.database import build_engine, create_session_factory, init_database, session_scope
from dailydigest.services.digest import generate_persona_digest

app = typer.Typer(add_completion=False, help="Generate persona-based digests from processed articles.")
console = Console()


@app.command("generate")
def generate_digest(
    persona: str = typer.Option("genai", "--persona", "-p", help="Persona: genai or product"),
    min_score: float = typer.Option(0.6, "--min-score", help="Minimum relevance score"),
    days: int = typer.Option(1, "--days", help="Include articles from last N days"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save digest to database"),
    display: bool = typer.Option(True, "--display/--no-display", help="Display digest in terminal"),
) -> None:
    """Generate a persona-based digest from recent articles."""
    
    configure_logging()
    log = structlog.get_logger("cli.digest")
    config = get_config()
    
    engine = build_engine(config.database_url)
    init_database(engine)
    session_factory = create_session_factory(engine)
    
    # Determine score field
    persona_lower = persona.lower()
    if persona_lower.startswith("gen"):
        score_field = "genai_news_score"
        persona_name = "GenAI News"
    else:
        score_field = "product_ideas_score"
        persona_name = "Product Ideas"
    
    with session_scope(session_factory) as session:
        # Query recent processed articles above score threshold
        since = datetime.now(tz=UTC) - timedelta(days=days)
        
        query = (
            session.query(IngestedItem)
            .filter(IngestedItem.processed_at.isnot(None))
            .filter(IngestedItem.processed_at >= since)
        )
        
        if persona_lower.startswith("gen"):
            query = query.filter(IngestedItem.genai_news_score >= min_score)
        else:
            query = query.filter(IngestedItem.product_ideas_score >= min_score)
        
        articles_db = query.all()
        
        if not articles_db:
            console.print(f"\n[yellow]No articles found for {persona_name} persona with score >= {min_score}[/yellow]")
            return
        
        log.info("articles_fetched", count=len(articles_db), persona=persona_name)
        
        # Convert to dict format
        articles = []
        for article in articles_db:
            articles.append({
                "id": str(article.id),
                "title": article.title,
                "summary": article.summary or article.content or "",
                "url": article.url,
                "source": article.source,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "embedding": article.embedding,
                "genai_news_score": article.genai_news_score,
                "product_ideas_score": article.product_ideas_score,
            })
        
        console.print(f"\n[cyan]📊 Found {len(articles)} articles for {persona_name}[/cyan]")
        console.print("[cyan]🔄 Clustering similar articles...[/cyan]")
        
        # Cluster articles
        clusters = cluster_articles(articles, min_cluster_size=2, similarity_threshold=0.6)
        
        # Rank clusters
        ranked_clusters = rank_clusters_by_importance(clusters, score_field=score_field)
        
        if not ranked_clusters:
            console.print("[yellow]No clusters formed. Try lowering min-score or including more days.[/yellow]")
            return
        
        console.print(f"[cyan]✓ Created {len(ranked_clusters)} topic clusters[/cyan]")
        console.print("[cyan]✍️  Generating digest with LLM...[/cyan]\n")
        
        # Generate digest
        digest_data = generate_persona_digest(
            clusters=ranked_clusters,
            persona=persona_lower,
            max_clusters=5,
        )
        
        # Save to database
        if save:
            digest = Digest(
                persona=persona_lower,
                intro=digest_data["intro"],
                content_json=digest_data,
                total_articles=digest_data["total_articles"],
                total_clusters=digest_data["total_clusters"],
            )
            session.add(digest)
            session.commit()
            
            log.info("digest_saved", digest_id=str(digest.id), persona=persona_name)
            console.print(f"[green]✓ Digest saved to database (ID: {digest.id})[/green]\n")
        
        # Display digest
        if display:
            _display_digest(digest_data, persona_name)


@app.command("list")
def list_digests(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of digests to show"),
) -> None:
    """List previously generated digests."""
    
    configure_logging()
    config = get_config()
    
    engine = build_engine(config.database_url)
    session_factory = create_session_factory(engine)
    
    with session_scope(session_factory) as session:
        digests = (
            session.query(Digest)
            .order_by(Digest.generated_at.desc())
            .limit(limit)
            .all()
        )
        
        if not digests:
            console.print("[yellow]No digests found.[/yellow]")
            return
        
        console.print(f"\n[cyan]📰 Recent Digests[/cyan]")
        console.print("=" * 80)
        
        for digest in digests:
            persona_emoji = "🤖" if digest.persona.startswith("gen") else "🚀"
            persona_name = "GenAI News" if digest.persona.startswith("gen") else "Product Ideas"
            
            console.print(f"\n{persona_emoji} [bold]{persona_name}[/bold]")
            console.print(f"   ID: {digest.id}")
            console.print(f"   Generated: {digest.generated_at.strftime('%Y-%m-%d %H:%M')}")
            console.print(f"   Articles: {digest.total_articles} | Clusters: {digest.total_clusters}")
            console.print(f"   Intro: {digest.intro[:100]}...")


@app.command("show")
def show_digest(
    digest_id: str = typer.Argument(..., help="Digest ID to display"),
) -> None:
    """Display a specific digest."""
    
    configure_logging()
    config = get_config()
    
    engine = build_engine(config.database_url)
    session_factory = create_session_factory(engine)
    
    with session_scope(session_factory) as session:
        digest = session.query(Digest).filter(Digest.id == digest_id).first()
        
        if not digest:
            console.print(f"[red]Digest {digest_id} not found.[/red]")
            return
        
        persona_name = "GenAI News" if digest.persona.startswith("gen") else "Product Ideas"
        _display_digest(digest.content_json, persona_name)


def _display_digest(digest_data: dict, persona_name: str) -> None:
    """Display a digest in the terminal."""
    emoji = "🤖" if "genai" in persona_name.lower() else "🚀"
    
    console.print(f"\n[bold cyan]{emoji} {persona_name} Digest[/bold cyan]")
    console.print(f"[dim]{digest_data['generated_at']}[/dim]")
    console.print("=" * 80)
    
    # Intro
    console.print(f"\n[bold]{digest_data['intro']}[/bold]\n")
    
    # Sections
    for i, section in enumerate(digest_data["sections"], 1):
        console.print(f"\n[bold cyan]Topic {i}: {section['theme']}[/bold cyan]")
        console.print(f"[dim]({section['article_count']} articles, avg score: {section['avg_score']:.2f})[/dim]")
        console.print(f"\n{section['summary']}\n")
        
        console.print("[dim]Articles:[/dim]")
        for article in section["articles"]:
            console.print(f"  • {article['title']}")
            console.print(f"    [dim]{article['url']}[/dim]")
    
    console.print("\n" + "=" * 80)
    console.print(f"[dim]Total: {digest_data['total_articles']} articles across {digest_data['total_clusters']} topics[/dim]\n")
