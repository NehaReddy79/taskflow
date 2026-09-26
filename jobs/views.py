from django.shortcuts import render
from rest_framework import generics 
from rest_framework.response import Response
from .models import Job
from .serializers import JobSerializer
import time
from .redis_client import redis_client


class JobListCreateView(generics.ListCreateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    def create(self, request , *args , **kwargs):
        
        data = request.data.copy()
        if data.get('idempotency_key') == "":
            data['idempotency_key'] = None

        idempotency_key  = data.get('idempotency_key')

        if idempotency_key: 
            job = Job.objects.filter(idempotency_key=idempotency_key).first()
            if job:
                serializer = JobSerializer(job)
                return Response(serializer.data , status=200)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        job_id = serializer.data['id']
        priority = serializer.data['priority']

        score = (priority * 10**13) + time.time() 
        """
            Both priority and time are used bcoz if priority is same then 
            time can be the differentiating factor and vice versa.
            Also 10**13 is used so even minor value differences can change the order 
            strongly.
        """
        redis_client.zadd("job_queue" , {str(job_id) : score})
        return Response(serializer.data , status=201 )

class JobDetailView(generics.RetrieveAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    lookup_field = 'pk'