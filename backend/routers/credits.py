"""
Router: Billetera de Créditos y Pasarela Wompi
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel
import os
import shutil
import uuid
from backend.services.supabase_client import supabase_service
from backend.services.wompi_service import wompi_service, PACKAGES
from backend.services.nequi_receipt_scanner import nequi_scanner

router = APIRouter(prefix="/api/credits", tags=["Billetera y Pagos"])

VOUCHERS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage", "vouchers"))
os.makedirs(VOUCHERS_DIR, exist_ok=True)

class CheckoutRequest(BaseModel):
    package_id: str = "STANDARD_PACK_5"

class SimulatePaymentRequest(BaseModel):
    package_id: str = "STANDARD_PACK_5"

@router.post("/upload-voucher")
async def upload_voucher_endpoint(
    package_id: str = Form("STANDARD_PACK_5"),
    voucher_file: UploadFile = File(...)
):
    """
    Recibe el comprobante (Nequi / Corresponsal Bancolombia / Wompi),
    extrae los datos mediante visión artificial y ejecuta validación antifraude estricta.
    """
    from backend.services.nequi_receipt_validator import extract_receipt_data, validate_and_release_credits

    user_id = "demo_user_1"
    pkg = PACKAGES.get(package_id, PACKAGES["STANDARD_PACK_5"])
    expected_amount = float(pkg["price_cop"])

    # Leer bytes del archivo
    file_bytes = await voucher_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="El archivo subido está vacío.")

    # 1. Extracción con motor de visión artificial
    extracted_data = await extract_receipt_data(file_bytes)

    # 2. Validación estricta y prevención de fraude
    val_res = validate_and_release_credits(
        raw_data=extracted_data,
        image_bytes=file_bytes,
        expected_amount=expected_amount,
        requested_package=package_id
    )

    # 3. Gestión de estados
    if val_res.status == "APPROVED":
        # Liberación inmediata de créditos
        supabase_service.recharge_credits(user_id, package_id)
        updated_credits = supabase_service.get_user_credits(user_id)
        return {
            "status": "APPROVED",
            "message": f"¡Comprobante verificado con éxito! Se acreditaron {val_res.credits_granted} créditos a tu cuenta.",
            "credits": updated_credits,
            "extraction": extracted_data,
            "reasons": val_res.reasons
        }
    elif val_res.status == "MANUAL_REVIEW_REQUIRED":
        return {
            "status": "MANUAL_REVIEW_REQUIRED",
            "message": "Comprobante recibido. Pasó a verificación semi-asistida y se activará en pocos minutos.",
            "credits": supabase_service.get_user_credits(user_id),
            "extraction": extracted_data,
            "reasons": val_res.reasons
        }
    else:
        # REJECTED
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Comprobante no válido o sospecha de inconsistencia.",
                "reasons": val_res.reasons,
                "detected_data": extracted_data
            }
        )

@router.get("/balance")
async def get_balance():
    user_id = "demo_user_1"
    credits = supabase_service.get_user_credits(user_id)
    return {
        "status": "success",
        "user_id": user_id,
        "credits": credits
    }

@router.get("/packages")
async def get_packages():
    return {
        "status": "success",
        "packages": PACKAGES
    }

@router.post("/create-checkout")
async def create_checkout(req: CheckoutRequest):
    user_id = "demo_user_1"
    checkout_data = wompi_service.create_checkout_session(user_id, req.package_id)
    return {
        "status": "success",
        "checkout": checkout_data
    }

@router.post("/simulate-payment")
async def simulate_payment(req: SimulatePaymentRequest):
    """Permite simular el pago instantáneo en modo desarrollo."""
    user_id = "demo_user_1"
    res = supabase_service.recharge_credits(user_id, req.package_id)
    updated_credits = supabase_service.get_user_credits(user_id)
    return {
        "status": "success",
        "message": f"Pago aprobado exitosamente. Se activó el paquete: {req.package_id}",
        "credits": updated_credits
    }
