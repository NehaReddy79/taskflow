from django.conf import settings
import redis

redis_client = redis.from_url(settings.REDIS_URL , decode_responses=True)