import asyncio

from fastapi import APIRouter
from loguru import logger

from .crud import db
from .tasks import wait_for_paid_invoices
from .views import smtp_generic_router
from .views_api import smtp_api_router

smtp_static_files = [
    {
        "path": "/smtp/static",
        "name": "smtp_static",
    }
]

smtp_ext: APIRouter = APIRouter(prefix="/smtp", tags=["smtp"])
smtp_ext.include_router(smtp_generic_router)
smtp_ext.include_router(smtp_api_router)

scheduled_tasks: list[asyncio.Task] = []


def smtp_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)


def smtp_start():
    from lnbits.tasks import create_permanent_unique_task

    task = create_permanent_unique_task("ext_smtp", wait_for_paid_invoices)
    scheduled_tasks.append(task)


__all__ = ["db", "smtp_ext", "smtp_static_files", "smtp_start", "smtp_stop"]
