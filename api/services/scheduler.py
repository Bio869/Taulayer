# api/services/scheduler.py

from fastapi import BackgroundTasks
from typing import Callable
import logging

logger = logging.getLogger(__name__)

def enqueue_background_task(
    background_tasks: BackgroundTasks,
    task_fn: Callable,
    *args,
    **kwargs
):
    """
    Adds the given function to the FastAPI background task queue.
    """
    logger.info("Enqueuing background task: %s", task_fn.__name__)
    background_tasks.add_task(task_fn, *args, **kwargs)
