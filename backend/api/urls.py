"""
API URL Configuration — Phase 4.

New routes:
  POST /api/resumes/<id>/match/    — create a job match
  GET  /api/resumes/<id>/matches/  — list all matches for a resume
  GET  /api/matches/<id>/          — get a single match with full result
"""

from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Phase 1
    path('test/', views.test_connection, name='test-connection'),

    # Phase 2
    path('resumes/upload/', views.upload_resume, name='resume-upload'),
    path('resumes/', views.list_resumes, name='resume-list'),

    # Phase 3
    path('resumes/<int:resume_id>/', views.get_resume, name='resume-detail'),
    path('resumes/<int:resume_id>/analyze/', views.analyze_resume, name='resume-analyze'),

    # Phase 4
    path('resumes/<int:resume_id>/match/', views.create_job_match, name='job-match-create'),
    path('resumes/<int:resume_id>/matches/', views.list_job_matches, name='job-match-list'),
    path('matches/<int:match_id>/', views.get_job_match, name='job-match-detail'),
]
