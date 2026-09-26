from django.db import models
from django.utils.translation import gettext_lazy as _

class Job(models.Model):
    class Status(models.TextChoices):
            PENDING = "PENDING" , _("Pending")
            RUNNING = "RUNNING" , _("Running")
            SUCCESS = "SUCCESS" , _("Success")
            FAILED = "FAILED" , _("Failed")
            RETRYING = "RETRYING" , _("Retrying")
            DEAD = "DEAD" , _("Dead")
    job_type = models.CharField(max_length=100)
    payload = models.JSONField(null=False)
    status = models.CharField(choices=Status.choices , default=Status.PENDING , max_length=20)
    priority = models.IntegerField()
    idempotency_key = models.CharField(null=True  , unique=True, max_length=225 , blank=True)
    locked_by = models.CharField(null=True , max_length=100 )
    lease_expires_at = models.DateTimeField(null=True)
    attempt_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job(id={self.id} , type={self.job_type} , status={self.status})"

    class Meta:
        ordering = ['-created_at']
