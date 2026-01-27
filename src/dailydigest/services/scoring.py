"""LLM-based scoring and relevance evaluation using Ollama."""

from __future__ import annotations

import json
from typing import Dict, List, Optional

import ollama
import structlog

log = structlog.get_logger(__name__)

DEFAULT_MODEL = "llama3.2:3b"

RELEVANCE_PROMPT = """You are a tech news relevance evaluator. Score this article on its relevance to the following categories:

**Categories:**
1. **GENAI_NEWS**: Generative AI, LLMs, AI research, machine learning breakthroughs
2. **PRODUCT_IDEAS**: Innovative products, startups, tech tools, developer products

**Article:**
Title: {title}
Summary: {summary}

**Task:** Rate relevance for each category from 0.0 (not relevant) to 1.0 (highly relevant).

Respond ONLY with valid JSON in this exact format:
{{"genai_news": 0.8, "product_ideas": 0.3, "explanation": "Brief reason for scores"}}"""


def score_article_relevance(
    title: str,
    summary: str,
    model_name: str = DEFAULT_MODEL,
) -> Dict[str, float]:
    """
    Score an article's relevance to different categories using LLM.
    
    Args:
        title: Article title
        summary: Article summary/content
        model_name: Ollama model name
        
    Returns:
        Dictionary with scores: {
            'genai_news': float,
            'product_ideas': float,
            'explanation': str
        }
    """
    prompt = RELEVANCE_PROMPT.format(title=title, summary=summary[:500])
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.1, "num_predict": 150},
        )
        
        content = response["message"]["content"].strip()
        
        # Try to extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        scores = json.loads(content)
        
        # Validate and normalize scores
        result = {
            "genai_news": max(0.0, min(1.0, float(scores.get("genai_news", 0.0)))),
            "product_ideas": max(0.0, min(1.0, float(scores.get("product_ideas", 0.0)))),
            "explanation": scores.get("explanation", ""),
        }
        
        log.info(
            "scored_article",
            title=title[:50],
            genai=result["genai_news"],
            product=result["product_ideas"],
        )
        
        return result
        
    except Exception as exc:
        log.error("scoring_failed", error=str(exc), title=title[:50])
        return {
            "genai_news": 0.0,
            "product_ideas": 0.0,
            "explanation": f"Error: {str(exc)}",
        }


def batch_score_articles(
    articles: List[Dict[str, str]],
    model_name: str = DEFAULT_MODEL,
) -> List[Dict[str, float]]:
    """
    Score multiple articles for relevance.
    
    Args:
        articles: List of dicts with 'title' and 'summary' keys
        model_name: Ollama model name
        
    Returns:
        List of score dictionaries
    """
    results = []
    for article in articles:
        scores = score_article_relevance(
            title=article.get("title", ""),
            summary=article.get("summary", ""),
            model_name=model_name,
        )
        results.append(scores)
    
    return results
