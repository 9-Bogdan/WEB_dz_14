from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from services.auth import auth_service
from conf.config import settings

base_path = Path(__file__).resolve().parent.parent
print(base_path)
TEMPLATE_FOLDEr = base_path /'services'/ 'templates'


conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME="Desired Name",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=TEMPLATE_FOLDEr,
)


async def send_email(email: EmailStr, username: str, host: str):
    """
    Send a confirmation email to the user.

    :param email: Email address of the recipient.
    :type email: EmailStr
    :param username: Username of the recipient.
    :type username: str
    :param host: Host URL for email confirmation link.
    :type host: str
    :return: None
    :rtype: None
    """
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_template.html")
    except ConnectionErrors as err:
        print(err)
