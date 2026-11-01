"""
Lanzador Maestro de la Aplicación AcademicPro AI
Ejecuta el servidor FastAPI en el puerto 8000 y abre la aplicación en el navegador.
"""

import os
import sys
import webbrowser
import uvicorn

# Asegurar que el directorio de Blueprint esté en el PATH de Python
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

if __name__ == "__main__":
    # Forzar codificación UTF-8 en Windows si es necesario
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 75)
    print("[+] INICIANDO ACADEMICPRO AI - PLATAFORMA SAAS UNAD & SENA")
    print("=" * 75)
    print("• Motor APA 7a Edicion: Calibrado segun Instructivo Oficial UNAD")
    print("• Backend API: FastAPI + Python-Docx + OpenPyXL + Supabase Engine")
    print("• Pasarela de Pagos: Wompi (Nequi / Daviplata / PSE)")
    print("• Servidor Local: http://localhost:8000")
    print("=" * 75)
    print("Presiona CTRL + C para detener el servidor.\n")

    # Iniciar servidor uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
