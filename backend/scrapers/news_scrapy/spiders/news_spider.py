"""
VoteSmart TN — News Spider (Scrapy Spider)

Crawls Google News RSS for election-related articles about candidates 
in the database. Passes articles through the Gemini fact-checker before 
saving to Supabase.

Usage:
  cd backend && scrapy crawl news_spider
  OR: python backend/scrapers/news_scrapy/spiders/news_spider.py
"""
import os
import sys
import re
import logging
from datetime import datetime
from urllib.parse import urlparse

import scrapy
from scrapy.crawler import CrawlerProcess

logger = logging.getLogger('scrapers.news_spider')

# Regional domains (for local_mention tagging)
REGIONAL_DOMAINS = [
    'www.puthiyathalaimurai.com',
    'www.dinamalar.com',
    'tamil.news18.com',
    'www.dailythanthi.com',
    'www.hindutamil.in',
]

class NewsSpider(scrapy.Spider):
    """
    Spider that scrapes election news globally using Google News RSS.
    """
    name = 'news_spider'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Load env
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '.env')
        load_dotenv(env_path)
        
        # Initialize Supabase
        from supabase import create_client
        self.supabase = create_client(
            os.environ.get('SUPABASE_URL'),
            os.environ.get('SUPABASE_SERVICE_KEY')
        )
        
        # Fetch candidates from DB
        self.candidates = self._fetch_candidates()
        
        # Build start URLs from candidate search queries
        self.start_urls = self._build_search_urls()
        
        # Track processed URLs to avoid duplicates
        self.processed_urls = set()
        
        logger.info(f"Initialized with {len(self.candidates)} candidates, {len(self.start_urls)} start URLs")

    def _fetch_candidates(self) -> list:
        """Fetch all candidates with their constituency names from Supabase."""
        try:
            result = self.supabase.table('candidates') \
                .select('id, name, constituency_id, party') \
                .execute()
            candidates = result.data or []
            
            # Fetch constituency names
            const_result = self.supabase.table('constituencies') \
                .select('id, name') \
                .execute()
            const_map = {c['id']: c['name'] for c in (const_result.data or [])}
            
            for c in candidates:
                c['constituency_name'] = const_map.get(c['constituency_id'], '')
            
            return candidates
        except Exception as e:
            logger.error(f"Failed to fetch candidates: {e}")
            return []

    def _build_search_urls(self) -> list:
        """Build Bing News RSS search URLs for each candidate."""
        urls = []
        
        # Add candidate-specific search URLs (limit to first 50 to avoid overwhelming)
        for candidate in self.candidates[:50]:
            query = f"{candidate['name']} {candidate['constituency_name']} election"
            query_encoded = query.replace(' ', '+')
            # Bing News RSS (returns HTTP 302 direct links instead of JS redirects like Google)
            urls.append(f"https://www.bing.com/news/search?q={query_encoded}&format=rss&mkt=en-in")
            urls.append(f"https://www.bing.com/news/search?q={query_encoded}&format=rss&mkt=ta-in")
        
        return urls

    def start_requests(self):
        """Explicitly yield start requests."""
        logger.info(f"Starting requests for {len(self.start_urls)} URLs")
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        """Parse Google News RSS XML and yield requests to article links."""
        response.selector.remove_namespaces() # To easily match <item><link>
        links = response.xpath('//item/link/text()').getall()
        
        for link in links:
            if link and link.startswith('http'):
                yield scrapy.Request(link, callback=self.parse_article)

    def _find_matching_candidate(self, text: str) -> dict | None:
        """
        Find which candidate this article is about by checking if any
        candidate's name appears in the article text.
        """
        text_lower = text.lower()
        for candidate in self.candidates:
            name = candidate.get('name', '')
            if not name:
                continue
                
            # Check for candidate name (both full and partial matches)
            if name.lower() in text_lower:
                return candidate
            # Also check first name + last name separately for better matching
            name_parts = name.split()
            if len(name_parts) >= 2:
                if all(part.lower() in text_lower for part in name_parts):
                    return candidate
        return None

    def parse_article(self, response):
        """
        Parse a news article page.
        
        Extracts headline, body, published date, and passes through
        Gemini fact-checker before saving to Supabase.
        """
        url = response.url
        
        # Skip if already processed
        if url in self.processed_urls:
            return
        self.processed_urls.add(url)
        
        # Determine source domain
        domain = urlparse(url).netloc
        is_local = any(d in domain for d in REGIONAL_DOMAINS)
        
        # Extract content based on site structure
        headline = self._extract_headline(response)
        body = self._extract_body(response)
        published_at = self._extract_date(response)
        
        if not headline or not body or len(body) < 100:
            return
        
        # Try to match article to a candidate
        full_text = f"{headline} {body}"
        candidate = self._find_matching_candidate(full_text)
        
        if not candidate:
            logger.debug(f"No candidate match: {headline[:60]}")
            return
        
        # Build article dict
        article = {
            'candidate_id': candidate['id'],
            'source': domain,
            'url': url,
            'headline': headline[:500],
            'body': body[:10000],
            'published_at': published_at,
            'local_mention': is_local,
        }
        
        # Run through Gemini filter (sync wrapper since Scrapy uses Twisted)
        try:
            # Important: handle relative imports depending on how script is run
            import sys
            import os
            # Ensure backend path is in sys.path
            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            if backend_dir not in sys.path:
                sys.path.append(backend_dir)
                
            from scrapers.gemini_filter import filter_article_sync
            filtered = filter_article_sync(article)
            
            if filtered is None:
                logger.info(f"Gemini filtered out: {headline[:60]}")
                return
            
            # Save to Supabase
            save_data = {
                'candidate_id': filtered['candidate_id'],
                'source': filtered['source'],
                'url': filtered['url'],
                'headline': filtered['headline'],
                'body': filtered['body'],
                'published_at': filtered.get('published_at'),
                'sentiment_score': filtered.get('sentiment_score', 0.0),
                'is_factual': True,
                'local_mention': filtered.get('local_mention', False),
            }
            
            self.supabase.table('news_articles').upsert(
                save_data,
                on_conflict='url'
            ).execute()
            
            logger.info(
                f"Saved article: {headline[:50]} → {candidate['name']} "
                f"(sentiment: {filtered.get('sentiment_score', 0):.2f})"
            )
            
        except Exception as e:
            logger.error(f"Error processing article '{headline[:40]}': {e}")

    def _extract_headline(self, response) -> str:
        """Extract article headline using common selectors."""
        selectors = [
            'h1.title::text',
            'h1.article-heading::text',
            'h1::text',
            'meta[property="og:title"]::attr(content)',
            '.article-title::text',
            '.entry-title::text',
            '.headline::text',
        ]
        for selector in selectors:
            text = response.css(selector).get()
            if text and text.strip():
                return text.strip()
        return ''

    def _extract_body(self, response) -> str:
        """Extract article body text using common selectors."""
        selectors = [
            '.article-body p::text',
            '.article-content p::text',
            '.entry-content p::text',
            '.story-content p::text',
            'article p::text',
            '.content-area p::text',
            '#content-body p::text',
        ]
        for selector in selectors:
            paragraphs = response.css(selector).getall()
            if paragraphs:
                return ' '.join(p.strip() for p in paragraphs if p.strip())
        
        # Fallback: extract all paragraph text
        all_p = response.css('p::text').getall()
        return ' '.join(p.strip() for p in all_p if p.strip())

    def _extract_date(self, response) -> str | None:
        """Extract published date using meta tags and common selectors."""
        selectors = [
            'meta[property="article:published_time"]::attr(content)',
            'meta[name="pubdate"]::attr(content)',
            'meta[name="publish-date"]::attr(content)',
            'time::attr(datetime)',
            '.article-date::text',
            '.published-date::text',
        ]
        for selector in selectors:
            date_str = response.css(selector).get()
            if date_str and date_str.strip():
                try:
                    # Try ISO format first
                    dt = datetime.fromisoformat(date_str.strip().replace('Z', '+00:00'))
                    return dt.isoformat()
                except ValueError:
                    return date_str.strip()
        return None


def run_spider():
    """Run the news spider from command line."""
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '.env')
    load_dotenv(env_path)
    
    process = CrawlerProcess({
        'BOT_NAME': 'votesmart_news',
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS': 8,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4,
        'DOWNLOAD_DELAY': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        },
        'LOG_LEVEL': 'DEBUG',
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'DEPTH_LIMIT': 3, # Google News links might redirect
        'REQUEST_FINGERPRINTER_IMPLEMENTATION': '2.7',
    })
    
    process.crawl(NewsSpider)
    process.start()


if __name__ == '__main__':
    run_spider()
