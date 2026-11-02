"""
Servicio de Notificaciones y Correos Electrónicos (AcademicPro AI)
Envía correos de confirmación de registro y alertas de entrega de trabajos.
Soporta:
  - Envío real por SMTP (Gmail / Outlook / Servidor propio).
  - Almacenamiento local de respaldo en storage/sent_emails/ para auditoría.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

def _get_emails_dir() -> str:
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        tmp_dir = "/tmp/academicpro_storage/sent_emails"
        os.makedirs(tmp_dir, exist_ok=True)
        return tmp_dir
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage", "sent_emails"))
    try:
        os.makedirs(base_dir, exist_ok=True)
        return base_dir
    except (OSError, PermissionError):
        tmp_dir = "/tmp/academicpro_storage/sent_emails"
        os.makedirs(tmp_dir, exist_ok=True)
        return tmp_dir

STORAGE_EMAILS_DIR = _get_emails_dir()

def _get_smtp_credentials():
    user = os.getenv("SMTP_USER", "").strip()
    pwd = os.getenv("SMTP_PASS", "").replace(" ", "").strip()
    if user and pwd:
        return user, pwd

    env_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
        os.path.abspath(os.path.join(os.getcwd(), ".env")),
        os.path.abspath(os.path.join(os.getcwd(), "Blueprint", ".env"))
    ]
    for ep in env_paths:
        if os.path.exists(ep):
            try:
                with open(ep, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("SMTP_USER="):
                            user = line.split("=", 1)[1].strip()
                        elif line.startswith("SMTP_PASS="):
                            pwd = line.split("=", 1)[1].replace(" ", "").strip()
            except Exception:
                pass
    return user, pwd

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

class EmailService:
    def send_welcome_email(self, to_email: str, username_alias: str, initial_credits: int = 2) -> dict:
        """Envía el correo oficial de bienvenida al estudiante."""
        subject = "🎓 ¡Tu registro en AcademicPro ha sido todo un éxito! (Créditos Activos)"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0B132B; color: #F8FAFC; margin: 0; padding: 20px; }}
            .container {{ max-width: 580px; margin: 0 auto; background-color: #1C2541; border: 1px solid #3A506B; border-radius: 16px; overflow: hidden; }}
            .header {{ background-color: #0F172A; padding: 24px; text-align: center; border-bottom: 2px solid #D4F63C; }}
            .header h1 {{ margin: 0; font-size: 24px; color: #FFFFFF; }}
            .header span.pro {{ color: #D4F63C; font-weight: 800; }}
            .body {{ padding: 28px; line-height: 1.6; font-size: 14px; color: #CBD5E1; }}
            .badge-box {{ background: rgba(212, 246, 60, 0.1); border: 1px solid rgba(212, 246, 60, 0.3); border-radius: 10px; padding: 14px; text-align: center; margin: 20px 0; }}
            .badge-box strong {{ font-size: 20px; color: #D4F63C; display: block; }}
            .btn-cta {{ display: inline-block; background-color: #D4F63C; color: #0B132B; padding: 12px 28px; font-weight: 800; border-radius: 8px; text-decoration: none; margin-top: 16px; }}
            .footer {{ background: #0F172A; padding: 16px; text-align: center; font-size: 11px; color: #94A3B8; border-top: 1px solid #3A506B; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>Academic<span class="pro">Pro</span> AI</h1>
              <p style="margin: 4px 0 0; font-size: 12px; color: #94A3B8;">Plataforma Oficial de Asistencia Académica UNAD & SENA</p>
            </div>
            <div class="body">
              <h2 style="color: #FFFFFF; font-size: 18px; margin-top: 0;">¡Hola, {username_alias}! 🚀</h2>
              <p>Tu registro en <strong>AcademicPro</strong> ha sido todo un éxito. Tu cuenta está activa y lista para estructurar tus actividades académicas, ensayos y proyectos de grado bajo el <strong>Instructivo Oficial de Normas APA 7.ª Edición</strong>.</p>
              
              <div class="badge-box">
                <span style="font-size: 12px; color: #CBD5E1;">Bono de Bienvenida Activado:</span>
                <strong>💳 {initial_credits} Créditos Gratuitos Disponibles</strong>
                <span style="font-size: 11px; color: #94A3B8;">Rinden para estructurar o auditar tus primeros trabajos.</span>
              </div>

              <p><strong>Lo que puedes hacer hoy mismo:</strong></p>
              <ul>
                <li>📄 <strong>Crear desde Guía:</strong> Sube tu guía de actividades (PDF o Word) y obtén tu trabajo maquetado con citas y portada.</li>
                <li>📊 <strong>Auditoría con Certificación en Excel:</strong> Revisa tu borrador y genera el reporte comparativo para tu tutor.</li>
                <li>📈 <strong>Plantillas de Excel:</strong> Completa matrices de marco lógico y cronogramas institucionales.</li>
              </ul>

              <div style="text-align: center;">
                <a href="http://localhost:8000" class="btn-cta">Entrar a la Plataforma</a>
              </div>
            </div>
            <div class="footer">
              <p>Asesoría personalizada y soporte directo: <strong>+57 320 710 5618</strong> (Jhon Zapata)</p>
              <p style="margin: 0;">AcademicPro AI · Privacidad Blindada para Estudiantes Universitarios</p>
            </div>
          </div>
        </body>
        </html>
        """

        # 1. Guardar copia física del correo enviado en la bóveda
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_alias = "".join(c for c in username_alias if c.isalnum() or c in "_-")
        email_record_path = os.path.join(STORAGE_EMAILS_DIR, f"Bienvenida_{safe_alias}_{timestamp}.html")
        try:
            with open(email_record_path, "w", encoding="utf-8") as f:
                f.write(html_content)
        except Exception:
            pass

        # 2. Si hay credenciales SMTP en .env, enviar a través de internet
        smtp_sent = False
        smtp_error = None
        user, pwd = _get_smtp_credentials()
        if user and pwd:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"AcademicPro AI <{user}>"
                msg["To"] = to_email
                msg.attach(MIMEText(html_content, "html", "utf-8"))

                with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=12) as server:
                    server.starttls()
                    server.login(user, pwd)
                    server.sendmail(user, [to_email], msg.as_string())
                smtp_sent = True
            except Exception as e:
                smtp_error = str(e)

        return {
            "status": "success",
            "to_email": to_email,
            "smtp_delivered": smtp_sent,
            "smtp_error": smtp_error,
            "email_backup_html": email_record_path,
            "message": f"Correo de bienvenida preparado y registrado para {to_email}."
        }

email_service = EmailService()
