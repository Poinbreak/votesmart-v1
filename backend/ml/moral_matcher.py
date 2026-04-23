"""
VoteSmart TN — Moral Matcher Engine

Uses a CrossEncoder (MiniLM) to score moral alignment between a voter's
stated values and each candidate's public record. Gemini provides
natural-language explanations for the top matches.
"""
import os
import logging
from typing import Optional
import google.generativeai as genai

logger = logging.getLogger('ml.moral_matcher')

# Lazy import to avoid loading heavy ML libs at module level
_cross_encoder = None


def _get_cross_encoder():
    """Lazy-load CrossEncoder to avoid startup cost when not needed."""
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder
        logger.info("Loading CrossEncoder model (ms-marco-MiniLM-L-6-v2)...")
        _cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        logger.info("CrossEncoder loaded successfully.")
    return _cross_encoder


class MoralMatcher:
    """
    Scores candidates against a voter's moral priorities using a CrossEncoder.
    
    The model computes semantic similarity between the voter's stated values
    and a document built from each candidate's public record (affidavit data,
    news claims, party positions).
    """

    def __init__(self):
        self.model = _get_cross_encoder()

    def build_candidate_document(self, candidate: dict) -> str:
        """
        Build a rich text document from candidate data for scoring.
        
        Concatenates:
        - Party and alliance info
        - Asset and criminal case data from ECI affidavit
        - Key news article headlines (factual only)
        - Education and experience info
        
        Preserves bilingual (Tamil + English) content where available.
        """
        parts = []

        # Basic identity
        parts.append(f"Candidate: {candidate.get('name', 'Unknown')}")
        parts.append(f"Party: {candidate.get('party', 'Unknown')}")
        
        alliance = candidate.get('alliance')
        if alliance:
            parts.append(f"Alliance: {alliance}")

        # Asset and integrity data
        asset_current = candidate.get('asset_value_current')
        asset_previous = candidate.get('asset_value_previous')
        if asset_current is not None:
            parts.append(f"Current declared assets: ₹{asset_current:,}")
        if asset_previous is not None and asset_current is not None:
            growth = ((asset_current - asset_previous) / max(asset_previous, 1)) * 100
            parts.append(f"Asset growth from last election: {growth:.1f}%")

        criminal_cases = candidate.get('criminal_cases', 0)
        if criminal_cases > 0:
            parts.append(f"Criminal cases pending: {criminal_cases}")
        else:
            parts.append("No criminal cases pending.")

        # Incumbency record
        if candidate.get('is_incumbent'):
            terms = candidate.get('terms_served', 1)
            parts.append(f"Incumbent MLA. Served {terms} term(s).")

        # Education
        education = candidate.get('education')
        if education:
            parts.append(f"Education: {education}")

        # Age
        age = candidate.get('age')
        if age:
            parts.append(f"Age: {age}")

        # News-based data — headlines from factual articles
        news_articles = candidate.get('news_articles', [])
        if news_articles:
            headlines = [a.get('headline', '') for a in news_articles[:5] if a.get('headline')]
            if headlines:
                parts.append("Recent verified news: " + "; ".join(headlines))

        # Affidavit processed claims
        payload = candidate.get('processed_text_payload')
        if payload and isinstance(payload, dict):
            claims = payload.get('key_claims', [])
            if claims:
                parts.append("Key claims from affidavit: " + "; ".join(claims[:5]))

        return ". ".join(parts)

    def score(self, user_moral_input: str, candidates: list) -> list:
        """
        Score each candidate against the voter's moral input.
        
        Args:
            user_moral_input: Free-text description of voter's ideal candidate
            candidates: List of candidate dicts from Supabase
            
        Returns:
            Sorted list of dicts with 'candidate' and 'score' keys,
            ordered by compatibility (highest first). Score is 0.0–1.0.
        """
        if not candidates:
            return []

        # Build (query, document) pairs for CrossEncoder
        pairs = []
        candidate_docs = []
        for candidate in candidates:
            doc = self.build_candidate_document(candidate)
            candidate_docs.append(doc)
            pairs.append((user_moral_input, doc))

        # Run CrossEncoder prediction
        raw_scores = self.model.predict(pairs)

        # Normalize scores to 0-1 range using sigmoid
        import numpy as np
        normalized = 1 / (1 + np.exp(-raw_scores))  # Sigmoid normalization

        # Build result list
        results = []
        for i, candidate in enumerate(candidates):
            results.append({
                'candidate': candidate,
                'score': float(normalized[i]),
            })

        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        return results

    def get_explanation(self, user_input: str, candidate: dict, gemini_key: str) -> str:
        """
        Generate a natural-language explanation of why this candidate
        aligns or conflicts with the voter's stated priorities.
        
        Uses Gemini 1.5 Flash for fast, bilingual explanation generation.
        
        Args:
            user_input: The voter's moral input text
            candidate: Candidate dict from Supabase
            gemini_key: Gemini API key
            
        Returns:
            3-sentence explanation string, or fallback message on error
        """
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash')

            candidate_doc = self.build_candidate_document(candidate)
            
            prompt = f"""You are an unbiased political analyst for Tamil Nadu elections.
In exactly 3 concise sentences, explain why this candidate's record aligns or conflicts 
with these voter priorities. Be specific — cite data points from the candidate record.
Use simple English that any voter can understand.

Voter priorities: {user_input}

Candidate record: {candidate_doc}

Respond in 3 sentences only. Do not use bullet points."""

            response = model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini explanation error for {candidate.get('name')}: {e}")
            candidate_name = candidate.get('name', 'This candidate')
            party = candidate.get('party', 'their party')
            return (
                f"{candidate_name} from {party} has a public record that can be "
                f"compared against your stated values. Check their asset declarations, "
                f"criminal record status, and recent news coverage for more details."
            )
