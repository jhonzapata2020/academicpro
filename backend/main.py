"""
Servidor Principal FastAPI - AcademicPro AI
Monta las APIs de generación, auditoría, créditos Wompi y sirve el frontend estático.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "AcademicPro AI backend en línea. Frontend no encontrado."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
