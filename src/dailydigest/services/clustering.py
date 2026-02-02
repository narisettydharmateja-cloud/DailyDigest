"""Clustering service for grouping similar articles using embeddings."""

from __future__ import annotations

from typing import List, Dict, Any
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import structlog

log = structlog.get_logger(__name__)


def cluster_articles(
    articles: List[Dict[str, Any]],
    min_cluster_size: int = 2,
    similarity_threshold: float = 0.7,
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Cluster articles based on embedding similarity using DBSCAN.
    
    Args:
        articles: List of article dicts with 'id', 'embedding', and other fields
        min_cluster_size: Minimum number of articles to form a cluster
        similarity_threshold: Cosine similarity threshold (0-1)
        
    Returns:
        Dictionary mapping cluster_id to list of articles
        Cluster -1 contains outliers (unclustered articles)
    """
    if not articles or len(articles) < min_cluster_size:
        log.info("too_few_articles_to_cluster", count=len(articles))
        return {0: articles} if articles else {}
    
    # Extract embeddings
    embeddings = []
    valid_articles = []
    
    for article in articles:
        if article.get("embedding") and len(article["embedding"]) > 0:
            embeddings.append(article["embedding"])
            valid_articles.append(article)
    
    if len(embeddings) < min_cluster_size:
        log.warning("insufficient_embeddings", available=len(embeddings), required=min_cluster_size)
        return {0: valid_articles} if valid_articles else {}
    
    # Convert to numpy array
    X = np.array(embeddings)
    
    # DBSCAN clustering with cosine distance
    # eps = 1 - similarity_threshold converts similarity to distance
    eps = 1 - similarity_threshold
    clustering = DBSCAN(eps=eps, min_samples=min_cluster_size, metric="cosine")
    labels = clustering.fit_predict(X)
    
    # Group articles by cluster
    clusters: Dict[int, List[Dict[str, Any]]] = {}
    for article, label in zip(valid_articles, labels):
        label = int(label)
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(article)
    
    # Log cluster statistics
    n_clusters = len([k for k in clusters.keys() if k != -1])
    n_noise = len(clusters.get(-1, []))
    
    log.info(
        "clustering_complete",
        total_articles=len(valid_articles),
        clusters=n_clusters,
        noise=n_noise,
    )
    
    # If no clusters formed, treat each article as its own cluster
    if n_clusters == 0 and valid_articles:
        log.info("no_clusters_formed_using_individual_articles")
        clusters = {i: [article] for i, article in enumerate(valid_articles)}
    
    return clusters


def get_cluster_centroid(articles: List[Dict[str, Any]]) -> List[float]:
    """
    Calculate the centroid (mean embedding) of a cluster.
    
    Args:
        articles: List of articles with embeddings
        
    Returns:
        Centroid embedding vector
    """
    embeddings = [a["embedding"] for a in articles if a.get("embedding")]
    if not embeddings:
        return []
    
    centroid = np.mean(embeddings, axis=0)
    return centroid.tolist()


def find_representative_article(
    articles: List[Dict[str, Any]],
    centroid: List[float] | None = None,
) -> Dict[str, Any]:
    """
    Find the article closest to the cluster centroid.
    
    Args:
        articles: List of articles in the cluster
        centroid: Pre-computed centroid (optional)
        
    Returns:
        The most representative article
    """
    if not articles:
        return {}
    
    if len(articles) == 1:
        return articles[0]
    
    if centroid is None:
        centroid = get_cluster_centroid(articles)
    
    if not centroid:
        return articles[0]
    
    # Calculate similarity to centroid
    centroid_array = np.array(centroid).reshape(1, -1)
    max_similarity = -1
    representative = articles[0]
    
    for article in articles:
        if not article.get("embedding"):
            continue
        
        embedding = np.array(article["embedding"]).reshape(1, -1)
        similarity = cosine_similarity(centroid_array, embedding)[0][0]
        
        if similarity > max_similarity:
            max_similarity = similarity
            representative = article
    
    return representative


def rank_clusters_by_importance(
    clusters: Dict[int, List[Dict[str, Any]]],
    score_field: str = "genai_news_score",
) -> List[tuple[int, List[Dict[str, Any]], float]]:
    """
    Rank clusters by average relevance score.
    
    Args:
        clusters: Dictionary of cluster_id to articles
        score_field: Field name to use for scoring
        
    Returns:
        List of (cluster_id, articles, avg_score) tuples, sorted by score
    """
    ranked = []
    
    for cluster_id, articles in clusters.items():
        if cluster_id == -1:  # Skip noise cluster
            continue
        
        scores = [a.get(score_field, 0.0) for a in articles]
        avg_score = np.mean(scores) if scores else 0.0
        ranked.append((cluster_id, articles, float(avg_score)))
    
    # Sort by average score descending
    ranked.sort(key=lambda x: x[2], reverse=True)
    
    return ranked
