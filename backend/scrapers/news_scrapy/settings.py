"""
Scrapy settings for VoteSmart TN news spider.
"""

BOT_NAME = 'votesmart_news'

SPIDER_MODULES = ['scrapers.news_scrapy.spiders']
NEWSPIDER_MODULE = 'scrapers.news_scrapy.spiders'

# Crawl responsibly
ROBOTSTXT_OBEY = True

# Concurrency settings — be polite to news sites
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 3  # seconds between requests to same domain

# User agent
USER_AGENT = 'VoteSmartTN/1.0 (Election Research Bot; +https://votesmart-tn.in/about)'

# Retry settings
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Timeouts
DOWNLOAD_TIMEOUT = 30

# Allowed domains — WHITELIST ONLY
# Enforced in the spider as well
ALLOWED_DOMAINS = [
    'www.thehindu.com',
    'www.puthiyathalaimurai.com',
    'www.dinamalar.com',
    'tamil.news18.com',
]

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(levelname)s %(asctime)s [%(name)s] %(message)s'

# Don't follow pagination excessively
DEPTH_LIMIT = 3

# AutoThrottle for adaptive rate limiting
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3
AUTOTHROTTLE_MAX_DELAY = 15
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# Feed exports (disabled — we write directly to Supabase)
FEEDS = {}

# Item pipelines
ITEM_PIPELINES = {}

# Request fingerprinting
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
