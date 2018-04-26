from django.utils import timezone

from .tasks import benchmark_request

try:
    from log_request_id import local
except ImportException:
    local = None

def benchmark(description):
    now = timezone.now()
    uuid = getattr(local, 'request_id', None)

    # Only create a RequestBenchmark if there is a request_id
    if uuid:
        benchmark_request.apply_async(args=[description, uuid, now])
