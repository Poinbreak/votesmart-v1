"""
VoteSmart TN — XGBoost Training Script

Trains an XGBRegressor to predict vote share for Tamil Nadu elections.

Features (11):
  1. local_support_ratio
  2. alliance_historical_win_share
  3. power_fatigue_score
  4. wealth_divergence_score
  5. anti_incumbency_score
  6. positive_sentiment_avg
  7. news_volume_7d
  8. criminal_cases
  9. asset_value_current_log (log-transformed)
  10. terms_served
  11. age

Target: predicted_vote_share (float, 0-1)

Usage:
  python backend/ml/train_xgboost.py
"""
import os
import sys
import logging
import math
import json
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s %(message)s')
logger = logging.getLogger('ml.train_xgboost')

# Feature column names (in order)
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


def get_supabase() -> Client:
    """Create Supabase client."""
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    return create_client(url, key)


def fetch_training_data(supabase: Client) -> pd.DataFrame:
    """
    Fetch and join data from candidates, ml_features, and predictions tables.
    Returns a DataFrame ready for training.
    """
    logger.info("Fetching training data from Supabase...")

    # Fetch candidates
    candidates_result = supabase.table('candidates').select('*').execute()
    candidates_df = pd.DataFrame(candidates_result.data or [])

    if candidates_df.empty:
        logger.warning("No candidates found in database.")
        return pd.DataFrame()

    # Fetch ML features
    features_result = supabase.table('ml_features').select('*').execute()
    features_df = pd.DataFrame(features_result.data or [])

    if features_df.empty:
        logger.warning("No ML features found. Run feature_engineer.py first.")
        return pd.DataFrame()

    # Fetch existing predictions (for re-training / supervised labels)
    predictions_result = supabase.table('predictions').select('*').execute()
    predictions_df = pd.DataFrame(predictions_result.data or [])

    # Merge candidates with features
    merged = candidates_df.merge(
        features_df,
        left_on='id',
        right_on='candidate_id',
        how='inner',
        suffixes=('', '_feat')
    )

    # Add log-transformed asset value
    merged['asset_value_current_log'] = merged['asset_value_current'].apply(
        lambda x: math.log1p(x) if x and x > 0 else 0.0
    )

    # Fill missing values
    merged['criminal_cases'] = merged['criminal_cases'].fillna(0)
    merged['terms_served'] = merged['terms_served'].fillna(0)
    merged['age'] = merged['age'].fillna(45)  # Default median age
    merged['news_volume_7d'] = merged['news_volume_7d'].fillna(0)

    # If we have prior predictions, use them as labels for re-training
    if not predictions_df.empty:
        merged = merged.merge(
            predictions_df[['candidate_id', 'predicted_vote_share']],
            left_on='id',
            right_on='candidate_id',
            how='left',
            suffixes=('', '_pred')
        )
        merged['target'] = merged['predicted_vote_share']
    else:
        # Generate synthetic targets based on alliance win share + noise
        # This allows training even without prior predictions
        logger.info("No prior predictions found. Generating synthetic targets.")
        np.random.seed(42)
        base = merged['alliance_historical_win_share'].values
        noise = np.random.normal(0, 0.05, len(merged))
        merged['target'] = np.clip(base + noise, 0.01, 0.95)

    # Drop rows with NaN targets
    merged = merged.dropna(subset=['target'])

    logger.info(f"Training data shape: {merged.shape}")
    return merged


def train_model(df: pd.DataFrame) -> xgb.XGBRegressor:
    """
    Train XGBRegressor with 5-fold cross-validation.
    
    Returns the trained model.
    """
    # Prepare feature matrix and target
    X = df[FEATURE_COLUMNS].values.astype(np.float32)
    y = df['target'].values.astype(np.float32)

    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Target range: [{y.min():.4f}, {y.max():.4f}]")

    # Configure model
    model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        objective='reg:squarederror',
        eval_metric='rmse',
        n_jobs=-1,
    )

    # 5-fold cross-validation
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(
        model, X, y,
        cv=kf,
        scoring='neg_mean_squared_error',
        n_jobs=-1,
    )
    
    rmse_scores = np.sqrt(-cv_scores)
    logger.info(f"5-Fold CV RMSE: {rmse_scores.mean():.4f} ± {rmse_scores.std():.4f}")
    logger.info(f"Per-fold RMSE: {[f'{s:.4f}' for s in rmse_scores]}")

    # Train final model on all data
    model.fit(X, y, verbose=False)

    # Feature importance
    importance = model.feature_importances_
    for fname, imp in sorted(zip(FEATURE_COLUMNS, importance), key=lambda x: -x[1]):
        logger.info(f"  Feature '{fname}': importance = {imp:.4f}")

    # Final metrics on training set (not CV — just diagnostic)
    y_pred = model.predict(X)
    train_rmse = np.sqrt(mean_squared_error(y, y_pred))
    train_mae = mean_absolute_error(y, y_pred)
    train_r2 = r2_score(y, y_pred)
    logger.info(f"Training RMSE: {train_rmse:.4f}, MAE: {train_mae:.4f}, R²: {train_r2:.4f}")

    return model


def save_model(model: xgb.XGBRegressor, path: str = MODEL_PATH):
    """Save trained model to JSON."""
    model.save_model(path)
    logger.info(f"Model saved to {path}")


def main():
    """Full training pipeline."""
    # Load environment
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    load_dotenv(env_path)

    supabase = get_supabase()

    # Fetch data
    df = fetch_training_data(supabase)
    if df.empty or len(df) < 10:
        logger.error(f"Insufficient training data ({len(df)} rows). Need at least 10.")
        logger.info("Make sure to run scrapers and feature_engineer.py first.")
        sys.exit(1)

    # Train
    model = train_model(df)

    # Save
    save_model(model)

    # Write predictions back to Supabase for all candidates
    logger.info("Writing predictions back to Supabase...")
    from ml.reality_predictor import RealityPredictor
    predictor = RealityPredictor()

    constituencies_result = supabase.table('constituencies').select('id').execute()
    for constituency in (constituencies_result.data or []):
        try:
            predictor.predict_constituency(constituency['id'], supabase, write_db=True)
        except Exception as e:
            logger.error(f"Prediction failed for constituency {constituency['id']}: {e}")

    logger.info("Training pipeline complete.")


if __name__ == '__main__':
    main()
