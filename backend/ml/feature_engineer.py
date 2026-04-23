"""
VoteSmart TN — Feature Engineer

Computes ML features for each candidate from raw data:
- Anti-incumbency score (1+3 formula)
- Local support ratio
- Alliance historical win share
- Wealth divergence score
- Sentiment averages

Results are upserted into the ml_features table nightly.
"""
import os
import logging
import math
from supabase import create_client, Client

logger = logging.getLogger('ml.feature_engineer')

# ─── Tamil Nadu Political Constants ──────────────────────────
# Current ruling party (update per election cycle)
CURRENT_RULING_PARTY = 'DMK'

# Historical alliance win share for Tamil Nadu (approximate from 2006-2021 data)
ALLIANCE_WIN_SHARE = {
    'DMK+': 0.52,
    'DMK': 0.52,
    'INDIA': 0.52,
    'DMK-INDIA': 0.52,
    'AIADMK+': 0.35,
    'AIADMK': 0.35,
    'NDA': 0.08,
    'BJP': 0.08,
    'NTK': 0.03,
    'MNM': 0.02,
    'Independent': 0.02,
    'PMK': 0.05,
    'DMDK': 0.03,
}


def get_supabase() -> Client:
    """Create Supabase client."""
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    return create_client(url, key)


def query_avg_sentiment(candidate_id: int, supabase: Client) -> float:
    """
    Compute average sentiment score from factual news articles for a candidate.
    Returns 0.0 if no articles found.
    """
    try:
        result = supabase.table('news_articles') \
            .select('sentiment_score') \
            .eq('candidate_id', candidate_id) \
            .eq('is_factual', True) \
            .not_.is_('sentiment_score', 'null') \
            .execute()
        
        articles = result.data or []
        if not articles:
            return 0.0
        
        scores = [a['sentiment_score'] for a in articles if a.get('sentiment_score') is not None]
        if not scores:
            return 0.0
        
        return sum(scores) / len(scores)
    
    except Exception as e:
        logger.error(f"Error querying sentiment for candidate {candidate_id}: {e}")
        return 0.0


def query_news_volume_7d(candidate_id: int, supabase: Client) -> int:
    """Count factual news articles from the last 7 days."""
    try:
        from datetime import datetime, timedelta
        seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        result = supabase.table('news_articles') \
            .select('id', count='exact') \
            .eq('candidate_id', candidate_id) \
            .eq('is_factual', True) \
            .gte('published_at', seven_days_ago) \
            .execute()
        
        return result.count or 0
    
    except Exception as e:
        logger.error(f"Error querying news volume for candidate {candidate_id}: {e}")
        return 0


