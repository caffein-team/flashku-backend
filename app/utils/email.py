from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib
from app.config import settings

logger = logging.getLogger(__name__)


def send_otp_email(to_email: str, otp_code: str, user_name: str) -> bool:
    """Send an OTP code for password reset via Google Gmail SMTP.

    Falls back to console logging if credentials are missing or in dev.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            f"[EMAIL MOCK] SMTP_USER or SMTP_PASSWORD is not configured in .env. "
            f"Reset OTP for {to_email} ({user_name}) is: >>> {otp_code} <<<"
        )
        print(f"\n=======================================================")
        print(f"[OTP NOTIFICATION] To: {to_email}")
        print(f"Name: {user_name}")
        print(f"OTP Code: >>> {otp_code} <<< (Valid for {settings.OTP_EXPIRE_MINUTES} mins)")
        print(f"=======================================================\n")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Kode Verifikasi Reset Password - {settings.APP_NAME}"
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
        msg["To"] = to_email

        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reset Password OTP</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px;">
    <div style="max-width: 480px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1); border: 1px solid #e2e8f0;">
        <div style="text-align: center; margin-bottom: 24px;">
            <h1 style="color: #0f172a; font-size: 24px; font-weight: 700; margin: 0;">{settings.APP_NAME}</h1>
            <p style="color: #64748b; font-size: 14px; margin-top: 4px;">Permintaan Atur Ulang Kata Sandi</p>
        </div>
        
        <p style="color: #334155; font-size: 15px; line-height: 1.6; margin-bottom: 16px;">
            Halo <strong>{user_name}</strong>,
        </p>
        <p style="color: #334155; font-size: 15px; line-height: 1.6; margin-bottom: 24px;">
            Kami menerima permintaan untuk mereset kata sandi akun Anda. Masukkan 6-digit kode OTP berikut pada aplikasi untuk melanjutkan:
        </p>
        
        <div style="background-color: #f1f5f9; border: 2px dashed #94a3b8; border-radius: 12px; padding: 18px; text-align: center; margin-bottom: 24px;">
            <span style="font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #2563eb; font-family: monospace;">{otp_code}</span>
        </div>
        
        <p style="color: #64748b; font-size: 13px; text-align: center; margin-bottom: 24px;">
            Kode ini kedaluwarsa dalam waktu <strong>{settings.OTP_EXPIRE_MINUTES} menit</strong>.
        </p>
        
        <div style="border-top: 1px solid #e2e8f0; padding-top: 16px; margin-top: 16px;">
            <p style="color: #94a3b8; font-size: 12px; line-height: 1.5; margin: 0; text-align: center;">
                Jika Anda tidak merasa meminta reset kata sandi, silakan abaikan pesan ini. Akun Anda tetap terlindungi dengan aman.
            </p>
        </div>
    </div>
</body>
</html>
"""
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, [to_email], msg.as_string())

        logger.info(f"Password reset OTP sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email} via Gmail SMTP: {e}")
        print(f"\n[FALLBACK OTP LOG] Due to SMTP error: OTP for {to_email} is: >>> {otp_code} <<<\n")
        return False
