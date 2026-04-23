"""
VoteSmart TN — Gemini Filter (Fact-Check & Sentiment)

Uses Gemini 1.5 Flash to:
1. Determine if an article is factual (not opinion/spam)
2. Score sentiment (-1.0 to 1.0) about the candidate
3. Extract key factual claims
4. Detect IT-cell/propaganda spam signals

Articles that fail the filter (non-factual or 2+ spam signals) are discarded.

Usage:
  from scrapers.gemini_filter import filter_article, batch_filter_articles
"""
import os
import json
import asyncio
import logging
from typing import Optional

from google import genai
from google.genai import types

logger = logging.getLogger('scrapers.gemini_filter')

# Rate limiting config
BATCH_SIZE = 10
DELAY_BETWEEN_CALLS = 1.0  # seconds


def _get_client():
    """Configure and return Gemini Client."""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment")
    return genai.Client(api_key=api_key)


def _build_prompt(headline: str, body: str) -> str:
    """Build the fact-checking prompt for Gemini."""
    # Truncate body to 2000 chars to stay within token limits
    truncated_body = body[:2000] if body else ""
    
    return f"""You are a political fact-checker for Tamil Nadu elections.
Analyze this article and return JSON only (no markdown, no code fences):
{{
  "is_factual": true/false,
  "sentiment_score": float,
  "key_claims": [string],
  "spam_signals": [string]
}}

Rules:
- "is_factual": true if the article contains verifiable facts about candidates, elections, 
  policies, or government actions. false if it's pure opinion, satire, clickbait, or spam.
- "sentiment_score": a float from -1.0 (very negative about the candidate) to 1.0 
  (very positive). 0.0 for neutral.
- "key_claims": extract up to 3 specific factual claims from the article. Each claim should 
  be a concise statement about what the candidate did, said, or what happened.
- "spam_signals": list propaganda phrases, IT-cell boilerplate, or manipulative language 
  detected. Examples: "undeniable leader", "anti-national elements", "divine blessing", 
  "paid media", excessive use of party slogans.

Article headline: {headline}
Article body: {truncated_body}"""


async def filter_article(article_dict: dict) -> Optional[dict]:
    """
    Filter a single article through Gemini fact-checking.
    
    Args:
        article_dict: Dict with 'headline' and 'body' keys
        
    Returns:
        Enriched article dict if factual, None if filtered out
    """
    headline = article_dict.get('headline', '')
    body = article_dict.get('body', '')
    
    if not headline and not body:
        logger.warning("Empty article passed to filter — skipping")
        return None
    
    try:
        client = _get_client()
        prompt = _build_prompt(headline, body)
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,  # Low temp for consistent analysis
                max_output_tokens=500,
                response_mime_type="application/json",
            )
        )
        
        # Parse JSON response
        response_text = response.text.strip()
        
        # Clean up potential markdown code fences
        if response_text.startswith('```'):
            response_text = response_text.split('\n', 1)[1]  # Remove first line
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
        
        result = json.loads(response_text)
        
        is_factual = result.get('is_factual', False)
        spam_signals = result.get('spam_signals', [])
        
        # Filter decision
        if not is_factual:
            logger.info(f"FILTERED (non-factual): {headline[:80]}")
            return None
        
        if len(spam_signals) >= 2:
            logger.info(f"FILTERED (spam x{len(spam_signals)}): {headline[:80]}")
            return None
        
        # Enrich article with Gemini analysis
        article_dict['sentiment_score'] = float(result.get('sentiment_score', 0.0))
        article_dict['is_factual'] = True
        article_dict['key_claims'] = result.get('key_claims', [])
        article_dict['spam_signals'] = spam_signals
        
        logger.info(
            f"PASSED: {headline[:60]} | sentiment={article_dict['sentiment_score']:.2f}"
        )
        return article_dict
    
    except json.JSONDecodeError as e:
        logger.error(f"Gemini returned invalid JSON for '{headline[:50]}': {e}")
        return None
    except Exception as e:
        logger.error(f"Gemini filter error for '{headline[:50]}': {e}")
        return None


async def batch_filter_articles(articles: list) -> list:
    """
    Process articles in batches of BATCH_SIZE using asyncio.gather().
    Includes rate limiting between API calls.
    
    Args:
        articles: List of article dicts with 'headline' and 'body'
        
    Returns:
        List of filtered (factual) articles with sentiment scores
    """
    valid_articles = []
    total = len(articles)
    
    logger.info(f"Batch filtering {total} articles (batch_size={BATCH_SIZE})...")
    
    for batch_start in range(0, total, BATCH_SIZE):
        batch = articles[batch_start:batch_start + BATCH_SIZE]
        batch_num = (batch_start // BATCH_SIZE) + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} articles)...")
        
        # Process batch concurrently
        tasks = [filter_article(article) for article in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch task error: {result}")
            elif result is not None:
                valid_articles.append(result)
        
        # Rate limit delay between batches
        if batch_start + BATCH_SIZE < total:
            await asyncio.sleep(DELAY_BETWEEN_CALLS)
    
    logger.info(
        f"Batch filter complete: {len(valid_articles)}/{total} articles passed "
        f"({(len(valid_articles)/max(total,1))*100:.1f}% pass rate)"
    )
    return valid_articles


def filter_article_sync(article_dict: dict) -> Optional[dict]:
    """Synchronous wrapper for filter_article."""
    return asyncio.run(filter_article(article_dict))