def compute_features(candidate_id: int, supabase: Client = None) -> dict:
    """
    Compute all ML features for a single candidate.
    
    ANTI-INCUMBENCY SCORE ("1+3" formula):
      - power_fatigue: +0.2 if incumbent, +0.3 if ruling party
      - wealth_divergence: asset growth penalty when sentiment is low
      - Final: power_fatigue + (wealth_divergence * 0.5)
    
    LOCAL SUPPORT RATIO:
      - local_mentions / total_mentions from news articles
    
    ALLIANCE STRENGTH:
      - Historical win share lookup by alliance name
    
    Args:
        candidate_id: ID of the candidate in Supabase
        supabase: Optional pre-created Supabase client
        
    Returns:
        Dict matching ml_features table schema
    """
    if supabase is None:
        supabase = get_supabase()

    # ─── Fetch candidate data ────────────────────────────────
    result = supabase.table('candidates') \
        .select('*') \
        .eq('id', candidate_id) \
        .limit(1) \
        .execute()
    
    if not result.data:
        logger.error(f"Candidate {candidate_id} not found")
        return {}
    
    candidate = result.data[0]

    # ─── POWER FATIGUE ───────────────────────────────────────
    power_fatigue = 0.0
    if candidate.get('is_incumbent', False):
        power_fatigue += 0.2
    if candidate.get('party', '').upper() == CURRENT_RULING_PARTY.upper():
        power_fatigue += 0.3

    # ─── ASSET GROWTH & WEALTH DIVERGENCE ────────────────────
    asset_current = candidate.get('asset_value_current') or 0
    asset_previous = candidate.get('asset_value_previous') or 0
    
    if asset_previous > 0:
        asset_growth_pct = ((asset_current - asset_previous) / asset_previous) * 100
    else:
        asset_growth_pct = 0.0

    # Average sentiment
    avg_sentiment = query_avg_sentiment(candidate_id, supabase)
    positive_sentiment_avg = max(avg_sentiment, 0.0)

    # Wealth-to-Satisfaction Divergence
    # High growth (>100%) + low sentiment (<0.2) = high penalty
    wealth_divergence = (asset_growth_pct / 100.0) * (1.0 - max(avg_sentiment, 0.0))
    wealth_divergence = max(0.0, min(wealth_divergence, 5.0))  # Clamp to [0, 5]

    # ─── ANTI-INCUMBENCY SCORE ───────────────────────────────
    anti_incumbency_score = power_fatigue + (wealth_divergence * 0.5)

    # ─── LOCAL SUPPORT RATIO ─────────────────────────────────
    try:
        local_result = supabase.table('news_articles') \
            .select('id', count='exact') \
            .eq('candidate_id', candidate_id) \
            .eq('local_mention', True) \
            .execute()
        local_mentions = local_result.count or 0

        total_result = supabase.table('news_articles') \
            .select('id', count='exact') \
            .eq('candidate_id', candidate_id) \
            .execute()
        total_mentions = total_result.count or 0

        local_support_ratio = local_mentions / max(total_mentions, 1)
    except Exception:
        local_support_ratio = 0.0

    # ─── ALLIANCE STRENGTH ───────────────────────────────────
    alliance = candidate.get('alliance', '') or ''
    alliance_historical_win_share = ALLIANCE_WIN_SHARE.get(
        alliance, 
        ALLIANCE_WIN_SHARE.get(candidate.get('party', ''), 0.02)
    )

    # ─── NEWS VOLUME (7-day) ─────────────────────────────────
    news_volume_7d = query_news_volume_7d(candidate_id, supabase)

    # ─── BUILD FEATURES DICT ─────────────────────────────────
    features = {
        'candidate_id': candidate_id,
        'local_support_ratio': round(local_support_ratio, 4),
        'alliance_historical_win_share': round(alliance_historical_win_share, 4),
        'power_fatigue_score': round(power_fatigue, 4),
        'wealth_divergence_score': round(wealth_divergence, 4),
        'anti_incumbency_score': round(anti_incumbency_score, 4),
        'positive_sentiment_avg': round(positive_sentiment_avg, 4),
        'news_volume_7d': news_volume_7d,
    }

    # ─── UPSERT TO SUPABASE ──────────────────────────────────
    try:
        supabase.table('ml_features').upsert(
            features,
            on_conflict='candidate_id'
        ).execute()
        logger.info(f"Features upserted for candidate {candidate_id}")
    except Exception as e:
        logger.error(f"Failed to upsert features for candidate {candidate_id}: {e}")

    return features


def compute_all_features(supabase: Client = None):
    """
    Compute and upsert features for ALL candidates in the database.
    Called nightly by the cron job.
    """
    if supabase is None:
        supabase = get_supabase()

    result = supabase.table('candidates').select('id').execute()
    candidates = result.data or []

    logger.info(f"Computing features for {len(candidates)} candidates...")
    
    success_count = 0
    error_count = 0
    
    for candidate in candidates:
        try:
            compute_features(candidate['id'], supabase)
            success_count += 1
        except Exception as e:
            error_count += 1
            logger.error(f"Feature compute failed for candidate {candidate['id']}: {e}")

    logger.info(f"Feature computation complete. Success: {success_count}, Errors: {error_count}")


if __name__ == '__main__':
    """Run feature engineering for all candidates."""
    import sys
    from dotenv import load_dotenv
    
    # Load .env from project root
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    load_dotenv(env_path)
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s %(message)s')
    compute_all_features()
