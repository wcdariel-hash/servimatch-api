import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "f8b7e2d9b2a7c4"), # Mailtrap Default para demo
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "a1b2c3d4e5f6g7"), # Mailtrap Default para demo
    MAIL_FROM=os.getenv("MAIL_FROM", "verify@servimatch.app"),
    MAIL_PORT=587,
    MAIL_SERVER="sandbox.smtp.mailtrap.io",
    MAIL_FROM_NAME="ServiMatch Security",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_otp_email(email: EmailStr, otp: str):
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #0e0e15; color: #ffffff; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background-color: #1a1a24; padding: 40px; border-radius: 20px; border: 1px solid #333;">
                <h2 style="color: #6C63FF; text-align: center;">Verifica tu identidad</h2>
                <p style="font-size: 16px; line-height: 1.6;">Hola,</p>
                <p style="font-size: 16px; line-height: 1.6;">Gracias por unirte a <b>ServiMatch</b>. Para completar tu registro y activar tu billetera de $100, ingresa el siguiente código en la aplicación:</p>
                <div style="text-align: center; margin: 40px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 10px; background-color: #0e0e15; padding: 15px 30px; border-radius: 10px; border: 1px solid #6C63FF; color: #00E5FF;">{otp}</span>
                </div>
                <p style="font-size: 14px; color: #888; text-align: center;">Este código expirará en 10 minutos. Si no solicitaste este correo, puedes ignorarlo.</p>
                <hr style="border: 0; border-top: 1px solid #333; margin: 40px 0;">
                <p style="font-size: 12px; color: #555; text-align: center;">&copy; 2026 ServiMatch Premium Marketplace</p>
            </div>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Código de Verificación ServiMatch",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        print(f"[MAIL SUCCESS] Código enviado a {email}")
        return True
    except Exception as e:
        print(f"[MAIL ERROR] Fallo al enviar a {email}: {e}")
        return False
