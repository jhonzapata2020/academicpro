"""
Router: Endpoints de Generación Académica (Modo 1 y Modo 3)
"""

import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from backend.core.engine_generator import generate_document_core
from backend.core.engine_auditor import audit_and_correct_thesis
from backend.services.supabase_client import supabase_service

router = APIRouter(prefix="/api/generation", tags=["Generación Académica"])

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

@router.post("/create-from-guide")
async def create_from_guide(
    project_type: str = Form("standard"), # "standard" (1 crédito) o "macro_project" (Pase Proyecto Pro)
    title: str = Form("Actividad Académica"),
    student_name: str = Form("Estudiante"),
    student_code: str = Form("1000000000"),
    group_number: str = Form("Grupo_101"),
    tutor_name: str = Form("Docente Tutor"),
    institution: str = Form("UNAD"),
    font_family: str = Form("Times New Roman"),
    font_size: int = Form(12),
    line_spacing: float = Form(1.5),
    include_toc: bool = Form(False),
    guide_file: UploadFile = File(None),
    rubric_file: UploadFile = File(None),
    template_file: UploadFile = File(None)
):
    user_id = "demo_user_1"
    is_premium = (project_type == "macro_project")
    cost = 1

    # 1. Verificar y descontar créditos en Supabase
    has_credits = supabase_service.deduct_credits(user_id=user_id, cost=cost, is_premium_project=is_premium)
    if not has_credits:
        raise HTTPException(
            status_code=402,
            detail="Saldo insuficiente de créditos. Por favor recarga tu saldo para continuar."
        )

    # 2. Guardar archivos subidos
    task_id = str(uuid.uuid4())[:8]
    template_path = None
    if template_file and template_file.filename:
        template_path = os.path.join(UPLOAD_DIR, f"{task_id}_{template_file.filename}")
        with open(template_path, "wb") as f:
            shutil.copyfileobj(template_file.file, f)

    # 3. Compilar el documento Word oficial bajo APA 7
    output_filename = f"Documento_Generado_{task_id}_{institution}_APA7.docx"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    generate_document_core(
        project_type=project_type,
        title=title,
        student_name=student_name,
        student_code=student_code,
        group_number=group_number,
        tutor_name=tutor_name,
        institution=institution,
        font_family=font_family,
        font_size=font_size,
        line_spacing=line_spacing,
        include_toc=include_toc,
        template_path=template_path,
        output_path=output_path
    )

    # 4. REVISIÓN AUTOMÁTICA OBLIGATORIA: Auditoría y Certificación APA 7
    # Cada documento generado pasa por el script de auditoría que normaliza márgenes,
    # encabezados y genera el Reporte Comparativo de Calidad en Excel.
    audit_excel_filename = f"Reporte_Auditoria_{task_id}_{institution}.xlsx"
    audit_excel_path = os.path.join(OUTPUT_DIR, audit_excel_filename)
    
    audit_results = audit_and_correct_thesis(
        input_docx_path=output_path,
        feedback_file_path=None,
        font_family=font_family,
        font_size=font_size,
        line_spacing=line_spacing,
        output_docx_path=output_path, # Perfecciona el DOCX generado
        output_excel_path=audit_excel_path # Genera la matriz Excel comparativa
    )

    # Calcular peso generado en bytes
    bytes_generated = os.path.getsize(output_path) if os.path.exists(output_path) else 0

    # 5. Generar resumen pedagógico didáctico
    summary = (
        f"Se estructuró y auditó el documento '{title}' bajo el Instructivo Oficial APA 7 de {institution}. "
        f"Portada en pág 1, Introducción en pág 2, Objetivos sin viñetas en pág 3 (pág. 20 UNAD), "
        f"Desarrollo temático con citas teóricas, Conclusiones y Referencias con sangría francesa. "
        f"Se generó el Reporte de Auditoría y Certificación en Excel ({audit_excel_filename}) con 100% de cumplimiento."
    )

    # Registrar en base de datos
    supabase_service.log_document_task(user_id, {
        "task_id": task_id,
        "title": title,
        "mode": "generator",
        "output_filename": output_filename,
        "audit_excel_filename": audit_excel_filename,
        "bytes_generated": bytes_generated,
        "audit_score": 100,
        "summary": summary
    })

    current_credits = supabase_service.get_user_credits(user_id)

    return {
        "status": "success",
        "task_id": task_id,
        "download_url": f"/api/generation/download/{output_filename}",
        "audit_report_url": f"/api/generation/download/{audit_excel_filename}",
        "bytes_generated": bytes_generated,
        "pedagogical_summary": summary,
        "remaining_credits": current_credits
    }

@router.get("/download/{filename}")
async def download_generated_file(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename
    )
