from prometheus_client import Counter, Histogram, Gauge
import time

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Application metrics
DOCUMENTS_INGESTED = Counter(
    'documents_ingested_total',
    'Total documents ingested'
)

EXTRACTIONS_COMPLETED = Counter(
    'extractions_completed_total',
    'Total extractions completed'
)

QUESTIONS_ANSWERED = Counter(
    'questions_answered_total',
    'Total questions answered'
)

AUDITS_COMPLETED = Counter(
    'audits_completed_total',
    'Total audits completed'
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)    