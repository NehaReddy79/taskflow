import time
from jobs.models import Job
from jobs.redis_client import redis_client
from django.core.management import BaseCommand
import os , socket
from django.db.models import F
from django.utils import timezone
from datetime import timedelta
LEASE_SECONDS = 30

class Command(BaseCommand):

    def handle(self , *args , **options):
        worker_id = f"{socket.gethostname()}-{os.getpid()}"
        while True:
           
            jobs = redis_client.zpopmin("job_queue")
            if jobs : 
                job_id , score = jobs[0]
                job_con = Job.objects.filter(id=job_id , status__in = ['PENDING' , 'RETRYING']).update(status='RUNNING' , 
                                                                                                        locked_by=worker_id , lease_expires_at=timezone.now() + timedelta(seconds = LEASE_SECONDS) , attempt_count=F('attempt_count') + 1)
                
                if job_con == 0 : 
                    print("Skipped , already claimed")
                    continue

                job_det = Job.objects.filter(id = job_id).first()
                print(f"{job_det.job_type} , {job_det.payload} , {job_det.pk}")

            else : 
                time.sleep(2)