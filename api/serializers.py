"""
API Serializers — Phase 4 update.

Added: JobMatchSerializer for the new JobMatch model.
"""

from rest_framework import serializers
from .models import Resume, JobMatch


class ResumeSerializer(serializers.ModelSerializer):
    file_size_kb = serializers.ReadOnlyField()
    ats_score    = serializers.ReadOnlyField()

    class Meta:
        model  = Resume
        fields = [
            'id', 'original_name', 'file', 'file_size', 'file_size_kb',
            'uploaded_at', 'analysis_status', 'analysis', 'analysis_error',
            'analyzed_at', 'ats_score',
        ]
        read_only_fields = [
            'id', 'uploaded_at', 'file_size_kb', 'analysis_status',
            'analysis', 'analysis_error', 'analyzed_at', 'ats_score',
        ]


class ResumeListSerializer(serializers.ModelSerializer):
    file_size_kb = serializers.ReadOnlyField()
    ats_score    = serializers.ReadOnlyField()

    class Meta:
        model  = Resume
        fields = ['id', 'original_name', 'file_size_kb', 'uploaded_at', 'analysis_status', 'ats_score']


class JobMatchSerializer(serializers.ModelSerializer):
    """
    Serializer for JobMatch.

    match_score is a @property on the model so we declare it as ReadOnlyField.
    We exclude job_description from the list output to keep responses small.
    """
    match_score = serializers.ReadOnlyField()

    class Meta:
        model  = JobMatch
        fields = [
            'id', 'resume', 'job_description', 'job_title', 'company',
            'match_status', 'match_result', 'match_error',
            'created_at', 'matched_at', 'match_score',
        ]
        read_only_fields = [
            'id', 'resume', 'job_title', 'company', 'match_status',
            'match_result', 'match_error', 'created_at', 'matched_at', 'match_score',
        ]


class JobMatchListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing matches — omits full result JSON."""
    match_score = serializers.ReadOnlyField()

    class Meta:
        model  = JobMatch
        fields = ['id', 'job_title', 'company', 'match_status', 'match_score', 'created_at']
