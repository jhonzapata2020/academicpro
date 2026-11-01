"""
Servicio: Cliente Supabase (Gestión de Autenticación, Créditos y Base de Datos)
Incluye modo híbrido:
    - Modo Producción: Conexión oficial a Supabase Cloud con URL y ANON/SERVICE KEY.
    - Modo Local Dev: Almacenamiento local con billetera activa (1 crédito de bienvenida y recarga simulada).
"""

import os
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Estado de desarrollo local en memoria
_LOCAL_USERS = {
    "demo_user_1": {
        "id": "demo_user_1",
        "email": "estudiante@unad.edu.co",
        "full_name": "Juan Esteban Torres Asprilla",
        "institution": "UNAD",
        "balance": 4,                    # 4 créditos regulares disponibles
        "premium_projects_balance": 1,  # 1 pase de Macroproyecto disponible
        "history": []
    }
}

class SupabaseService:
    def __init__(self):
        self.client = None
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                from supabase import create_client
                self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("Conectado exitosamente a Supabase Cloud.")
            except Exception as e:
                print("Aviso: No se pudo conectar a Supabase Cloud. Operando en modo Local Mock:", e)

    def get_user_credits(self, user_id="demo_user_1"):
        """Retorna el balance de créditos del usuario."""
        if self.client:
            try:
                res = self.client.table("user_credits").select("*").eq("user_id", user_id).single().execute()
                if res.data:
                    return {
                        "balance": res.data.get("balance", 0),
                        "premium_projects_balance": res.data.get("premium_projects_balance", 0)
                    }
            except Exception as e:
                print("Error consultando créditos en Supabase:", e)

        # Fallback local
        user = _LOCAL_USERS.get(user_id, _LOCAL_USERS["demo_user_1"])
        return {
            "balance": user["balance"],
            "premium_projects_balance": user["premium_projects_balance"]
        }

    def deduct_credits(self, user_id="demo_user_1", cost=1, is_premium_project=False):
        """Descuenta créditos según el tipo de trabajo."""
        if self.client:
            try:
                # Llamada RPC a la función SQL de Supabase
                res = self.client.rpc("deduct_credit", {"p_user_id": user_id, "p_cost": cost}).execute()
                return res.data
            except Exception as e:
                print("Error en RPC deduct_credit Supabase:", e)

        # Fallback local
        user = _LOCAL_USERS.get(user_id, _LOCAL_USERS["demo_user_1"])
        if is_premium_project:
            if user["premium_projects_balance"] >= 1:
                user["premium_projects_balance"] -= 1
                return True
            return False
        else:
            if user["balance"] >= cost:
                user["balance"] -= cost
                return True
            return False

    def recharge_credits(self, user_id="demo_user_1", pack_type="STANDARD_PACK_5"):
        """Recarga créditos tras aprobación de pago en Wompi."""
        user = _LOCAL_USERS.get(user_id, _LOCAL_USERS["demo_user_1"])
        if pack_type == "STANDARD_PACK_5":
            user["balance"] += 5
            return {"status": "ok", "new_balance": user["balance"], "added": 5}
        elif pack_type == "PREMIUM_PROJECT_PASS":
            user["premium_projects_balance"] += 1
            return {"status": "ok", "new_premium_balance": user["premium_projects_balance"], "added": 1}
        return {"status": "error", "message": "Paquete desconocido"}

    def log_document_task(self, user_id="demo_user_1", task_data=None):
        """Registra el trabajo en el historial."""
        user = _LOCAL_USERS.get(user_id, _LOCAL_USERS["demo_user_1"])
        if task_data:
            task_data["created_at"] = datetime.now().isoformat()
            user["history"].append(task_data)
        return True

supabase_service = SupabaseService()
