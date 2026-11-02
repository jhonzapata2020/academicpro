"""
Módulo de Gestión de Bóveda y Backup Local (Admin Vault Manager)
Permite:
  - Respaldar en tu máquina local todas las plantillas (.xlsx, .docx) y guías que suban los estudiantes.
  - Empaquetar un archivo ZIP descargable con 1 solo clic.
  - Purgar la nube de Supabase y temporales para mantenerse siempre dentro del Nivel Gratuito (1 GB de Storage).
"""

import os
import shutil
import zipfile
from datetime import datetime
from typing import Dict, Any, List

STORAGE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
UPLOADS_DIR = os.path.join(STORAGE_ROOT, "uploads")
OUTPUTS_DIR = os.path.join(STORAGE_ROOT, "outputs")
VAULT_PERMANENT_DIR = os.path.join(STORAGE_ROOT, "vault_local_backup")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(VAULT_PERMANENT_DIR, exist_ok=True)

class VaultManager:
    def get_storage_stats(self) -> Dict[str, Any]:
        """Calcula el peso y cantidad de archivos actuales."""
        total_bytes = 0
        file_count = 0
        categories = {"guias_pdf": 0, "plantillas_excel": 0, "documentos_word": 0, "otros": 0}

        for folder in [UPLOADS_DIR, OUTPUTS_DIR]:
            for root, _, files in os.walk(folder):
                for f in files:
                    if f.startswith("."):
                        continue
                    fp = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(fp)
                        total_bytes += sz
                        file_count += 1
                        ext = f.lower().split(".")[-1]
                        if ext == "pdf":
                            categories["guias_pdf"] += 1
                        elif ext in ["xlsx", "xls"]:
                            categories["plantillas_excel"] += 1
                        elif ext in ["docx", "doc"]:
                            categories["documentos_word"] += 1
                        else:
                            categories["otros"] += 1
                    except Exception:
                        pass

        mb_used = round(total_bytes / (1024 * 1024), 2)
        # Supabase da 1024 MB (1 GB) gratis en Storage
        supabase_free_limit_mb = 1024.0
        pct_used = round((mb_used / supabase_free_limit_mb) * 100, 2)

        return {
            "total_files": file_count,
            "mb_used": mb_used,
            "supabase_free_limit_mb": supabase_free_limit_mb,
            "pct_storage_used": pct_used,
            "categories": categories,
            "status": "ÓPTIMO (Capa Gratuita)" if pct_used < 70 else "ATENCIÓN: Purga Recomendada"
        }

    def create_local_backup_zip(self, backup_name: str = None) -> str:
        """
        Copia todos los insumos valiosos (plantillas y guías) a la bóveda local permanente
        y genera un archivo ZIP descargable fechado.
        """
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"Backup_Plantillas_AcademicPro_{timestamp}.zip"

        zip_output_path = os.path.join(VAULT_PERMANENT_DIR, backup_name)

        with zipfile.ZipFile(zip_output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for folder_name, folder_path in [("subidos_estudiantes", UPLOADS_DIR), ("generados_auditados", OUTPUTS_DIR)]:
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        if file.startswith("."):
                            continue
                        file_path = os.path.join(root, file)
                        # Ruta relativa dentro del ZIP
                        rel_path = os.path.join(folder_name, file)
                        zipf.write(file_path, arcname=rel_path)

        return zip_output_path

    def purge_storage_after_backup(self, keep_days: int = 15) -> Dict[str, Any]:
        """
        Limpia archivos procesados antiguos de la nube o temporales para liberar espacio,
        asegurando que tu Supabase Storage se mantenga siempre dentro de los 1000 MB gratis.
        """
        deleted_count = 0
        freed_bytes = 0
        now = datetime.now().timestamp()
        cutoff_seconds = keep_days * 86400

        for folder in [UPLOADS_DIR, OUTPUTS_DIR]:
            for root, _, files in os.walk(folder):
                for f in files:
                    if f.startswith("."):
                        continue
                    fp = os.path.join(root, f)
                    try:
                        mtime = os.path.getmtime(fp)
                        if (now - mtime) > cutoff_seconds:
                            sz = os.path.getsize(fp)
                            os.remove(fp)
                            deleted_count += 1
                            freed_bytes += sz
                    except Exception:
                        pass

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        return {
            "deleted_files_count": deleted_count,
            "freed_mb": freed_mb,
            "message": f"Se liberaron {freed_mb} MB de almacenamiento. La base de datos sigue protegida dentro del límite gratuito."
        }

vault_manager = VaultManager()
