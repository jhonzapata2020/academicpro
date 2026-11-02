"""
Router: Endpoints de Autenticación de Estudiantes
Maneja Registro Anónimo (Alias), Login y Consulta de Perfil/Créditos
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from backend.services.auth_service import auth_service
from backend.services.email_service import email_service

router = APIRouter(prefix="/api/auth", tags=["Autenticación de Estudiantes"])

class RegisterPayload(BaseModel):
    email: str
    username_alias: str
    institution: str = "UNAD"
    password: str
    device_fingerprint: str = ""

class LoginPayload(BaseModel):
    email: str
    password: str

@router.post("/register")
async def register_student(payload: RegisterPayload, request: Request):
    try:
        client_ip = request.client.host if request.client else ""
        user = auth_service.register(
            email=payload.email,
            username_alias=payload.username_alias,
            institution=payload.institution,
            password=payload.password,
            device_fingerprint=payload.device_fingerprint,
            client_ip=client_ip
        )
        
        # Enviar correo oficial de bienvenida
        try:
            email_info = email_service.send_welcome_email(
                to_email=user["email"],
                username_alias=user["username_alias"],
                initial_credits=user["balance"]
            )
            user["email_status"] = email_info
        except Exception as mail_err:
            user["email_status"] = {"status": "skipped", "error": str(mail_err)}

        return {"status": "success", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno al registrar usuario.")

@router.post("/login")
async def login_student(payload: LoginPayload):
    try:
        user = auth_service.login(email=payload.email, password=payload.password)
        return {"status": "success", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno en autenticación.")

@router.get("/user/{user_id}")
async def get_user_profile(user_id: str):
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return {"status": "success", "user": user}
