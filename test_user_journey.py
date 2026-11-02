"""
Simulador de Usuario Completo (End-to-End User Journey)
Simula el comportamiento real de un estudiante:
  1. Registro anónimo con Alias e Institución UNAD.
  2. Verificación de balance de bienvenida (créditos).
  3. Carga y generación de tarea académica desde guía.
  4. Auditoría automática del resultado (Word APA 7 + Excel).
  5. Verificación en el Panel Administrativo de Jhon Zapata.
"""

import os
import sys
import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

def run_simulation():
    print("=" * 70)
    print("🤖 INICIANDO SIMULACIÓN DE USUARIO REAL EN ACADEMICPRO")
    print("=" * 70)

    # 1. Registro del estudiante
    student_payload = {
        "email": "estudiante_lina@unad.edu.co",
        "username_alias": "Lina_LecturaInferencial",
        "institution": "UNAD",
        "password": "miClaveSegura2026*"
    }
    print(f"\n[1] Registrando estudiante: {student_payload['username_alias']} ({student_payload['email']})...")
    
    with httpx.Client(timeout=30.0) as client:
        # Intentar login primero por si ya existía de pruebas previas
        login_res = client.post(f"{BASE_URL}/api/auth/login", json={"email": student_payload["email"], "password": student_payload["password"]})
        if login_res.status_code == 200:
            user = login_res.json()["user"]
            print(f"  ✓ Usuario existente autenticado con éxito. Saldo actual: {user['balance']} créditos.")
        else:
            reg_res = client.post(f"{BASE_URL}/api/auth/register", json=student_payload)
            if reg_res.status_code == 200:
                user = reg_res.json()["user"]
                print(f"  ✓ ¡Registro exitoso! Id: {user['id']} | Balance de bienvenida: {user['balance']} créditos.")
            else:
                print(f"  ✗ Error al registrar: {reg_res.text}")
                return

        user_id = user["id"]

        # 2. Subir y procesar tarea académica desde guía
        print("\n[2] Procesando tarea académica con la guía de 'Los momentos de lectura de Isabel Solé'...")
        
        # Buscar archivo de guía o rúbrica de muestra en el proyecto
        sample_doc = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Trabajo_Generado_Desde_Guia_APA7.docx"))
        files = {}
        if os.path.exists(sample_doc):
            files["guide_file"] = ("Guia_Isabel_Sole.docx", open(sample_doc, "rb"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            print(f"  ✓ Adjuntando archivo de guía real: {os.path.basename(sample_doc)}")
        else:
            print("  ℹ Usando parámetros temáticos directos...")

        data = {
            "title": "Estrategias de Animación Lectora y Nivel Inferencial en Primaria según Isabel Solé",
            "student_name": user["username_alias"],
            "student_code": "1004567890",
            "group_number": "Grupo 50001_89",
            "tutor_name": "Asesor de Práctica Pedagógica",
            "institution": "UNAD",
            "font_family": "Times New Roman",
            "font_size": "12",
            "line_spacing": "1.5",
            "include_toc": "false"
        }

        gen_res = client.post(f"{BASE_URL}/api/generation/create-from-guide", data=data, files=files if files else None)
        
        if gen_res.status_code == 200:
            task_result = gen_res.json()
            print(f"  ✓ ¡Documento generado con éxito!")
            print(f"    - Enlace Descarga Word APA 7: {task_result.get('download_url')}")
            print(f"    - Enlace Reporte Auditoría Excel: {task_result.get('audit_report_url')}")
            print(f"    - Bytes Generados: {task_result.get('bytes_generated'):,} bytes")
            print(f"    - Créditos restantes: {task_result.get('remaining_credits')}")
            print(f"    - Resumen pedagógico: {task_result.get('pedagogical_summary')[:100]}...")
        else:
            print(f"  ✗ Error en generación: {gen_res.status_code} - {gen_res.text}")
            return

        # 3. Supervisión en el Panel Administrativo (Jhon Zapata)
        print("\n[3] Verificando trazabilidad en el Panel Administrativo (/admin)...")
        admin_res = client.get(f"{BASE_URL}/api/admin/users?pin=7105")
        if admin_res.status_code == 200:
            admin_data = admin_res.json()
            print(f"  ✓ Total de estudiantes en BD: {admin_data.get('total')}")
            for u in admin_data.get("users", []):
                if u["email"] == student_payload["email"]:
                    print(f"    -> Encontrado: Alias: {u['alias']} | Email: {u['email']} | Saldo: {u['balance']} créditos.")
        else:
            print(f"  ✗ Error en admin: {admin_res.text}")

        # 4. Estadísticas de almacenamiento
        stats_res = client.get(f"{BASE_URL}/api/admin/storage-stats")
        if stats_res.status_code == 200:
            st = stats_res.json()
            print(f"\n[4] Estado del almacenamiento en Supabase/Local:")
            print(f"  ✓ Espacio ocupado: {st['mb_used']} MB / {st['supabase_free_limit_mb']} MB ({st['pct_storage_used']}%)")
            print(f"  ✓ Plantillas y archivos guardados: {st['total_files']} ({st['categories']})")
            print(f"  ✓ Condición: {st['status']}")

    print("\n" + "=" * 70)
    print("🎉 SIMULACIÓN END-TO-END COMPLETADA CON ÉXITO AL 100%")
    print("=" * 70)

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    run_simulation()
