"""Digest generation service using LLM for persona-aware summaries."""

from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any

import ollama
import structlog

log = structlog.get_logger(__name__)

DEFAULT_MODEL = "llama3.2:3b"

GENAI_DIGEST_PROMPT = """You are an AI research digest writer. Create a concise, engaging summary of these GenAI/AI news articles for technical professionals.

**Articles in this cluster:**
{articles}

**Instructions:**
- Write 2-3 sentences summarizing the key theme connecting these articles
- Highlight the most important development or insight
- Use clear, direct language
- Focus on what's new or significant

Respond ONLY with the summary text (no JSON, no extra formatting)."""

PRODUCT_DIGEST_PROMPT = """You are a product innovation digest writer. Create a concise, engaging summary of these product/startup news articles for builders and entrepreneurs.

**Articles in this cluster:**
{articles}

**Instructions:**
- Write 2-3 sentences summarizing the key product trend or innovation
- Highlight what's interesting for product builders
- Use clear, direct language
- Focus on actionable insights or inspiration

Respond ONLY with the summary text (no JSON, no extra formatting)."""

OVERALL_DIGEST_PROMPT = """You are writing a daily digest introduction. Create a brief, engaging intro (2-3 sentences) for today's {persona} digest.

**Context:**
- {num_clusters} main topics
- {num_articles} total articles
- Top themes: {themes}

Write a welcoming intro that sets the tone and previews the key themes. Be concise and engaging.

Respond ONLY with the intro text (no JSON, no extra formatting)."""

ARTICLE_SUMMARY_PROMPT = """You are summarizing a single news article for a daily digest.

Title:
{title}

Source text:
{source_text}

Instructions:
- Write 2-3 sentences summarizing the article
- Be concise and factual
- Do not include links or markdown

Respond ONLY with the summary text (no JSON, no extra formatting)."""


def format_articles_for_llm(articles: List[Dict[str, Any]]) -> str:
    """Format article list for LLM prompt."""
    lines = []
    for i, article in enumerate(articles, 1):
        title = article.get("title", "Untitled")
        summary = article.get("summary", "")[:200]  # Truncate long summaries
        score = article.get("genai_news_score") or article.get("product_ideas_score", 0.0)
        lines.append(f"{i}. {title} (relevance: {score:.1f})")
        if summary:
            lines.append(f"   {summary}")
    return "\n".join(lines)


def summarize_cluster(
    articles: List[Dict[str, Any]],
    persona: str = "genai",
    model_name: str = DEFAULT_MODEL,
) -> str:
    """
    Generate a summary for a cluster of articles.
    
    Args:
        articles: List of articles in the cluster
        persona: "genai" or "product"
        model_name: Ollama model name
        
    Returns:
        Summary text
    """
    if not articles:
        return ""
    
    articles_text = format_articles_for_llm(articles)
    
    if persona.lower().startswith("gen"):
        prompt = GENAI_DIGEST_PROMPT.format(articles=articles_text)
    else:
        prompt = PRODUCT_DIGEST_PROMPT.format(articles=articles_text)
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.7, "num_predict": 200},
        )
        
        summary = response["message"]["content"].strip()
        
        log.info(
            "cluster_summarized",
            persona=persona,
            articles=len(articles),
            length=len(summary),
        )
        
        return summary
        
    except Exception as exc:
        log.error("summarization_failed", error=str(exc), persona=persona)
        return f"Summary of {len(articles)} articles about {articles[0].get('title', 'tech news')[:50]}..."


def summarize_article(
    title: str,
    source_text: str,
    model_name: str = DEFAULT_MODEL,
) -> str:
    """Generate a concise summary for a single article."""
    title = (title or "").strip()
    source_text = (source_text or "").strip()

    if not title and not source_text:
        return ""

    prompt = ARTICLE_SUMMARY_PROMPT.format(
        title=title or "Untitled",
        source_text=source_text[:1200],
    )

    try:
        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.4, "num_predict": 180},
        )

        summary = response["message"]["content"].strip()
        log.info("article_summarized", length=len(summary))
        return summary
    except Exception as exc:
        log.error("article_summary_failed", error=str(exc))
        return (source_text or title)[:300]


