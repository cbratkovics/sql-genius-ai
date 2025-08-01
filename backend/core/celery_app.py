from celery import Celery
from kombu import Queue
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "sql_genius_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "backend.tasks.query_processing",
        "backend.tasks.file_processing", 
        "backend.tasks.analytics",
        "backend.tasks.notifications",
        "backend.tasks.maintenance"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "backend.tasks.query_processing.*": {"queue": "query_processing"},
        "backend.tasks.file_processing.*": {"queue": "file_processing"},
        "backend.tasks.analytics.*": {"queue": "analytics"},
        "backend.tasks.notifications.*": {"queue": notifications"},
        "backend.tasks.maintenance.*": {"queue": "maintenance"}
    },
    
    # Queue definitions
    task_queues=(
        Queue("query_processing", routing_key="query_processing"),
        Queue("file_processing", routing_key="file_processing"), 
        Queue("analytics", routing_key="analytics"),
        Queue("notifications", routing_key="notifications"),
        Queue("maintenance", routing_key="maintenance"),
    ),
    
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_expires=3600,  # 1 hour
    timezone="UTC",
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Task execution
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    
    # Result backend settings
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    
    # Beat scheduler settings (for periodic tasks)
    beat_schedule={
        "cleanup-expired-files": {
            "task": "backend.tasks.maintenance.cleanup_expired_files",
            "schedule": 3600.0,  # Every hour
        },
        "update-usage-metrics": {
            "task": "backend.tasks.analytics.update_usage_metrics", 
            "schedule": 300.0,  # Every 5 minutes
        },
        "cache-warmup": {
            "task": "backend.tasks.maintenance.warm_cache",
            "schedule": 1800.0,  # Every 30 minutes
        },
        "generate-reports": {
            "task": "backend.tasks.analytics.generate_daily_reports",
            "schedule": 86400.0,  # Daily
        }
    },
    beat_scheduler="django_celery_beat.schedulers:DatabaseScheduler",
)

# Task priority levels
celery_app.conf.task_routes.update({
    "backend.tasks.query_processing.process_urgent_query": {"queue": "query_processing", "priority": 9},
    "backend.tasks.query_processing.process_standard_query": {"queue": "query_processing", "priority": 5},
    "backend.tasks.file_processing.process_large_file": {"queue": "file_processing", "priority": 3},
    "backend.tasks.analytics.generate_insights": {"queue": "analytics", "priority": 4},
})

# Error handling
celery_app.conf.task_annotations = {
    "*": {
        "rate_limit": "100/m",  # 100 tasks per minute
        "max_retries": 3,
        "default_retry_delay": 60,  # 60 seconds
    },
    "backend.tasks.query_processing.*": {
        "rate_limit": "50/m",
        "max_retries": 2,
    },
    "backend.tasks.file_processing.*": {
        "rate_limit": "20/m", 
        "max_retries": 3,
        "default_retry_delay": 120,
    }
}

if __name__ == "__main__":
    celery_app.start()