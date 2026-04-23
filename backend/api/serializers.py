"""
VoteSmart TN — DRF Serializers

These serializers are used for input validation on API endpoints.
Data is stored/retrieved via Supabase client (not Django ORM).
"""
from rest_framework import serializers


class MoralMatchInputSerializer(serializers.Serializer):
    """Validates input for the moral match endpoint."""
    constituency_id = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text="ID of the target constituency (1-234)"
    )
    moral_input = serializers.CharField(
        required=True,
        min_length=5,
        max_length=2000,
        help_text="Free-text description of voter's ideal candidate values"
    )


class CandidateSerializer(serializers.Serializer):
    """Serializes candidate data for API responses."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    party = serializers.CharField()
    alliance = serializers.CharField(allow_null=True)
    is_incumbent = serializers.BooleanField(default=False)
    terms_served = serializers.IntegerField(default=0)
    criminal_cases = serializers.IntegerField(default=0)
    asset_value_current = serializers.IntegerField(allow_null=True)
    asset_value_previous = serializers.IntegerField(allow_null=True)
    education = serializers.CharField(allow_null=True)
    age = serializers.IntegerField(allow_null=True)


class MoralMatchResultSerializer(serializers.Serializer):
    """Serializes a single moral match result."""
    candidate = CandidateSerializer()
    score = serializers.FloatField()
    explanation = serializers.CharField()


class PredictionSerializer(serializers.Serializer):
    """Serializes a prediction result."""
    candidate = CandidateSerializer()
    predicted_vote_share = serializers.FloatField()
    predicted_rank = serializers.IntegerField()
    confidence_score = serializers.FloatField()
    anti_incumbency_score = serializers.FloatField(allow_null=True)


class ConstituencySerializer(serializers.Serializer):
    """Serializes constituency data."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    district = serializers.CharField()
    total_voters = serializers.IntegerField(allow_null=True)
