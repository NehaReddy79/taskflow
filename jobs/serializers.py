from rest_framework import serializers
from .models import Job

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields =['status' , 'locked_by' , 'lease_expires_at',
                           'attempt_count' , 'created_at' , 'updated_at' ,
                           'id'
                           ]

    def validate_max_retries(self , value):
        if value < 0 or value > 10 :
            raise serializers.ValidationError("max retries must be between 0 to 10")
        return value