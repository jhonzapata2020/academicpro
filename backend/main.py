"""
Servidor Principal FastAPI - AcademicPro AI
Monta las APIs de generación, auditoría, créditos Wompi y sirve el frontend estático.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from backend.routers import generation, auditing, credits, quote, webhook_integromat

app = FastAPI(
    title="AcademicPro AI API",
    description="Plataforma SaaS de Generación y Auditoría de Trabajos de Grado y Actividades Académicas (UNAD/SENA)",
    version="1.0.0"
)

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir Routers
app.include_router(generation.router)
app.include_router(auditing.router)
app.include_router(credits.router)
app.include_router(quote.router)
app.include_router(webhook_integromat.router)

# Rutas estáticas del frontend
def _find_frontend_dir() -> str:
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend")),
        os.path.abspath(os.path.join(os.getcwd(), "frontend")),
        "/var/task/frontend"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

FRONTEND_DIR = _find_frontend_dir()
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AcademicPro AI API", "version": "1.0.0"}

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        except Exception:
            return FileResponse(index_file)
    return HTMLResponse(content="<h1>AcademicPro AI en línea</h1><p>Frontend inicializado.</p>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
