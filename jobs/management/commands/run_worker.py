import time
from jobs.models import Job
from jobs.redis_client import redis_client
from django.core.management import BaseCommand

class Command(BaseCommand):

    def handle(self , *args , **options):
        while True:
            jobs = redis_client.zpopmin("job_queue")
            if jobs : 
                job_id , score = jobs[0]

                job_det = Job.objects.filter(id = job_id).first()
                print(f"{job_det.job_type} , {job_det.payload} , {job_det.pk}")

            else : 
                time.sleep(2)