def generate_digest_intro(
    num_clusters: int,
    num_articles: int,
    top_themes: List[str],
    persona: str = "genai",
    model_name: str = DEFAULT_MODEL,
) -> str:
    """
    Generate an introduction for the digest.
    
    Args:
        num_clusters: Number of topic clusters
        num_articles: Total article count
        top_themes: List of theme descriptions
        persona: "genai" or "product"
        model_name: Ollama model name
        
    Returns:
        Intro text
    """
    persona_name = "GenAI News" if persona.lower().startswith("gen") else "Product Ideas"
    themes_text = ", ".join(top_themes[:3])
    
    prompt = OVERALL_DIGEST_PROMPT.format(
        persona=persona_name,
        num_clusters=num_clusters,
        num_articles=num_articles,
        themes=themes_text,
    )
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.8, "num_predict": 150},
        )
        
        intro = response["message"]["content"].strip()
        log.info("intro_generated", persona=persona)
        return intro
        
    except Exception as exc:
        log.error("intro_generation_failed", error=str(exc))
        return f"Your {persona_name} digest with {num_articles} articles across {num_clusters} topics."


def generate_persona_digest(
    clusters: List[tuple[int, List[Dict[str, Any]], float]],
    persona: str = "genai",
    model_name: str = DEFAULT_MODEL,
    max_clusters: int = 5,
) -> Dict[str, Any]:
    """
    Generate a complete digest for a persona.
    
    Args:
        clusters: Ranked list of (cluster_id, articles, score) tuples
        persona: "genai" or "product"
        model_name: Ollama model name
        max_clusters: Maximum clusters to include
        
    Returns:
        Digest dictionary with intro, sections, and metadata
    """
    if not clusters:
        return {
            "persona": persona,
            "generated_at": datetime.now().isoformat(),
            "intro": "No relevant articles found for this digest.",
            "sections": [],
            "total_articles": 0,
        }
    
    # Take top N clusters
    top_clusters = clusters[:max_clusters]
    total_articles = sum(len(articles) for _, articles, _ in top_clusters)
    
    # Generate summaries for each cluster
    sections = []
    theme_titles = []
    
    for cluster_id, articles, avg_score in top_clusters:
        summary = summarize_cluster(articles, persona, model_name)
        
        # Use the most representative article's title as theme
        from dailydigest.services.clustering import find_representative_article
        rep_article = find_representative_article(articles)
        theme = rep_article.get("title", "Tech News")[:80]
        theme_titles.append(theme)
        
        article_items = []
        for article in articles:
            source_text = article.get("summary", "") or article.get("content", "") or ""
            llm_summary = article.get("llm_summary") or summarize_article(
                article.get("title", ""),
                source_text,
                model_name,
            )

            article_items.append({
                "title": article.get("title", ""),
                "summary": source_text,
                "llm_summary": llm_summary,
                "url": article.get("url", ""),
                "source": article.get("source", ""),
                "published_at": article.get("published_at"),
            })

        sections.append({
            "cluster_id": cluster_id,
            "theme": theme,
            "summary": summary,
            "avg_score": avg_score,
            "article_count": len(articles),
            "articles": article_items,
        })
    
    # Generate intro
    intro = generate_digest_intro(
        num_clusters=len(sections),
        num_articles=total_articles,
        top_themes=theme_titles,
        persona=persona,
        model_name=model_name,
    )
    
    digest = {
        "persona": persona,
        "generated_at": datetime.now().isoformat(),
        "intro": intro,
        "sections": sections,
        "total_articles": total_articles,
        "total_clusters": len(sections),
    }
    
    log.info(
        "digest_generated",
        persona=persona,
        clusters=len(sections),
        articles=total_articles,
    )
    
    return digest
