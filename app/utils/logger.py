import logging
import re
from typing import Any

class PIIRedactor(logging.Filter):
    """Filter to redact PII from logs."""
    
    PII_PATTERNS = [
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),  # SSN
        (r'\b\d{16}\b', '[CARD]'),  # Credit card
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),  # Email
        (r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]'),  # Phone
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern, replacement in self.PII_PATTERNS:
            message = re.sub(pattern, replacement, message)
        record.msg = message
        return True

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('contract_intelligence')
logger.addFilter(PIIRedactor())