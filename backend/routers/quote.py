"""
Router: Endpoints de Cotización Dinámica en Tiempo Real
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.core.pricing_engine import calcular_creditos, estimate_document_pages
from backend.services.supabase_client import supabase_service

router = APIRouter(prefix="/api/quote", tags=["Cotización Dinámica"])

@router.post("/estimate")
async def estimate_quote_endpoint(
    modalidad: str = Form("correccion"), # "creacion" | "correccion"
    file: UploadFile = File(None),
    manual_pages: int = Form(None)
):
    user_id = "demo_user_1"
    user_credits = supabase_service.get_user_credits(user_id)
    current_balance = user_credits.get("balance", 0)

    pages = 1
    if manual_pages and manual_pages > 0:
        pages = manual_pages
    elif file and file.filename:
        file_bytes = await file.read()
        pages = estimate_document_pages(file_bytes, file.filename)
    else:
        # Default de previsualización
        pages = 15 if modalidad == "creacion" else 65

    quote = calcular_creditos(pages, modalidad)
    credits_needed = quote["creditos"]
    can_process = (current_balance >= credits_needed)
    missing_credits = max(0, credits_needed - current_balance)

    return {
        "status": "success",
        "quote": quote,
        "current_balance": current_balance,
        "can_process": can_process,
        "missing_credits": missing_credits,
        "credits_needed": credits_needed
    }
