from redis import Redis
from rq import Queue

from settings import get_required_env


def get_redis_url() -> str:
    return get_required_env("REDIS_URL")


def get_rq_queue_name() -> str:
    return get_required_env("RQ_QUEUE_NAME")


def create_redis_connection() -> Redis:
    return Redis.from_url(get_redis_url())


def get_job_queue() -> Queue:
    return Queue(
        name=get_rq_queue_name(),
        connection=create_redis_connection(),
    )
