"""
Servicio Core: Conexión con IA de Google Gemini para AcademicPro AI.
Permite:
  - Generación de secciones académicas rigurosas bajo APA 7.
  - Detección proactiva de vacíos o información faltante en la guía (Gap Analysis).
  - Llenado inteligente de matrices y tablas en plantillas Excel (.xlsx).
  - Sugerencia de prompts técnicos para generadores de imágenes (Midjourney/DALL-E).
"""

import os
import json
import httpx
from typing import List, Dict, Any, Optional

def _load_api_key() -> str:
    # 1. Variable de entorno directa
    key = os.getenv("GEMINI_API_KEY")
    if key and key.strip():
        return key.strip()
    
    # 2. Leer desde archivo .env si existe
    env_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
        os.path.abspath(os.path.join(os.getcwd(), ".env")),
        os.path.abspath(os.path.join(os.getcwd(), "Blueprint", ".env"))
    ]
    for ep in env_paths:
        if os.path.exists(ep):
            try:
                with open(ep, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GEMINI_API_KEY="):
                            k = line.split("=", 1)[1].strip()
                            if k:
                                return k
            except Exception:
                pass
    return os.getenv("GEMINI_API_KEY", "")

GEMINI_API_KEY = _load_api_key()

# Modelos en orden de prioridad y estabilidad
MODELS_TO_TRY = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-flash-latest"
]

class GeminiAIService:
    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def _call_gemini(self, prompt: str, system_prompt: Optional[str] = None, json_mode: bool = False) -> str:
        """Llama a la API de Gemini con rotación automática de modelos y control de errores."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY no configurada.")

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"INSTRUCCIÓN SISTEMA:\n{system_prompt}\n"}]})
            contents.append({"role": "model", "parts": [{"text": "Comprendido. Actuaré bajo este rol y normas estrictamente."}]})

        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3 if json_mode else 0.7,
                "maxOutputTokens": 3000
            }
        }
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        last_error = None
        for model in MODELS_TO_TRY:
            url = f"{self.base_url}/{model}:generateContent?key={self.api_key}"
            try:
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts and "text" in parts[0]:
                                return parts[0]["text"]
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text}"
            except Exception as e:
                last_error = str(e)

        raise RuntimeError(f"Error comunicando con Gemini API: {last_error}")

    def analyze_guide_and_detect_gaps(self, guide_text: str, student_context: str = "") -> Dict[str, Any]:
        """
        Analiza la guía de aprendizaje de la UNAD o el SENA.
        Detecta si faltan datos indispensables que el estudiante deba ingresar.
        """
        system_prompt = (
            "Eres el Auditor Académico Principal de AcademicPro AI para la UNAD y el SENA. "
            "Tu tarea es analizar guías de actividades, rúbricas y requerimientos."
        )
        prompt = f"""
Analiza la siguiente guía de aprendizaje y el contexto suministrado por el estudiante.
GUÍA DE APRENDIZAJE:
\"\"\"{guide_text[:4000]}\"\"\"

CONTEXTO DEL ESTUDIANTE:
\"\"\"{student_context}\"\"\"

Determina:
1. 'has_all_info': true si se puede elaborar la actividad completa sin ambigüedades, false si faltan datos críticos (ej. rol de trabajo colaborativo, tema específico elegido de una lista, datos de una empresa real a intervenir).
2. 'summary': Resumen en 2 renglones de lo que exige la guía.
3. 'missing_fields': Lista de preguntas para el estudiante si faltan datos. Cada elemento debe ser:
   {{"field_id": "...", "question": "...", "helper_text": "...", "type": "text|select", "options": ["..."]}}

Responde ÚNICAMENTE en JSON válido con las llaves: 'has_all_info', 'summary', 'missing_fields'.
"""
        raw = self._call_gemini(prompt, system_prompt=system_prompt, json_mode=True)
        try:
            return json.loads(raw)
        except Exception:
            return {"has_all_info": True, "summary": "Guía procesada correctamente.", "missing_fields": []}

    def fill_excel_matrix(self, headers: List[str], guide_text: str, row_count: int = 5) -> List[Dict[str, Any]]:
        """
        Genera el contenido académico fila por fila para diligenciar una matriz o plantilla en Excel (.xlsx).
        """
        system_prompt = "Eres un especialista académico que completa matrices metodológicas, marcos lógicos y cronogramas de la UNAD y el SENA."
        prompt = f"""
Basándote en la siguiente guía:
\"\"\"{guide_text[:3000]}\"\"\"

Debes llenar una matriz de Excel que tiene exactamente las siguientes columnas:
{json.dumps(headers, ensure_ascii=False)}

Genera exactamente {row_count} filas realistas, exhaustivas, con rigor profesional.
Devuelve ÚNICAMENTE un arreglo JSON de objetos, donde cada objeto tenga como llaves los nombres exactos de las columnas.
"""
        raw = self._call_gemini(prompt, system_prompt=system_prompt, json_mode=True)
        try:
            res = json.loads(raw)
            if isinstance(res, list):
                return res
            elif isinstance(res, dict) and "filas" in res:
                return res["filas"]
            return []
        except Exception:
            return []

    def generate_image_prompt(self, topic: str, institution: str = "UNAD") -> str:
        """
        Genera un prompt optimizado para generadores de imágenes (Midjourney, DALL-E) según la temática académica.
        """
        prompt = (
            f"Genera un prompt en inglés y español para Midjourney/DALL-E que cree un diagrama conceptual o infografía limpia "
            f"sobre: '{topic}' para una tarea académica en {institution}. Estilo minimalista, flat vector, académico, sin texto ilegible. "
            f"Devuelve solo el texto del prompt sin introducciones."
        )
        return self._call_gemini(prompt).strip()

ai_service = GeminiAIService()
