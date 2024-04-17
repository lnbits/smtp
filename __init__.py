import asyncio

from loguru import logger
from fastapi import APIRouter

from lnbits.db import Database
from lnbits.helpers import template_renderer
from lnbits.tasks import create_permanent_unique_task

db = Database("ext_smtp")

smtp_static_files = [
    {
        "path": "/smtp/static",
        "name": "smtp_static",
    }
]

smtp_ext: APIRouter = APIRouter(prefix="/smtp", tags=["smtp"])


def smtp_renderer():
    return template_renderer(["smtp/templates"])


from .tasks import wait_for_paid_invoices
from .views import *  # noqa: F401,F403
from .views_api import *  # noqa: F401,F403


scheduled_tasks: list[asyncio.Task] = []

def smtp_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)

def smtp_start():
    task = create_permanent_unique_task("ext_smtp", wait_for_paid_invoices)
    scheduled_tasks.append(task)
