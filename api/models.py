"""
API Models — Phase 4 update.

New model: JobMatch
  Stores a job description + the AI match report for a given resume.
  It has a ForeignKey to Resume — one resume can have many job matches.
"""

from django.db import models
import os


def resume_upload_path(instance, filename):
    return os.path.join('resumes', filename)


class Resume(models.Model):
    STATUS_PENDING   = 'pending'
    STATUS_ANALYZING = 'analyzing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED    = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING,   'Pending'),
        (STATUS_ANALYZING, 'Analyzing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED,    'Failed'),
    ]

    original_name    = models.CharField(max_length=255)
    file             = models.FileField(upload_to=resume_upload_path)
    file_size        = models.PositiveIntegerField()
    uploaded_at      = models.DateTimeField(auto_now_add=True)
    analysis_status  = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    analysis         = models.JSONField(null=True, blank=True)
    analysis_error   = models.TextField(null=True, blank=True)
    analyzed_at      = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_name} [{self.analysis_status}]"

    @property
    def file_size_kb(self):
        return round(self.file_size / 1024, 1)

    @property
    def ats_score(self):
        if self.analysis:
            return self.analysis.get('ats_score')
        return None


class JobMatch(models.Model):
    """
    Stores one job-match request: a resume × job description → AI report.

    ForeignKey:
      Each JobMatch belongs to exactly one Resume.
      resume.job_matches.all() gives all matches for a resume.
      on_delete=CASCADE means if the Resume is deleted, its JobMatches
      are deleted too — no orphaned records.
    """

    STATUS_PENDING  = 'pending'
    STATUS_MATCHING = 'matching'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED   = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING,   'Pending'),
        (STATUS_MATCHING,  'Matching'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED,    'Failed'),
    ]

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name='job_matches',
        help_text="The resume this match is against"
    )

    job_description = models.TextField(
        help_text="Raw job posting text pasted by the user"
    )

    # Detected from the JD by the AI — makes the UI nicer
    job_title = models.CharField(max_length=255, blank=True, default='')
    company   = models.CharField(max_length=255, blank=True, default='')

    match_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    match_result = models.JSONField(
        null=True,
        blank=True,
        help_text="Full AI match report stored as JSON"
    )

    match_error = models.TextField(null=True, blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    matched_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Match: {self.resume.original_name} × {self.job_title or 'Unknown Role'}"

    @property
    def match_score(self):
        if self.match_result:
            return self.match_result.get('match_score')
        return None
