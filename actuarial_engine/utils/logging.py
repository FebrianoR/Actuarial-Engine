"""
Structured logging untuk Actuarial Engine.
Menggunakan structlog agar output log bisa di-parse secara otomatis
untuk keperluan monitoring dan audit trail.
"""
import logging
import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """
    Konfigurasi structlog untuk output JSON di production,
    dan output berwarna (pretty print) di development.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level.upper())
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
