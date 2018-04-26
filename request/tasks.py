import time

from uuid import uuid4

from contextlib import contextmanager

from celery import Celery
from celery.five import monotonic

from django.conf import settings
from django.core.cache import cache

from .models import Request, RequestBenchmark

celery_app = Celery(settings.CELERY_APP_NAME)
celery_app.config_from_object('django.conf:settings')

LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes


@contextmanager
def memcache_lock(lock_id):
    timeout_at = monotonic() + LOCK_EXPIRE - 3

    status = False
    while not status:
        status = cache.add(lock_id, True, LOCK_EXPIRE)
        time.sleep(0.1)
        if monotonic() > timeout_at:
            break

    try:
        yield status
    finally:
        cache.delete(lock_id)


@celery_app.task(bind=True)
def benchmark_request(self, description, uuid, time):
    with memcache_lock(uuid) as acquired:
        if acquired:
            RequestBenchmark.objects.create(time=time, uuid=uuid, description=description)


@celery_app.task(bind=True)
def update_benchmarks(self, request_pk, uuid):
    with memcache_lock(uuid) as acquired:
        if acquired:
            RequestBenchmark.objects.filter(uuid=uuid).update(request=request_pk)

