from django.contrib import admin
from .models import Job

class JobAdmin(admin.ModelAdmin):
    list_display = ("id" , "job_type" , "status" , "priority" , "attempt_count" , "max_retries" , "created_at",)
    list_filter = ("status" , "job_type")
    search_fields = ("idempotency_key" , "job_type")

admin.site.register(Job , JobAdmin)