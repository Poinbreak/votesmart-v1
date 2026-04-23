"""
VoteSmart TN — MyNeta Candidate Scraper (Playwright)

Scrapes MyNeta for Tamil Nadu assembly election candidates. 
Extracts structured data directly from the constituency tables.

Target: https://www.myneta.info/TamilNadu2026/
Method: Playwright async API with Chromium
Schedule: Daily at 23:30 IST via GitHub Actions

Usage:
  python backend/scrapers/myneta_playwright.py
"""
import os
import sys
import re
import asyncio
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s %(asctime)s [%(name)s] %(message)s',
    stream=sys.stderr,
)
logger = logging.getLogger('scrapers.myneta')

async def get_supabase():
    """Create Supabase client."""
    from supabase import create_client
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    return create_client(url, key)

def parse_currency(amount_str: str) -> int:
    """Parse MyNeta asset strings like 'Rs 1,58,32,134 ~ 1 Crore+' to int."""
    if not amount_str or 'Nil' in amount_str:
        return 0
    match = re.search(r'([\d,]+)', amount_str)
    if match:
        try:
            return int(match.group(1).replace(',', ''))
        except ValueError:
            return 0
    return 0

def parse_int(val_str: str) -> int:
    """Safely parse integer from string."""
    if not val_str:
        return 0
    cleaned = re.sub(r'[^\d]', '', val_str)
    if cleaned:
        return int(cleaned)
    return 0

async def retry_with_backoff(func, max_retries=3, *args, **kwargs):
    """Execute an async function with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)

async def scrape_constituency(page, constituency_name: str, supabase, db_constituency_id: int, myneta_url: str):
    """
    Scrape candidate data for a single constituency from MyNeta.
    """
    logger.info(f"Scraping {constituency_name} via {myneta_url}")
    
    try:
        await page.goto(myneta_url, timeout=30000)
        await page.wait_for_selector('table.w3-table.w3-bordered tr', timeout=15000)
        
        # Get all rows in the candidates table
        rows = await page.locator('table.w3-table.w3-bordered tr').all()
        
        if len(rows) <= 1:
            logger.warning(f"No candidate rows found for {constituency_name}")
            return
            
        candidates_processed = 0
        
        # Skip header row (index 0)
        candidate_data_list = []
        for i in range(1, len(rows)):
            try:
                row = rows[i]
                cells = await row.locator('td').all()
                
                if len(cells) < 7:
                    continue
                
                candidate_name = (await cells[1].inner_text()).strip()
                party = (await cells[2].inner_text()).strip()
                cases_str = (await cells[3].inner_text()).strip()
                education = (await cells[4].inner_text()).strip()
                age_str = (await cells[5].inner_text()).strip()
                assets_str = (await cells[6].inner_text()).strip()
                
                if not candidate_name:
                    continue
                
                asset_value = parse_currency(assets_str)
                criminal_cases = parse_int(cases_str)
                age = parse_int(age_str)
                
                candidate_data_list.append({
                    'constituency_id': db_constituency_id,
                    'name': candidate_name,
                    'party': party,
                    'asset_value_current': asset_value if asset_value > 0 else None,
                    'criminal_cases': criminal_cases,
                    'education': education if education else None,
                    'age': age if age > 0 else None,
                    'affidavit_text': None,  # No raw affidavit text from MyNeta summary
                })
                    
            except Exception as e:
                logger.error(f"  Error processing row {i} for {constituency_name}: {e}")
                continue
                
        if candidate_data_list:
            try:
                # Delete existing candidates for this constituency to avoid duplicates
                supabase.table('candidates').delete().eq('constituency_id', db_constituency_id).execute()
                # Insert the newly scraped candidates
                supabase.table('candidates').insert(candidate_data_list).execute()
                candidates_processed = len(candidate_data_list)
                for c in candidate_data_list:
                    logger.info(f"  ✓ {c['name']} ({c['party']}) — Assets: ₹{c['asset_value_current'] or 0:,}, Cases: {c['criminal_cases']}")
            except Exception as e:
                logger.error(f"  ✗ DB insert failed for {constituency_name}: {e}")
                
        logger.info(f"Completed {constituency_name}: {candidates_processed} candidates processed")
        
    except Exception as e:
        logger.error(f"Failed to scrape constituency {constituency_name}: {e}", exc_info=True)

async def main():
    """Main scraping pipeline."""
    from playwright.async_api import async_playwright
    
    # Load env
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    load_dotenv(env_path)
    
    supabase = await get_supabase()
    
    # Fetch all constituencies from database
    result = supabase.table('constituencies') \
        .select('id, name') \
        .order('id') \
        .execute()
    
    db_constituencies = result.data or []
    logger.info(f"Found {len(db_constituencies)} constituencies in DB")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        page.set_default_timeout(30000)
        
        # 1. Map MyNeta constituencies
        logger.info("Fetching MyNeta constituency index...")
        await page.goto('https://www.myneta.info/TamilNadu2026/', timeout=30000)
        
        myneta_links = {}
        links = await page.locator('a[href*="show_candidates&constituency_id"]').all()
        for link in links:
            text = (await link.inner_text()).strip().upper()
            href = await link.get_attribute('href')
            if href:
                full_url = f"https://www.myneta.info/TamilNadu2026/{href}"
                
                # MyNeta names might include (SC) or (ST), we clean them for matching
                clean_name = re.sub(r'\(.*?\)', '', text).strip()
                myneta_links[clean_name] = full_url
                myneta_links[text] = full_url # keep original too
        
        logger.info(f"Found {len(myneta_links)} constituency links on MyNeta")
        
        # 2. Scrape each mapped constituency
        for db_c in db_constituencies:
            db_name = db_c['name'].upper()
            
            # Simple matching strategy
            match_url = None
            if db_name in myneta_links:
                match_url = myneta_links[db_name]
            else:
                # Try partial match or removing spaces (e.g. VIRUGAMPAKKAM vs VIRUGAMPAKKAM:CHENNAI)
                for mk, murl in myneta_links.items():
                    # MyNeta sometimes appends district like "VIRUGAMPAKKAM:CHENNAI"
                    # But the links list usually just has "VIRUGAMPAKKAM"
                    if db_name.replace(' ', '') == mk.replace(' ', ''):
                        match_url = murl
                        break
                        
            if not match_url:
                logger.warning(f"Could not find MyNeta link for DB constituency: {db_name}")
                continue
                
            try:
                await retry_with_backoff(
                    scrape_constituency,
                    max_retries=3,
                    page=page,
                    constituency_name=db_name,
                    supabase=supabase,
                    db_constituency_id=db_c['id'],
                    myneta_url=match_url
                )
            except Exception as e:
                logger.error(
                    f"FAILED after 3 retries — Constituency: {db_name} "
                    f"(ID: {db_c['id']}): {e}",
                    exc_info=True
                )
            
            # Polite delay between constituencies
            await asyncio.sleep(2)
        
        await browser.close()
    
    logger.info("MyNeta scraping pipeline complete.")

if __name__ == '__main__':
    asyncio.run(main())
