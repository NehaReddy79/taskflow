from .models import Job
from .redis_client import redis_client

def enqueue_job(job):
    score = job.priority * 10**13 + job.created_at.timestamp()
    redis_client.zadd("job_queue" , {str(job.id) : score})