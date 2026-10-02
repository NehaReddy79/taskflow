from rest_framework.test import APITestCase
from .models import Job

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