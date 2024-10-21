from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from lnbits.core.crud import get_user
from lnbits.core.models import WalletTypeInfo
from lnbits.core.services import check_transaction_status, create_invoice
from lnbits.decorators import require_admin_key, require_invoice_key

from .crud import (
    create_email,
    create_emailaddress,
    delete_email,
    delete_emailaddress,
    get_email,
    get_email_by_payment_hash,
    get_emailaddress,
    get_emailaddresses,
    get_emails,
    update_emailaddress,
)
from .models import CreateEmail, CreateEmailaddress, Email, Emailaddress
from .smtp import send_mail, valid_email

smtp_api_router = APIRouter()


## EMAILS
@smtp_api_router.get("/api/v1/email")
async def api_email(
    key_info: WalletTypeInfo = Depends(require_invoice_key),
    all_wallets: bool = Query(False),
) -> list[Email]:
    wallet_ids = [key_info.wallet.id]
    if all_wallets:
        user = await get_user(key_info.wallet.user)
        if user:
            wallet_ids = user.wallet_ids
    return await get_emails(wallet_ids)


@smtp_api_router.get("/api/v1/email/{payment_hash}")
async def api_smtp_send_email(payment_hash):
    email = await get_email_by_payment_hash(payment_hash)
    if not email:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="paymenthash is wrong"
        )

    emailaddress = await get_emailaddress(email.emailaddress_id)
    assert emailaddress

    try:
        status = await check_transaction_status(email.wallet, payment_hash)
        is_paid = not status.pending
    except Exception:
        return {"paid": False}
    if is_paid:
        if emailaddress.anonymize:
            await delete_email(email.id)
        return {"paid": True}
    return {"paid": False}


@smtp_api_router.post("/api/v1/email/{emailaddress_id}")
async def api_smtp_make_email(emailaddress_id, data: CreateEmail):
    valid_email(data.receiver)

    emailaddress = await get_emailaddress(emailaddress_id)
    if not emailaddress:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Emailaddress address does not exist.",
        )
    memo = f"sent email from {emailaddress.email} to {data.receiver}"
    if emailaddress.anonymize:
        memo = "sent email"

    payment = await create_invoice(
        wallet_id=emailaddress.wallet,
        amount=emailaddress.cost,
        memo=memo,
        extra={"tag": "smtp"},
    )

    email = await create_email(
        payment_hash=payment.payment_hash, wallet=emailaddress.wallet, data=data
    )

    if not email:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Email could not be fetched."
        )
    return {"payment_hash": payment.payment_hash, "payment_request": payment.bolt11}


@smtp_api_router.post(
    "/api/v1/email/{emailaddress_id}/send", dependencies=[Depends(require_admin_key)]
)
async def api_smtp_make_email_send(emailaddress_id, data: CreateEmail):
    valid_email(data.receiver)
    emailaddress = await get_emailaddress(emailaddress_id)
    if not emailaddress:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Emailaddress address does not exist.",
        )
    email = await create_email(wallet=emailaddress.wallet, data=data)
    if not email:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Email could not be fetched."
        )
    await send_mail(emailaddress, email)
    return {"sent": True}


@smtp_api_router.delete("/api/v1/email/{email_id}")
async def api_email_delete(
    email_id, key_info: WalletTypeInfo = Depends(require_invoice_key)
):
    email = await get_email(email_id)

    if not email:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="LNsubdomain does not exist."
        )

    if email.wallet != key_info.wallet.id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Not your email.")

    await delete_email(email_id)


@smtp_api_router.get("/api/v1/emailaddress")
async def api_emailaddresses(
    key_info: WalletTypeInfo = Depends(require_invoice_key),
    all_wallets: bool = Query(False),
) -> list[Emailaddress]:
    wallet_ids = [key_info.wallet.id]
    if all_wallets:
        user = await get_user(key_info.wallet.user)
        if user:
            wallet_ids = user.wallet_ids
    return await get_emailaddresses(wallet_ids)


@smtp_api_router.post("/api/v1/emailaddress")
@smtp_api_router.put("/api/v1/emailaddress/{emailaddress_id}")
async def api_emailaddress_create(
    data: CreateEmailaddress,
    emailaddress_id=None,
    key_info: WalletTypeInfo = Depends(require_invoice_key),
) -> Emailaddress:
    if emailaddress_id:
        emailaddress = await get_emailaddress(emailaddress_id)

        if not emailaddress:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Emailadress does not exist."
            )
        if emailaddress.wallet != key_info.wallet.id:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, detail="Not your emailaddress."
            )

        emailaddress = await update_emailaddress(emailaddress_id, **data.dict())
    else:
        emailaddress = await create_emailaddress(data=data)
    return emailaddress


@smtp_api_router.delete("/api/v1/emailaddress/{emailaddress_id}")
async def api_emailaddress_delete(
    emailaddress_id, key_info: WalletTypeInfo = Depends(require_invoice_key)
):
    emailaddress = await get_emailaddress(emailaddress_id)

    if not emailaddress:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Emailaddress does not exist."
        )
    if emailaddress.wallet != key_info.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your Emailaddress."
        )

    await delete_emailaddress(emailaddress_id)
