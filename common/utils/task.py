import logging
from typing import Any, Dict, List, Optional
from celery.app.task import Task
from django.core.cache import cache
from service.celery import app as celery_app

logger = logging.getLogger(__name__)


def is_task_running_or_waiting(
    task: Task,
    task_args: Optional[Dict[str, Any]] = None,
    ignored_args: Optional[List[str]] = None,
) -> bool:
    """
    Checks if a task is currently running or waiting to be executed.
    Args:
        task (Task): The task object to check.
        task_args (Dict[str, any], optional): The arguments of the task. Defaults to None.
    Returns:
        bool: True if the task is running or waiting, False otherwise.
    """

    # remove ignored args from task_args
    if ignored_args:
        task_args = {k: v for k, v in task_args.items() if k not in ignored_args}

    # logger.info(f"Checking if task {task.name} / {task.request.id} is running or waiting with args: {task_args}")

    scheduled = task.app.control.inspect().scheduled()
    scheduled_tasks = list(scheduled.values())[0] if scheduled else []

    for task_info in scheduled_tasks:
        info = task_info.get("request", {})

        if (
            info.get("name", None) == task.name
            and info.get("id", None) != task.request.id
        ):

            info_kwargs = info.get("kwargs", {})
            if ignored_args:
                info_kwargs = {
                    k: v for k, v in info_kwargs.items() if k not in ignored_args
                }

            # logger.info(f"Scheduled task {task.name} / {task.request.id} with args {info_kwargs}")

            # Check if task_args is provided and if the task arguments in task_info match task_args
            if task_args and info_kwargs == task_args:
                return True
            elif not task_args:
                return True

    active = task.app.control.inspect().active()
    active_tasks = list(active.values())[0] if active else []

    for task_info in active_tasks:
        info = task_info.get("request", {})

        if (
            info.get("name", None) == task.name
            and info.get("id", None) != task.request.id
        ):

            info_kwargs = info.get("kwargs", {})
            if ignored_args:
                info_kwargs = {
                    k: v for k, v in info_kwargs.items() if k not in ignored_args
                }

            # logger.info(f"Active task {task.name} / {task.request.id} with args {info_kwargs}")

            # Check if task_args is provided and if the task arguments in task_info match task_args
            if task_args and info_kwargs == task_args:
                return True
            elif not task_args:
                return True

    return False


def cancel_previous_tasks(
    task_name: any,
    task_args: Optional[Dict[str, Any]] = None,
    ignored_args: Optional[List[str]] = None,
):

    is_task_instance = isinstance(task_name, Task)

    revoked_scheduled_tasks = []
    revoked_active_tasks = []

    if not task_name:
        raise Exception("Task name is required")

    if is_task_instance:
        task_instance = task_name
        task_name = task_name.name
    elif isinstance(task_name, str):
        task_name = task_name
    else:
        raise Exception("Invalid task name")

    inspector = celery_app.control.inspect()

    scheduled = inspector.scheduled()
    scheduled_tasks = list(scheduled.values())[0] if scheduled else []

    for task_info in scheduled_tasks:
        info = task_info.get("request", {})

        if info.get("name", None) == task_name:

            info_kwargs = info.get("kwargs", {})
            if ignored_args:
                info_kwargs = {
                    k: v for k, v in info_kwargs.items() if k not in ignored_args
                }

            if is_task_instance and info.get("id", None) == task_instance.request.id:
                continue

            if task_args and info_kwargs == task_args:
                revoked_scheduled_tasks.append(info.get("id", None))

    if revoked_scheduled_tasks:
        celery_app.control.revoke(
            revoked_scheduled_tasks, terminate=True, signal="KILL"
        )

    active = inspector.active()
    active_tasks = list(active.values())[0] if active else []

    for task_info in active_tasks:
        info = task_info.get("request", {})

        if info.get("name", None) == task_name:
            info_kwargs = info.get("kwargs", {})
            if ignored_args:
                info_kwargs = {
                    k: v for k, v in info_kwargs.items() if k not in ignored_args
                }

            if is_task_instance and info.get("id", None) == task_name.task_instance.id:
                continue

            if task_args and info_kwargs == task_args:
                revoked_active_tasks.append(info.get("id", None))

    if revoked_active_tasks:
        celery_app.control.revoke(revoked_active_tasks, terminate=True, signal="KILL")

    if revoked_scheduled_tasks and revoked_active_tasks:
        logger.info(
            f"Revoked {len(revoked_scheduled_tasks)} scheduled and {len(revoked_active_tasks)} active tasks for {task_name} with args {task_args}"
        )
    elif revoked_scheduled_tasks:
        logger.info(
            f"Revoked {len(revoked_scheduled_tasks)} scheduled tasks for {task_name} with args {task_args}"
        )
    elif revoked_active_tasks:
        logger.info(
            f"Revoked {len(revoked_active_tasks)} active tasks for {task_name} with args {task_args}"
        )

    return len(revoked_scheduled_tasks), len(revoked_active_tasks)


def acquire_lock(key: str, timeout: int = 60) -> bool:
    """
    Acquires a lock for a given key.
    Args:
        key (str): The key to acquire the lock for.
        timeout (int): The timeout for the lock. (in seconds)

    Returns:
        bool: True if the lock was acquired, False otherwise.

    """
    return cache.add(key, "true", timeout)


def release_lock(key: str) -> bool:
    """
    Releases a lock for a given key.
    Args:
        key (str): The key to release the lock for.
    Returns:
        bool: True if the lock was released, False otherwise.
    """
    return cache.delete(key)
