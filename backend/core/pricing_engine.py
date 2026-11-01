"""
Módulo Core: pricing_engine.py
Motor de Tarifas y Reglas Financieras de AcademicPro

Escala de Créditos Oficial:
1 Crédito = $10.000 COP

Escala Base (Creación desde Guía / Tarifas Oficiales):
- 1 a 12 páginas (ensayos cortos, foros, fichas de 3 a 5 págs): 1 crédito ($10.000 COP)
- 13 a 30 páginas (tareas regulares de curso completo): 2 créditos ($20.000 COP)
- 31 a 50 páginas: 3 créditos ($30.000 COP)
- 51 a 75 páginas: 5 créditos ($50.000 COP)
- 76 a 100 páginas: 8 créditos ($80.000 COP)
- 101 a 140 páginas: 15 créditos ($150.000 COP)
- Más de 140 páginas: 17 créditos ($170.000 COP)

Escala Preferencial (Auditoría y Corrección de Documento Existente):
- 1 a 12 páginas: 1 crédito ($10.000 COP)
- 13 a 30 páginas: 2 créditos ($20.000 COP)
- 31 a 50 páginas: 2 créditos ($20.000 COP) - Ahorro del 33%
- 51 a 75 páginas: 3 créditos ($30.000 COP) - Ahorro del 40%
- 76 a 100 páginas: 5 créditos ($50.000 COP) - Ahorro del 38%
- 101 a 140 páginas: 8 créditos ($80.000 COP) - Ahorro del 47%
- Más de 140 páginas: 10 créditos ($100.000 COP) - Ahorro del 41%
"""

import docx
from pypdf import PdfReader
import io

def calcular_creditos(paginas: int, modalidad: str = "creacion") -> dict:
    """
    Calcula los créditos requeridos según la extensión en páginas y modalidad del trabajo.
    1 Crédito = $10.000 COP
    """
    if paginas <= 0:
        raise ValueError("El documento debe tener al menos 1 página.")

    modalidad_clean = modalidad.lower().strip() if modalidad else "creacion"

    if modalidad_clean == "correccion":
        # Corrección de documento existente (con tarifa preferencial para tesis extensas)
        if paginas <= 12:
            creditos = 1   # $10.000 COP
        elif paginas <= 30:
            creditos = 2   # $20.000 COP (Garantizado: 13 a 30 págs = 2 créditos)
        elif paginas <= 50:
            creditos = 2   # $20.000 COP
        elif paginas <= 75:
            creditos = 3   # $30.000 COP
        elif paginas <= 100:
            creditos = 5   # $50.000 COP
        elif paginas <= 140:
            creditos = 8   # $80.000 COP
        else:
            creditos = 10  # $100.000 COP
    else:
        # Creación desde Guía (Nueva Regla Base oficial)
        if paginas <= 12:
            creditos = 1   # $10.000 COP (Ensayos cortos, foros, fichas de 3 a 5 págs)
        elif paginas <= 30:
            creditos = 2   # $20.000 COP (Tareas regulares de curso completo)
        elif paginas <= 50:
            creditos = 3   # $30.000 COP
        elif paginas <= 75:
            creditos = 5   # $50.000 COP
        elif paginas <= 100:
            creditos = 8   # $80.000 COP
        elif paginas <= 140:
            creditos = 15  # $150.000 COP
        else:
            creditos = 17  # $170.000 COP

    costo_cop = creditos * 10000

    return {
        "paginas": paginas,
        "modalidad": modalidad_clean,
        "creditos": creditos,
        "costo_cop": costo_cop,
        "costo_formateado": f"${costo_cop:,.0f} COP".replace(",", "."),
        "tier_label": get_tier_label(paginas)
    }

def get_tier_label(paginas: int) -> str:
    if paginas <= 12:
        return "Micro-ensayo / Ficha (<12 págs)"
    elif paginas <= 30:
        return "Tarea Regular de Curso (13-30 págs)"
    elif paginas <= 50:
        return "Trabajo Extenso / Anteproyecto (31-50 págs)"
    elif paginas <= 75:
        return "Monografía / Tesis Mediana (51-75 págs)"
    elif paginas <= 100:
        return "Tesis de Grado Estándar (76-100 págs)"
    elif paginas <= 140:
        return "Macro-Tesis de Posgrado (101-140 págs)"
    else:
        return "Investigación Exhaustiva (>140 págs)"

def estimate_document_pages(file_bytes: bytes, filename: str) -> int:
    """
    Estima o detecta de forma precisa el número de páginas de un archivo DOCX o PDF.
    """
    fname = filename.lower()
    if fname.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            return max(1, len(reader.pages))
        except Exception:
            return 1
    elif fname.endswith(".docx") or fname.endswith(".doc"):
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            total_words = 0
            for p in doc.paragraphs:
                total_words += len(p.text.split())
            for t in doc.tables:
                for row in t.rows:
                    for cell in row.cells:
                        total_words += len(cell.text.split())
            # En tipografía académica estándar APA 7 (Times 12pt o Arial 11pt, 1.5 espacios),
            # cada página contiene un promedio de 250 a 280 palabras.
            pages = max(1, round(total_words / 260))
            return pages
        except Exception:
            return 1
    return 1
