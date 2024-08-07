from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer
from starlette.responses import HTMLResponse

from .crud import get_emailaddress

templates = Jinja2Templates(directory="templates")
smtp_generic_router = APIRouter()


def smtp_renderer():
    return template_renderer(["smtp/templates"])


@smtp_generic_router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_user_exists)):
    return smtp_renderer().TemplateResponse(
        "smtp/index.html", {"request": request, "user": user.dict()}
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
