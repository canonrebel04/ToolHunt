"""Security audit logging for sensitive operations."""

import logging
import json
from datetime import datetime

audit_logger = logging.getLogger('toolhunt.audit')
audit_handler = logging.FileHandler('audit.log')
audit_handler.setFormatter(logging.Formatter(
    '%(asctime)s | AUDIT | %(message)s'
))
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

def log_search_event(ip: str, query: str, result_count: int, duration_ms: float):
    """Log a search event for audit purposes."""
    audit_logger.info(
        json.dumps({
            "event": "search",
            "ip": ip,
            "query": query,
            "result_count": result_count,
            "duration_ms": round(duration_ms, 2),
            "timestamp": datetime.utcnow().isoformat()
        })
    )

def log_rate_limit_event(ip: str, endpoint: str):
    """Log a rate limit hit."""
    audit_logger.warning(
        json.dumps({
            "event": "rate_limit_hit",
            "ip": ip,
            "endpoint": endpoint,
            "timestamp": datetime.utcnow().isoformat()
        })
    )

def log_error_event(ip: str, endpoint: str, error: str):
    """Log an error for audit trail."""
    audit_logger.error(
        json.dumps({
            "event": "error",
            "ip": ip,
            "endpoint": endpoint,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })
    )
