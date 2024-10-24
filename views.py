from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer

from .crud import get_emailaddress

smtp_generic_router = APIRouter()


def smtp_renderer():
    return template_renderer(["smtp/templates"])


@smtp_generic_router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_user_exists)):
    return smtp_renderer().TemplateResponse(
        "smtp/index.html", {"request": request, "user": user.json()}
    )


@smtp_generic_router.get("/{emailaddress_id}")
async def display(request: Request, emailaddress_id):
    emailaddress = await get_emailaddress(emailaddress_id)
    if not emailaddress:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Emailaddress does not exist."
        )

    return smtp_renderer().TemplateResponse(
        "smtp/display.html",
        {
            "request": request,
            "emailaddress_id": emailaddress.id,
            "email": emailaddress.email,
            "desc": emailaddress.description,
            "cost": emailaddress.cost,
        },
    )
