"""
VoteSmart TN — API Views

Endpoints:
  POST /api/moral-match/           → Moral alignment scoring
  GET  /api/reality-predict/<id>/  → Win probability prediction
  GET  /api/constituencies/        → All 234 constituencies
  GET  /api/candidates/<id>/       → Candidates for a constituency
"""
import os
import logging
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response
from rest_framework import status
from supabase import create_client, Client

from ml.moral_matcher import MoralMatcher
from ml.reality_predictor import RealityPredictor
from ml.feature_engineer import compute_features

logger = logging.getLogger('api')

# ─── Supabase Client (singleton) ─────────────────────────────
def get_supabase() -> Client:
    """Create and return Supabase client using service key for full access."""
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    return create_client(url, key)


# ─── Lazy-loaded ML singletons ───────────────────────────────
_moral_matcher = None
_reality_predictor = None


def get_moral_matcher() -> MoralMatcher:
    global _moral_matcher
    if _moral_matcher is None:
        _moral_matcher = MoralMatcher()
    return _moral_matcher


def get_reality_predictor() -> RealityPredictor:
    global _reality_predictor
    if _reality_predictor is None:
        _reality_predictor = RealityPredictor()
    return _reality_predictor


# ─── Endpoints ────────────────────────────────────────────────

@api_view(['POST'])
def moral_match(request):
    """
    Moral alignment scoring.
    
    Body: { "constituency_id": int, "moral_input": str }
    Returns: { "top3": [{ "candidate": {...}, "score": float, "explanation": str }] }
    """
    constituency_id = request.data.get('constituency_id')
    moral_input = request.data.get('moral_input', '')

    if not constituency_id:
        return Response(
            {'error': 'constituency_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not moral_input or len(moral_input.strip()) < 5:
        return Response(
            {'error': 'moral_input must be at least 5 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        supabase = get_supabase()
        gemini_key = os.environ.get('GEMINI_API_KEY')

        # 1. Fetch candidates for this constituency
        result = supabase.table('candidates') \
            .select('*') \
            .eq('constituency_id', constituency_id) \
            .limit(6) \
            .execute()
        
        candidates = result.data
        if not candidates:
            return Response(
                {'error': 'No candidates found for this constituency'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. Fetch news article key_claims for each candidate
        for candidate in candidates:
            news_result = supabase.table('news_articles') \
                .select('headline, sentiment_score') \
                .eq('candidate_id', candidate['id']) \
                .eq('is_factual', True) \
                .order('published_at', desc=True) \
                .limit(5) \
                .execute()
            candidate['news_articles'] = news_result.data or []

        # 3. Run MoralMatcher scoring
        matcher = get_moral_matcher()
        scored = matcher.score(moral_input, candidates)

        # 4. Get Gemini explanations for top 3
        top3 = []
        for entry in scored[:3]:
            explanation = matcher.get_explanation(
                moral_input, entry['candidate'], gemini_key
            )
            top3.append({
                'candidate': {
                    'id': entry['candidate']['id'],
                    'name': entry['candidate']['name'],
                    'party': entry['candidate']['party'],
                    'alliance': entry['candidate'].get('alliance'),
                    'criminal_cases': entry['candidate'].get('criminal_cases', 0),
                    'asset_value_current': entry['candidate'].get('asset_value_current'),
                    'asset_value_previous': entry['candidate'].get('asset_value_previous'),
                    'education': entry['candidate'].get('education'),
                    'age': entry['candidate'].get('age'),
                },
                'score': round(entry['score'], 4),
                'explanation': explanation,
            })

        return Response({'top3': top3})

    except Exception as e:
        logger.error(f"Moral match error: {e}", exc_info=True)
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def reality_predict(request, constituency_id):
    """
    Win probability prediction for a constituency.
    
    Returns: { "predictions": [{ "candidate": {...}, "vote_share": float, "rank": int, "confidence": float }] }
    """
    try:
        supabase = get_supabase()
        predictor = get_reality_predictor()

        predictions = predictor.predict_constituency(constituency_id, supabase)

        if not predictions:
            return Response(
                {'error': 'No predictions available — candidates or features may be missing'},
                status=status.HTTP_404_NOT_FOUND
            )

        response_data = []
        for pred in predictions:
            response_data.append({
                'candidate': {
                    'id': pred['candidate']['id'],
                    'name': pred['candidate']['name'],
                    'party': pred['candidate']['party'],
                    'alliance': pred['candidate'].get('alliance'),
                    'is_incumbent': pred['candidate'].get('is_incumbent', False),
                    'criminal_cases': pred['candidate'].get('criminal_cases', 0),
                    'asset_value_current': pred['candidate'].get('asset_value_current'),
                    'asset_value_previous': pred['candidate'].get('asset_value_previous'),
                    'age': pred['candidate'].get('age'),
                },
                'predicted_vote_share': round(pred['predicted_vote_share'], 4),
                'predicted_rank': pred['predicted_rank'],
                'confidence_score': round(pred.get('confidence_score', 0.5), 4),
                'anti_incumbency_score': pred.get('anti_incumbency_score'),
            })

        return Response({'predictions': response_data})

    except FileNotFoundError:
        return Response(
            {'error': 'XGBoost model not found. Run training script first.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        logger.error(f"Reality predict error: {e}", exc_info=True)
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def constituency_list(request):
    """
    Return all 234 constituencies grouped by district.
    
    Query params:
      ?search=<name> — filter by constituency name
      ?district=<name> — filter by district name
    """
    try:
        supabase = get_supabase()
        
        query = supabase.table('constituencies').select('*')
        
        # Optional filters
        search = request.query_params.get('search')
        district = request.query_params.get('district')
        
        if search:
            query = query.ilike('name', f'%{search}%')
        if district:
            query = query.eq('district', district)
        
        result = query.order('district').order('name').execute()
        constituencies = result.data or []

        # Group by district
        grouped = {}
        for c in constituencies:
            dist = c['district']
            if dist not in grouped:
                grouped[dist] = []
            grouped[dist].append({
                'id': c['id'],
                'name': c['name'],
                'district': c['district'],
                'total_voters': c.get('total_voters'),
            })

        return Response({
            'total': len(constituencies),
            'districts': grouped,
        })

    except Exception as e:
        logger.error(f"Constituency list error: {e}", exc_info=True)
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def candidates_for_constituency(request, constituency_id):
    """
    Return all candidates for a given constituency with their ML features.
    """
    try:
        supabase = get_supabase()
        
        # Fetch candidates
        result = supabase.table('candidates') \
            .select('*') \
            .eq('constituency_id', constituency_id) \
            .execute()
        
        candidates = result.data or []
        
        # Enrich with ML features
        for candidate in candidates:
            features_result = supabase.table('ml_features') \
                .select('*') \
                .eq('candidate_id', candidate['id']) \
                .limit(1) \
                .execute()
            candidate['ml_features'] = features_result.data[0] if features_result.data else None
            
            # Fetch recent news
            news_result = supabase.table('news_articles') \
                .select('headline, source, sentiment_score, published_at, url') \
                .eq('candidate_id', candidate['id']) \
                .eq('is_factual', True) \
                .order('published_at', desc=True) \
                .limit(5) \
                .execute()
            candidate['recent_news'] = news_result.data or []

        return Response({'candidates': candidates})

    except Exception as e:
        logger.error(f"Candidates fetch error: {e}", exc_info=True)
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
