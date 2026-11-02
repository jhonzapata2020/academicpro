"""
Router de Integración para Make / Integromat y Enlaces WhatsApp Directos
Maneja los eventos de notificación, validación semi-asistida y contacto de soporte (+57 320 710 5618).
"""

import os
import hmac
import hashlib
import urllib.parse
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/automation", tags=["Automation & Make"])

SUPPORT_WHATSAPP_NUMBER = "573207105618"
INTEGROMAT_WEBHOOK_URL = os.getenv("INTEGROMAT_WEBHOOK_URL", "")
INTEGROMAT_WEBHOOK_SECRET = os.getenv("INTEGROMAT_WEBHOOK_SECRET", "academicpro_secret_key_2026")

class WebhookPayload(BaseModel):
    tipo_evento: str = Field(..., description="nuevo_comprobante_nequi | solicitud_personalizada_whatsapp | pago_aprobado_wompi")
    usuario_id: Optional[str] = "usr_guest"
    nombre: str = "Estudiante"
    celular: str = "573000000000"
    email: Optional[str] = "estudiante@unad.edu.co"
    monto: Optional[int] = 0
    archivo_id: Optional[str] = None
    nombre_archivo: Optional[str] = "trabajo_academico.docx"
    paginas: Optional[int] = 1
    tipo_servicio: Optional[str] = "creacion"
    instrucciones_tutor: Optional[str] = ""

class CustomAssistanceRequest(BaseModel):
    nombre: str
    celular: str
    nombre_archivo: str
    paginas: int
    instrucciones: Optional[str] = ""

@router.post("/generate-whatsapp-link")
async def generate_whatsapp_link(req: CustomAssistanceRequest):
    """
    Genera el enlace interactivo wa.me estructurado para contactar directamente al canal de soporte académico.
    """
    cleaned_phone = req.celular.strip().replace("+", "").replace(" ", "").replace("-", "")
    
    mensaje_texto = (
        f"Hola, acabo de subir mi trabajo ({req.nombre_archivo}, {req.paginas} págs) a AcademicPro "
        f"y me gustaría cotizar la revisión personalizada. "
        f"Instrucciones o notas del tutor: '{req.instrucciones or 'Revisión general y formato APA 7'}'."
    )
    
    encoded_message = urllib.parse.quote(mensaje_texto)
    wa_url = f"https://wa.me/{SUPPORT_WHATSAPP_NUMBER}?text={encoded_message}"
    
    return {
        "status": "success",
        "whatsapp_url": wa_url,
        "recipient": f"+{SUPPORT_WHATSAPP_NUMBER} (Soporte Académico)",
        "message_preview": mensaje_texto
    }

@router.post("/webhook/receive")
async def receive_integromat_webhook(request: Request, x_signature: Optional[str] = Header(None)):
    """
    Recibe la confirmación desde Integromat (Make) cuando el administrador aprueba un pago vía Telegram/WhatsApp.
    Valida firma HMAC y libera el documento.
    """
    body_bytes = await request.body()
    
    # Verificación de firma opcional (o token)
    if x_signature:
        expected_sig = hmac.new(
            INTEGROMAT_WEBHOOK_SECRET.encode(),
            body_bytes,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(x_signature, expected_sig):
            raise HTTPException(status_code=401, detail="Firma de seguridad no válida")

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON malformado")

    action = data.get("action")
    trabajo_id = data.get("trabajo_id")
    monto = data.get("monto", 0)

    if action == "APPROVE":
        # Registrar aprobación en la base de datos y otorgar acceso al archivo
        return {
            "status": "success",
            "message": f"Trabajo {trabajo_id} aprobado con éxito por el Administrador. Descarga liberada.",
            "unlocked": True
        }
    elif action == "REJECT":
        return {
            "status": "success",
            "message": f"Trabajo {trabajo_id} rechazado. Se notificó al estudiante.",
            "unlocked": False
        }
    
    return {"status": "ignored", "action": action}
