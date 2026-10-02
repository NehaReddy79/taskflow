from rest_framework.test import APITestCase
from .models import Job
from django.utils import timezone
from datetime import timedelta
from jobs.queue import enqueue_job
from .redis_client import redis_client

class JobIdempotencyTests(APITestCase):
    def test_duplicate_idempotency_key(self):
        data = {
            "job_type" : "send_email",
            "payload" : {"to" : "user1"},
            "priority" : 1,
            "idempotency_key" : "abcd",
            "max_retries" : 5
        }
        response  = self.client.post("/jobs/" , data , format='json')
        self.assertEqual(response.status_code, 201)
        job_id = response.data['id']

        response2  = self.client.post("/jobs/" , data , format='json')
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(job_id , response2.data['id'])
        self.assertEqual(Job.objects.count() , 1)

class JobClaimRaceSafetyTests(APITestCase):
    def test_race_safety(self):
        job = Job.objects.create(job_type="send_email",payload={"to": "user1"},priority=1,status="PENDING",)

        claim_a = Job.objects.filter(id = job.id , status__in=["PENDING" , "RETRYING"]).update(
            status="RUNNING" , locked_by="worker_A",lease_expires_at=timezone.now() + timedelta(seconds=30))

        claim_b = Job.objects.filter(id = job.id , status__in=["PENDING" , "RETRYING"]).update(
            status="RUNNING" , locked_by="worker_B",lease_expires_at=timezone.now() + timedelta(seconds=30))

        self.assertEqual(claim_a, 1)
        self.assertEqual(claim_b, 0)
        job.refresh_from_db()
        self.assertEqual(job.locked_by , "worker_A")

class JobDeadTests(APITestCase):
    def test_max_retries_to_dead(self):
        job = Job.objects.create(job_type = "send_email" ,payload={"to": "user1"},priority=1,status="RUNNING", attempt_count=3 , max_retries= 3 )
        dead_job = Job.objects.filter(id = job.id , status='RUNNING').update(status="DEAD" , locked_by=None , lease_expires_at = None)
        
        self.assertEqual(dead_job , 1)
        job.refresh_from_db()
        self.assertEqual(job.status, "DEAD")

class JobPriorityTests(APITestCase):
    def test_priority_check(self):
        try:

            job1 = Job.objects.create(job_type="send_email",payload={"to": "user1"},priority=1,status="PENDING",)
            job2 = Job.objects.create(job_type="send_email",payload={"to": "user1"},priority=5,status="PENDING",)

            enqueue_job(job1)
            enqueue_job(job2)

            score1 = redis_client.zscore("job_queue" , str(job1.id))
            score2 = redis_client.zscore("job_queue" , str(job2.id))

            self.assertLess(score1 , score2)
        finally : 
            redis_client.zrem("job_queue" , str(job1.id))
            redis_client.zrem("job_queue" , str(job2.id))

class JobMaxRetriesTest(APITestCase):
    def test_validate_max_retries(self):
        data = {
                    "job_type" : "send_email",
                    "payload" : {"to" : "user1"},
                    "priority" : 1,
                    "idempotency_key" : "abcd",
                    "max_retries" : 15
                }
        response  = self.client.post("/jobs/" , data , format='json')

        self.assertEqual(response.status_code , 400)
        self.assertEqual(Job.objects.count() , 0)