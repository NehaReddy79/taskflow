import time
from jobs.models import Job
from jobs.redis_client import redis_client
from django.core.management import BaseCommand
import os , socket
from django.db.models import F
from django.utils import timezone
from datetime import timedelta
from jobs.queue import enqueue_job
LEASE_SECONDS = 30
REAPER_INTERVAL = 10
PENDING_SECONDS = 60

class Command(BaseCommand):

    def handle(self , *args , **options):
        worker_id = f"{socket.gethostname()}-{os.getpid()}"
        last_reap = 0
        while True:
           
            if time.time() - last_reap >= REAPER_INTERVAL :
                self.reap_stale_jobs()
                last_reap  = time.time()
            jobs = redis_client.zpopmin("job_queue")
            if jobs : 
                job_id , score = jobs[0]
                job_con = Job.objects.filter(id=job_id , status__in = ['PENDING' , 'RETRYING']).update(status='RUNNING' , 
                                                                                                        locked_by=worker_id , lease_expires_at=timezone.now() + timedelta(seconds = LEASE_SECONDS) , attempt_count=F('attempt_count') + 1 , updated_at = timezone.now())
                
                if job_con == 0 : 
                    print("Skipped , already claimed")
                    continue

                job_det = Job.objects.filter(id = job_id).first()
                print(f"{job_det.job_type} , {job_det.payload} , {job_det.pk}")

            else : 
                time.sleep(2)

    def reap_stale_jobs(self):

        
        stale_jobs = Job.objects.filter(status='RUNNING' , lease_expires_at__lt = timezone.now())
        for stale_job in stale_jobs:
            
            if(stale_job.attempt_count >= stale_job.max_retries):
                Job.objects.filter(id=stale_job.pk , status = 'RUNNING' , lease_expires_at__lt = timezone.now()).update(status='DEAD' , locked_by = None , lease_expires_at = None , updated_at = timezone.now())
                continue
            job_retry = Job.objects.filter(id=stale_job.pk , status='RUNNING' , lease_expires_at__lt = timezone.now()).update(status='RETRYING'  , locked_by = None , lease_expires_at = None  , updated_at=timezone.now())

            if job_retry == 1:
                enqueue_job(stale_job)

        cutoff_time = timezone.now()-timedelta(seconds=PENDING_SECONDS)
        orphans = Job.objects.filter(status__in=['PENDING', 'RETRYING'] , updated_at__lt =  cutoff_time)

        for orphan in orphans :
            job_score = redis_client.zscore("job_queue" , str(orphan.id))

            if job_score is None:
                enqueue_job(orphan)

                