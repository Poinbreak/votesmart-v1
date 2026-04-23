import os
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s %(message)s')
logger = logging.getLogger('ml.pipeline')

from dotenv import load_dotenv
load_dotenv('../../.env')

from supabase import create_client
from feature_engineer import compute_all_features
from reality_predictor import RealityPredictor

def run_pipeline():
    logger.info("Initializing Supabase client...")
    supabase = create_client(os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY'))
    
    logger.info("=== STEP 1: Feature Engineering ===")
    compute_all_features(supabase)
    
    logger.info("=== STEP 2: Predictions ===")
    predictor = RealityPredictor()
    
    constituencies = supabase.table('constituencies').select('id, name').execute().data or []
    logger.info(f"Predicting for {len(constituencies)} constituencies...")
    
    for c in constituencies:
        logger.info(f"Predicting constituency: {c['name']} ({c['id']})")
        predictor.predict_constituency(c['id'], supabase, write_db=True)
        
    logger.info("=== ML PIPELINE COMPLETE ===")

if __name__ == '__main__':
    run_pipeline()
