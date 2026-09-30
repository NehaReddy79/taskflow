from .models import Job
from .redis_client import redis_client
import time

def enqueue_job(job , delay_seconds = 0):
    if delay_seconds : 
        timestamp = time.time() + delay_seconds
    else:
        timestamp = job.created_at.timestamp()
    score = job.priority * 10**13 + timestamp
    redis_client.zadd("job_queue" , {str(job.id) : score})