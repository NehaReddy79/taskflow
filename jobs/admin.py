from django.contrib import admin
from .models import Job
from .queue import enqueue_job
class JobAdmin(admin.ModelAdmin):
    list_display = ("id" , "job_type" , "status" , "priority" , "attempt_count" , "max_retries" , "created_at",)
    list_filter = ("status" , "job_type")
    search_fields = ("idempotency_key" , "job_type")
    actions = ['retry_dead_jobs']
    def retry_dead_jobs(self , request , queryset):
        dead_jobs = queryset.filter(status='DEAD')
        skipped = queryset.exclude(status='DEAD').count()
        cnt = 0
        for job in dead_jobs:
            job.status = 'RETRYING'
            job.locked_by = None
            job.attempt_count = 0
            job.lease_expires_at = None
            job.save()
            enqueue_job(job)
            cnt += 1
        self.message_user(request , f"Retried {cnt} jobs. Skipped {skipped} job(s)")
    retry_dead_jobs.short_description = "Retry selected dead jobs"

admin.site.register(Job , JobAdmin)