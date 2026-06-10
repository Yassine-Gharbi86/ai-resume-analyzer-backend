from django.contrib import admin
from .models import Resume, JobMatch

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display  = ['original_name', 'analysis_status', 'ats_score', 'file_size_kb', 'uploaded_at']
    list_filter   = ['analysis_status']
    readonly_fields = ['uploaded_at', 'analyzed_at']
    ordering      = ['-uploaded_at']

@admin.register(JobMatch)
class JobMatchAdmin(admin.ModelAdmin):
    list_display  = ['resume', 'job_title', 'company', 'match_score', 'match_status', 'created_at']
    list_filter   = ['match_status']
    readonly_fields = ['created_at', 'matched_at']
    ordering      = ['-created_at']
