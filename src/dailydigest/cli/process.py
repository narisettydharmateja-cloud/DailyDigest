"""CLI commands for processing articles with embeddings and LLM scoring."""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
import typer

from dailydigest.config import get_config
from dailydigest.logging import configure_logging
from dailydigest.models.db import IngestedItem
from dailydigest.services.database import build_engine, create_session_factory, session_scope
from dailydigest.services.embeddings import generate_single_embedding
from dailydigest.services.scoring import score_article_relevance

app = typer.Typer(add_completion=False, help="Process articles with AI: embeddings and scoring.")


@app.command("process")
def process_articles(
    limit: int = typer.Option(None, "--limit", help="Max number of articles to process"),
    force: bool = typer.Option(False, "--force", help="Reprocess already processed articles"),
) -> None:
    """Generate embeddings and LLM scores for unprocessed articles."""
    
    configure_logging()
    log = structlog.get_logger("cli.process")
    config = get_config()
    
    engine = build_engine(config.database_url)
    session_factory = create_session_factory(engine)
    
    with session_scope(session_factory) as session:
        # Query unprocessed or all articles
        query = session.query(IngestedItem)
        if not force:
            query = query.filter(IngestedItem.processed_at.is_(None))
        
        if limit:
            query = query.limit(limit)
        
        articles = query.all()
        
        if not articles:
            log.info("no_articles_to_process")
            typer.echo("No articles to process.")
            return
        
        log.info("processing_articles", count=len(articles))
        typer.echo(f"Processing {len(articles)} articles...")
        
        processed = 0
        for article in articles:
            try:
                # Generate embedding from title + summary
                text_to_embed = f"{article.title}. {article.summary or ''}"[:1000]
                embedding = generate_single_embedding(text_to_embed)
                
                # Score with LLM
                scores = score_article_relevance(
                    title=article.title,
                    summary=article.summary or article.title,
                )
                
                # Update article
                article.embedding = embedding
                article.genai_news_score = scores["genai_news"]
                article.product_ideas_score = scores["product_ideas"]
                article.score_explanation = scores["explanation"]
                article.processed_at = datetime.now(tz=UTC)
                
                processed += 1
                
                if processed % 5 == 0:
                    session.commit()
                    log.info("progress", processed=processed, total=len(articles))
                    typer.echo(f"Processed {processed}/{len(articles)} articles...")
                
            except Exception as exc:  # noqa: BLE001
                log.error("processing_failed", article_id=str(article.id), error=str(exc))
                continue
        
        session.commit()
        log.info("processing_complete", processed=processed, total=len(articles))
        typer.echo(f"\n✓ Successfully processed {processed}/{len(articles)} articles")


@app.command("stats")
def show_stats() -> None:
    """Show statistics about processed articles."""
    
    configure_logging()
    config = get_config()
    
    engine = build_engine(config.database_url)
    session_factory = create_session_factory(engine)
    
    with session_scope(session_factory) as session:
        total = session.query(IngestedItem).count()
        processed = session.query(IngestedItem).filter(IngestedItem.processed_at.isnot(None)).count()
        unprocessed = total - processed
        
        typer.echo(f"\n📊 Article Processing Statistics")
        typer.echo(f"{'='*40}")
        typer.echo(f"Total articles:      {total}")
        typer.echo(f"Processed:           {processed}")
        typer.echo(f"Unprocessed:         {unprocessed}")
        typer.echo(f"{'='*40}")
        
        if processed > 0:
            # Show score distribution
            high_genai = session.query(IngestedItem).filter(
                IngestedItem.genai_news_score >= 0.7
            ).count()
            high_product = session.query(IngestedItem).filter(
                IngestedItem.product_ideas_score >= 0.7
            ).count()
            
            typer.echo(f"\n📈 Relevance Distribution")
            typer.echo(f"High GenAI relevance (≥0.7):     {high_genai}")
            typer.echo(f"High Product relevance (≥0.7):   {high_product}")


@app.command("list")
def list_top_articles(
    category: str = typer.Option("genai", "--category", "-c", help="Category: genai or product"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of articles to show"),
) -> None:
    """List top-scoring articles by category."""
    
    configure_logging()
    config = get_config()
    
    engine = build_engine(config.database_url)
    session_factory = create_session_factory(engine)
    
    with session_scope(session_factory) as session:
        query = session.query(IngestedItem).filter(IngestedItem.processed_at.isnot(None))
        
        if category.lower().startswith("gen"):
            query = query.order_by(IngestedItem.genai_news_score.desc())
            typer.echo(f"\n🤖 Top {limit} GenAI News Articles")
        else:
            query = query.order_by(IngestedItem.product_ideas_score.desc())
            typer.echo(f"\n🚀 Top {limit} Product Ideas Articles")
        
        articles = query.limit(limit).all()
        
        typer.echo(f"{'='*80}")
        for i, article in enumerate(articles, 1):
            score = article.genai_news_score if category.lower().startswith("gen") else article.product_ideas_score
            typer.echo(f"\n{i}. {article.title}")
            typer.echo(f"   Score: {score:.2f} | Source: {article.source}")
            typer.echo(f"   {article.url}")
