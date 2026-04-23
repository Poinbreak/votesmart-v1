"""
VoteSmart TN — Reality Predictor (XGBoost Inference)

Loads a trained XGBoost model and predicts vote share for all candidates
in a given constituency. Uses softmax normalization to ensure vote shares
sum to approximately 1.0.
"""
import os
import math
import logging
import numpy as np
import xgboost as xgb
from supabase import Client

logger = logging.getLogger('ml.reality_predictor')

# Feature column names — must match training order exactly
FEATURE_COLUMNS = [
    'local_support_ratio',
    'alliance_historical_win_share',
    'power_fatigue_score',
    'wealth_divergence_score',
    'anti_incumbency_score',
    'positive_sentiment_avg',
    'news_volume_7d',
    'criminal_cases',
    'asset_value_current_log',
    'terms_served',
    'age',
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'xgboost_model.json')
MODEL_VERSION = 'v1.0-xgb300'


class RealityPredictor:
    """
    Predicts election outcomes using a trained XGBoost model.
    
    For each constituency, produces:
    - Predicted vote share per candidate (softmax-normalized)
    - Predicted rank (1 = predicted winner)
    - Confidence score based on margin between top-2
    """

    def __init__(self, model_path: str = MODEL_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"XGBoost model not found at {model_path}. "
                f"Run 'python backend/ml/train_xgboost.py' first."
            )
        self.model = xgb.XGBRegressor()
        self.model.load_model(model_path)
        logger.info(f"XGBoost model loaded from {model_path}")

    def _build_feature_vector(self, candidate: dict, features: dict) -> list:
        """
        Build a single feature vector for a candidate.
        
        Args:
            candidate: Row from candidates table
            features: Row from ml_features table (or empty dict)
            
        Returns:
            List of 11 float values in FEATURE_COLUMNS order
        """
        asset_current = candidate.get('asset_value_current') or 0
        
        return [
            float(features.get('local_support_ratio', 0.0) or 0.0),
            float(features.get('alliance_historical_win_share', 0.02) or 0.02),
            float(features.get('power_fatigue_score', 0.0) or 0.0),
            float(features.get('wealth_divergence_score', 0.0) or 0.0),
            float(features.get('anti_incumbency_score', 0.0) or 0.0),
            float(features.get('positive_sentiment_avg', 0.0) or 0.0),
            int(features.get('news_volume_7d', 0) or 0),
            int(candidate.get('criminal_cases', 0) or 0),
            math.log1p(asset_current) if asset_current > 0 else 0.0,
            int(candidate.get('terms_served', 0) or 0),
            int(candidate.get('age', 45) or 45),
        ]

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax normalization so vote shares sum to ~1.0."""
        exp_x = np.exp(x - np.max(x))  # Subtract max for numerical stability
        return exp_x / exp_x.sum()

    def predict_constituency(
        self,
        constituency_id: int,
        supabase: Client,
        write_db: bool = False,
    ) -> list:
        """
        Predict vote share for all candidates in a constituency.
        
        Args:
            constituency_id: ID from constituencies table
            supabase: Supabase client instance
            write_db: If True, upsert predictions to Supabase predictions table
            
        Returns:
            Sorted list of dicts:
            [{
                'candidate': {candidate data},
                'predicted_vote_share': float,
                'predicted_rank': int,
                'confidence_score': float,
                'anti_incumbency_score': float,
            }]
        """
        # Fetch candidates for this constituency
        candidates_result = supabase.table('candidates') \
            .select('*') \
            .eq('constituency_id', constituency_id) \
            .execute()
        
        candidates = candidates_result.data or []
        if not candidates:
            logger.warning(f"No candidates found for constituency {constituency_id}")
            return []

        # Fetch ML features for each candidate
        feature_vectors = []
        candidate_features = []
        for candidate in candidates:
            features_result = supabase.table('ml_features') \
                .select('*') \
                .eq('candidate_id', candidate['id']) \
                .limit(1) \
                .execute()
            
            features = features_result.data[0] if features_result.data else {}
            candidate_features.append(features)
            feature_vectors.append(self._build_feature_vector(candidate, features))

        # Build feature matrix
        X = np.array(feature_vectors, dtype=np.float32)
        
        # Predict raw scores
        raw_scores = self.model.predict(X)
        
        # Softmax normalize to get vote shares
        vote_shares = self._softmax(raw_scores)

        # Build results
        results = []
        for i, candidate in enumerate(candidates):
            results.append({
                'candidate': candidate,
                'predicted_vote_share': float(vote_shares[i]),
                'raw_score': float(raw_scores[i]),
                'anti_incumbency_score': candidate_features[i].get('anti_incumbency_score'),
            })

        # Sort by vote share descending
        results.sort(key=lambda x: x['predicted_vote_share'], reverse=True)

        # Assign ranks and compute confidence
        top_margin = 0.0
        if len(results) >= 2:
            top_margin = results[0]['predicted_vote_share'] - results[1]['predicted_vote_share']
        
        confidence_score = min(top_margin * 5.0, 1.0)  # Scale margin to [0, 1]

        for rank, result in enumerate(results, start=1):
            result['predicted_rank'] = rank
            result['confidence_score'] = confidence_score if rank == 1 else max(0.1, 1.0 - (rank * 0.15))

        # Write to database if requested
        if write_db:
            for result in results:
                try:
                    supabase.table('predictions').upsert({
                        'constituency_id': constituency_id,
                        'candidate_id': result['candidate']['id'],
                        'predicted_vote_share': result['predicted_vote_share'],
                        'predicted_rank': result['predicted_rank'],
                        'confidence_score': result['confidence_score'],
                        'model_version': MODEL_VERSION,
                    }, on_conflict='candidate_id').execute()
                except Exception as e:
                    logger.error(f"Failed to write prediction for candidate {result['candidate']['id']}: {e}")

        # Remove raw_score from response
        for result in results:
            del result['raw_score']

        return results
