"""
API Views — Phase 4 update.

New endpoints:
  POST /api/resumes/<id>/match/        — create a job match for a resume
  GET  /api/resumes/<id>/matches/      — list all matches for a resume
  GET  /api/matches/<match_id>/        — get a single match result
"""

import os
from django.utils import timezone
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from .models import Resume, JobMatch
from .serializers import ResumeSerializer, ResumeListSerializer, JobMatchSerializer, JobMatchListSerializer
from .ai_service import run_full_analysis, run_job_match


# ─────────────────────────────────────────────
# PHASE 1
# ─────────────────────────────────────────────

@api_view(['GET'])
def test_connection(request):
    return Response({"message": "Backend connected successfully", "status": "ok", "phase": 4})


# ─────────────────────────────────────────────
# PHASE 2 — Upload
# ─────────────────────────────────────────────

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = ['application/pdf']


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_resume(request):
    """POST /api/resumes/upload/"""
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if uploaded_file.content_type not in ALLOWED_CONTENT_TYPES or ext != '.pdf':
        return Response({"error": f"Only PDF files accepted."}, status=status.HTTP_400_BAD_REQUEST)

    if uploaded_file.size > MAX_FILE_SIZE:
        return Response({"error": f"File too large. Max 5 MB."}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ResumeSerializer(data={
        'original_name': uploaded_file.name,
        'file': uploaded_file,
        'file_size': uploaded_file.size,
    })
    if serializer.is_valid():
        resume = serializer.save()
        return Response({"message": "Resume uploaded successfully", "resume": ResumeSerializer(resume).data}, status=status.HTTP_201_CREATED)

    return Response({"error": "Upload failed", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def list_resumes(request):
    """GET /api/resumes/"""
    resumes = Resume.objects.all()
    return Response({"count": resumes.count(), "resumes": ResumeListSerializer(resumes, many=True).data})


@api_view(['GET'])
def get_resume(request, resume_id):
    """GET /api/resumes/<id>/"""
    try:
        resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        return Response({"error": "Resume not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(ResumeSerializer(resume).data)


# ─────────────────────────────────────────────
# PHASE 3 — AI Analysis
# ─────────────────────────────────────────────

@api_view(['POST'])
def analyze_resume(request, resume_id):
    """POST /api/resumes/<id>/analyze/"""
    try:
        resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        return Response({"error": "Resume not found."}, status=status.HTTP_404_NOT_FOUND)

    if resume.analysis_status == Resume.STATUS_ANALYZING:
        return Response({"error": "Analysis already in progress."}, status=status.HTTP_409_CONFLICT)

    resume.analysis_status = Resume.STATUS_ANALYZING
    resume.analysis_error  = None
    resume.save(update_fields=['analysis_status', 'analysis_error'])

    try:
        result = run_full_analysis(resume.file.path)
        resume.analysis        = result
        resume.analysis_status = Resume.STATUS_COMPLETED
        resume.analyzed_at     = timezone.now()
        resume.save(update_fields=['analysis', 'analysis_status', 'analyzed_at'])
        return Response({"message": "Analysis completed", "resume": ResumeSerializer(resume).data})

    except ValueError as e:
        resume.analysis_status = Resume.STATUS_FAILED
        resume.analysis_error  = str(e)
        resume.save(update_fields=['analysis_status', 'analysis_error'])
        return Response({"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    except Exception as e:
        resume.analysis_status = Resume.STATUS_FAILED
        resume.analysis_error  = str(e)
        resume.save(update_fields=['analysis_status', 'analysis_error'])
        return Response({"error": "Analysis failed.", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# PHASE 4 — Job Matching
# ─────────────────────────────────────────────

@api_view(['POST'])
def create_job_match(request, resume_id):
    """
    POST /api/resumes/<resume_id>/match/

    Request body (JSON):
      { "job_description": "<full job posting text>" }

    Flow:
      1. Look up the resume
      2. Validate job_description is present and long enough
      3. Create a JobMatch record with status='matching'
      4. Call run_job_match() from ai_service.py
      5. Save the result and return it
    """
    try:
        resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        return Response({"error": "Resume not found."}, status=status.HTTP_404_NOT_FOUND)

    # ── Validate input ────────────────────────────────────────────
    job_description = request.data.get('job_description', '').strip()
    if not job_description:
        return Response(
            {"error": "job_description is required in the request body."},
            status=status.HTTP_400_BAD_REQUEST
        )
    if len(job_description) < 50:
        return Response(
            {"error": "Job description is too short. Please paste the full job posting."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ── Create JobMatch record ────────────────────────────────────
    # We create it immediately so it has an ID we can return,
    # and so the status is visible if the request takes a while.
    job_match = JobMatch.objects.create(
        resume=resume,
        job_description=job_description,
        match_status=JobMatch.STATUS_MATCHING,
    )

    # ── Run AI match ──────────────────────────────────────────────
    try:
        result = run_job_match(resume.file.path, job_description)

        # Pull detected title/company out of the result to top-level fields
        # so they're queryable without parsing the full JSON every time.
        job_match.job_title    = result.get('job_title_detected') or ''
        job_match.company      = result.get('company_detected') or ''
        job_match.match_result = result
        job_match.match_status = JobMatch.STATUS_COMPLETED
        job_match.matched_at   = timezone.now()
        job_match.save()

        return Response(
            {
                "message": "Job match completed",
                "match": JobMatchSerializer(job_match).data,
            },
            status=status.HTTP_201_CREATED
        )

    except ValueError as e:
        job_match.match_status = JobMatch.STATUS_FAILED
        job_match.match_error  = str(e)
        job_match.save(update_fields=['match_status', 'match_error'])
        return Response({"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    except Exception as e:
        job_match.match_status = JobMatch.STATUS_FAILED
        job_match.match_error  = str(e)
        job_match.save(update_fields=['match_status', 'match_error'])
        return Response({"error": "Matching failed.", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def list_job_matches(request, resume_id):
    """GET /api/resumes/<resume_id>/matches/ — all matches for a resume"""
    try:
        resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        return Response({"error": "Resume not found."}, status=status.HTTP_404_NOT_FOUND)

    matches = resume.job_matches.all()
    return Response({
        "resume_id": resume_id,
        "count": matches.count(),
        "matches": JobMatchListSerializer(matches, many=True).data,
    })


@api_view(['GET'])
def get_job_match(request, match_id):
    """GET /api/matches/<match_id>/ — single match with full result"""
    try:
        match = JobMatch.objects.get(id=match_id)
    except JobMatch.DoesNotExist:
        return Response({"error": "Match not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(JobMatchSerializer(match).data)
