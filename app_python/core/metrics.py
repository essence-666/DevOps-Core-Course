from prometheus_client import Counter, Histogram, Gauge

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests currently being processed',
)

endpoint_calls = Counter(
    'devops_info_endpoint_calls_total',
    'Total calls per endpoint',
    ['endpoint'],
)

system_info_duration = Histogram(
    'devops_info_system_collection_seconds',
    'Time spent collecting system info',
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5],
)
