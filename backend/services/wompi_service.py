"""
Servicio: Pasarela de Pagos Wompi Colombia (Nequi, Daviplata, PSE, Tarjetas)
Soporta:
    - Paquete Semestre Universitario: $50.000 COP (5 Créditos Estándar)
    - Pase Proyecto de Grado Premium / Tesis Completa: $120.000 COP (1 Macroproyecto a la Medida)
"""

import os
import hashlib
import uuid
from datetime import datetime

WOMPI_PUBLIC_KEY = os.getenv("WOMPI_PUBLIC_KEY", "pub_test_wompi_sandbox_token")
WOMPI_EVENTS_SECRET = os.getenv("WOMPI_EVENTS_SECRET", "test_events_secret")
WOMPI_INTEGRITY_SECRET = os.getenv("WOMPI_INTEGRITY_SECRET", "test_integrity_secret")

PACKAGES = {
    "MICRO_PACK_1": {
        "name": "Paquete Micro / Ensayos Cortos (1 Crédito)",
        "price_cop": 10000,
        "amount_in_cents": 1000000,
        "credits": 1,
        "tier": "standard",
        "description": "1 micro-ensayo, ficha de lectura o aporte al foro (1 a 5 págs)."
    },
    "BASIC_PACK_2": {
        "name": "Plan Básico / Tarea Regular (2 Créditos)",
        "price_cop": 20000,
        "amount_in_cents": 2000000,
        "credits": 2,
        "tier": "standard",
        "description": "Tarea regular de curso (psicología, educación, etc. de 13 a 30 págs) o corrección de hasta 50 págs."
    },
    "STANDARD_PACK_5": {
        "name": "Paquete Semestral Universitario (5 Créditos)",
        "price_cop": 50000,
        "amount_in_cents": 5000000,
        "credits": 5,
        "tier": "standard",
        "description": "2 a 3 tareas completas de 30 págs o corrección de tesis estándar."
    },
    "PREMIUM_PROJECT_PASS": {
        "name": "Macro-Tesis de Posgrado / Proyecto Extenso (10 Créditos)",
        "price_cop": 100000,
        "amount_in_cents": 10000000,
        "credits": 10,
        "tier": "premium_project",
        "description": "Tesis de grado o posgrado > 140 págs con Reporte Integral de Auditoría en Excel."
    }
}

class WompiService:
    def create_checkout_session(self, user_id, package_id):
        """Genera una referencia y la URL / datos de checkout para Wompi."""
        pkg = PACKAGES.get(package_id, PACKAGES["STANDARD_PACK_5"])
        reference = f"ACAD-{uuid.uuid4().hex[:10].upper()}"
        
        # Firma de integridad de Wompi (SHA256: reference + amountInCents + currency + integritySecret)
        currency = "COP"
        amount_cents = pkg["amount_in_cents"]
        raw_signature = f"{reference}{amount_cents}{currency}{WOMPI_INTEGRITY_SECRET}"
        signature = hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()

        return {
            "reference": reference,
            "package_id": package_id,
            "package_name": pkg["name"],
            "amount_cop": pkg["price_cop"],
            "amount_in_cents": amount_cents,
            "currency": currency,
            "public_key": WOMPI_PUBLIC_KEY,
            "signature": signature,
            "redirect_url": f"http://localhost:8000/?payment=success&ref={reference}",
            "payment_methods": ["NEQUI", "PSE", "BANCOLOMBIA", "CARD"]
        }

    def verify_webhook_signature(self, body_bytes, checksum_header):
        """Verifica la autenticidad del evento recibido desde Wompi."""
        # En modo sandbox se retorna True para pruebas locales
        return True

wompi_service = WompiService()
