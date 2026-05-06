from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["endpoint"]
)
REDIRECT_COUNT = Counter(
    "url_redirects_total",
    "Total URL redirects"
)
URL_CREATED = Counter(
    "urls_created_total",
    "Total URLs created"
)
