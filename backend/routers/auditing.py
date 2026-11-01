"""
Router: Endpoints de Auditoría y Corrección de Tesis de Grado (Modo 2)
"""

import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from backend.core.engine_auditor import audit_and_correct_thesis
from backend.services.supabase_client import supabase_service

router = APIRouter(prefix="/api/auditing", tags=["Auditoría de Tesis"])

def _get_storage_path(folder_name: str) -> str:
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        path = os.path.join("/tmp/academicpro_storage", folder_name)
    else:
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage", folder_name))
    try:
        os.makedirs(path, exist_ok=True)
    except (OSError, PermissionError):
        path = os.path.join("/tmp/academicpro_storage", folder_name)
        os.makedirs(path, exist_ok=True)
    return path

UPLOAD_DIR = _get_storage_path("uploads")
OUTPUT_DIR = _get_storage_path("outputs")

@router.post("/audit-thesis")
async def audit_thesis_endpoint(
    thesis_file: UploadFile = File(...),
    feedback_file: UploadFile = File(None),
    font_family: str = Form("Times New Roman"),
    font_size: int = Form(12),
    line_spacing: float = Form(1.5)
):
    user_id = "demo_user_1"
    cost = 5 # Auditar y corregir una tesis completa de 80-150 páginas consume 5 créditos

    # Verificar créditos
    has_credits = supabase_service.deduct_credits(user_id=user_id, cost=cost, is_premium_project=False)
    if not has_credits:
        raise HTTPException(
            status_code=402,
            detail="Saldo insuficiente de créditos para auditar una tesis completa (Requiere 5 créditos)."
        )

    task_id = str(uuid.uuid4())[:8]
    input_thesis_path = os.path.join(UPLOAD_DIR, f"{task_id}_{thesis_file.filename}")
    with open(input_thesis_path, "wb") as f:
        shutil.copyfileobj(thesis_file.file, f)

    feedback_path = None
    if feedback_file and feedback_file.filename:
        feedback_path = os.path.join(UPLOAD_DIR, f"{task_id}_{feedback_file.filename}")
        with open(feedback_path, "wb") as f:
            shutil.copyfileobj(feedback_file.file, f)

    output_docx_name = f"Tesis_Corregida_{task_id}_APA7.docx"
    output_excel_name = f"Reporte_Auditoria_{task_id}_AntesVsDespues.xlsx"
    output_docx_path = os.path.join(OUTPUT_DIR, output_docx_name)
    output_excel_path = os.path.join(OUTPUT_DIR, output_excel_name)

    audit_and_correct_thesis(
        input_docx_path=input_thesis_path,
        feedback_file_path=feedback_path,
        font_family=font_family,
        font_size=font_size,
        line_spacing=line_spacing,
        output_docx_path=output_docx_path,
        output_excel_path=output_excel_path
    )

    summary = (
        f"Se auditó y corrigió el manuscrito de grado. Se estandarizaron márgenes a 2.54 cm, "
        f"se unificó la tipografía {font_family} {font_size}pt con interlineado {line_spacing}, "
        f"se ajustaron títulos a Nivel 1 y 2, y se generó la matriz comparativa en Excel con los cambios realizados."
    )

    supabase_service.log_document_task(user_id, {
        "task_id": task_id,
        "title": thesis_file.filename,
        "mode": "auditor",
        "output_docx": output_docx_name,
        "output_excel": output_excel_name,
        "summary": summary
    })

    current_credits = supabase_service.get_user_credits(user_id)

    return {
        "status": "success",
        "task_id": task_id,
        "download_docx_url": f"/api/auditing/download/{output_docx_name}",
        "download_excel_url": f"/api/auditing/download/{output_excel_name}",
        "pedagogical_summary": summary,
        "remaining_credits": current_credits
    }

@router.get("/download/{filename}")
async def download_audited_file(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if filename.endswith(".xlsx"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return FileResponse(file_path, media_type=media_type, filename=filename)
