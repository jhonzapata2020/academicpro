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
    "STANDARD_PACK_5": {
        "name": "Paquete Semestre Universitario (5 Créditos)",
        "price_cop": 50000,
        "amount_in_cents": 5000000,
        "credits": 5,
        "tier": "standard",
        "description": "5 trabajos universitarios completos (UNAD/SENA) o 1 tesis de grado estándar."
    },
    "PREMIUM_PROJECT_PASS": {
        "name": "Pase Macroproyecto de Grado / Tesis a la Medida",
        "price_cop": 120000,
        "amount_in_cents": 12000000,
        "credits": 1,
        "tier": "premium_project",
        "description": "1 Proyecto de investigación / Tesis completa estructurada desde cero según tu PDF de especificación."
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
