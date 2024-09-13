from typing import Optional, Union

from lnbits.db import Database
from lnbits.helpers import insert_query, update_query, urlsafe_short_hash

from .models import CreateEmail, CreateEmailaddress, Email, Emailaddress
from .smtp import send_mail

db = Database("ext_smtp")


def get_test_mail(email, testemail):
    return CreateEmail(
        emailaddress_id=email,
        subject="LNBits SMTP - Test Email",
        message="This is a test email from the LNBits SMTP extension! email working!",
        receiver=testemail,
    )


async def create_emailaddress(data: CreateEmailaddress) -> Emailaddress:

    emailaddress_id = urlsafe_short_hash()

    # send test mail for checking connection
    email = get_test_mail(data.email, data.testemail)
    await send_mail(data, email)

    emailaddress = Emailaddress(
        id=emailaddress_id,
        **data.dict(),
    )
    await db.execute(
        insert_query("smtp.emailaddress", emailaddress),
        emailaddress.dict(),
    )
    return emailaddress


async def update_emailaddress(emailaddress: Emailaddress) -> Emailaddress:
    await db.execute(
        update_query("smtp.emailaddress", emailaddress),
        emailaddress.dict(),
    )
    # send test mail for checking connection
    email = get_test_mail(emailaddress.email, emailaddress.testemail)
    await send_mail(emailaddress, email)
    return emailaddress


async def get_emailaddress(emailaddress_id: str) -> Optional[Emailaddress]:
    row = await db.fetchone(
        "SELECT * FROM smtp.emailaddress WHERE id = :id",
        {"id": emailaddress_id},
    )
    return Emailaddress(**row) if row else None


async def get_emailaddress_by_email(email: str) -> Optional[Emailaddress]:
    row = await db.fetchone(
        "SELECT * FROM smtp.emailaddress WHERE email = :email", {"email": email}
    )
    return Emailaddress(**row) if row else None


async def get_emailaddresses(wallet_ids: Union[str, list[str]]) -> list[Emailaddress]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]

    q = ",".join([f"'{wallet_id}'" for wallet_id in wallet_ids])
    rows = await db.fetchall(f"SELECT * FROM smtp.emailaddress WHERE wallet IN ({q})")
    return [Emailaddress(**row) for row in rows]


async def delete_emailaddress(emailaddress_id: str) -> None:
    await db.execute(
        "DELETE FROM smtp.emailaddress WHERE id = :id", {"id": emailaddress_id}
    )


async def create_email(wallet: str, data: CreateEmail, payment_hash: str = "") -> Email:
    email_id = urlsafe_short_hash()
    email = Email(id=email_id, payment_hash=payment_hash, wallet=wallet, **data.dict())
    await db.execute(
        insert_query("smtp.email", email),
        email.dict(),
    )
    return email


async def set_email_paid(payment_hash: str) -> bool:
    email = await get_email_by_payment_hash(payment_hash)
    if email and email.paid is False:
        await db.execute(
            "UPDATE smtp.email SET paid = true WHERE payment_hash = :payment_hash",
            {"payment_hash": payment_hash},
        )
        return True
    return False


async def get_email_by_payment_hash(payment_hash: str) -> Optional[Email]:
    row = await db.fetchone(
        "SELECT * FROM smtp.email WHERE payment_hash = :payment_hash",
        {"payment_hash": payment_hash},
    )
    return Email(**row) if row else None


async def get_email(email_id: str) -> Optional[Email]:
    row = await db.fetchone("SELECT * FROM smtp.email WHERE id = :id", {"id": email_id})
    return Email(**row) if row else None


async def get_emails(wallet_ids: Union[str, list[str]]) -> list[Email]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]

    q = ",".join([f"'{wallet_id}'" for wallet_id in wallet_ids])
    rows = await db.fetchall(
        f"""
        SELECT s.*, d.email as emailaddress FROM smtp.email s
        INNER JOIN smtp.emailaddress d ON (s.emailaddress_id = d.id)
        WHERE s.wallet IN ({q})
        """
    )

    return [Email(**row) for row in rows]


async def delete_email(email_id: str) -> None:
    await db.execute("DELETE FROM smtp.email WHERE id = :id", {"id": email_id})
