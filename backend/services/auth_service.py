"""
Servicio de Autenticación Anónima y Segura para Estudiantes (AcademicPro AI)
Blindaje de Identidad:
  - Solo solicita: Correo, Alias / Username, Institución y Contraseña.
  - No expone nombres reales para proteger la privacidad académica del estudiante.
  - Asigna 2 créditos gratuitos de bienvenida para pruebas.
"""

import os
import hashlib
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

def _get_auth_db_path() -> str:
    """Retorna la ruta adecuada para la base de datos de usuarios (local o /tmp para Vercel)."""
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        tmp_dir = "/tmp/academicpro_storage"
        os.makedirs(tmp_dir, exist_ok=True)
        return os.path.join(tmp_dir, "academicpro_auth.db")

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
    try:
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, "academicpro_auth.db")
    except (OSError, PermissionError):
        tmp_dir = "/tmp/academicpro_storage"
        os.makedirs(tmp_dir, exist_ok=True)
        return os.path.join(tmp_dir, "academicpro_auth.db")

DB_PATH = _get_auth_db_path()

ADMIN_PIN = os.getenv("ADMIN_PIN", "7105") # Clave secreta de Jhon Zapata

def _hash_password(password: str) -> str:
    salt = "academicpro_secret_salt_2026"
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

def _init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # Tabla de Usuarios Estudiantes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                username_alias TEXT NOT NULL,
                institution TEXT NOT NULL DEFAULT 'UNAD',
                password_hash TEXT NOT NULL,
                balance INT NOT NULL DEFAULT 2,
                is_tester BOOLEAN DEFAULT 1,
                device_fingerprint TEXT,
                client_ip TEXT,
                created_at TEXT NOT NULL
            )
        """)
        # Asegurar migración de columnas si la tabla ya existía
        try:
            cur.execute("ALTER TABLE users ADD COLUMN device_fingerprint TEXT")
        except Exception:
            pass
        try:
            cur.execute("ALTER TABLE users ADD COLUMN client_ip TEXT")
        except Exception:
            pass
        # Tabla de Historial de Tareas y Documentos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_tasks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                email TEXT NOT NULL,
                title TEXT NOT NULL,
                mode TEXT NOT NULL,
                docx_filename TEXT,
                excel_filename TEXT,
                audit_score INT DEFAULT 100,
                summary TEXT,
                created_at TEXT NOT NULL
            )
        """)
        # Tabla de Pagos Nequi Registrados
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nequi_vouchers (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                email TEXT NOT NULL,
                package_id TEXT NOT NULL,
                amount_cop INT NOT NULL,
                voucher_filename TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING_APPROVAL',
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print("Aviso: SQLite temporal para auth en Vercel:", e)

_init_db()

class AuthService:
    def register(self, email: str, username_alias: str, institution: str, password: str, device_fingerprint: str = "", client_ip: str = "") -> Dict[str, Any]:
        email_clean = email.strip().lower()
        alias_clean = username_alias.strip() or "EstudianteAnonimo"
        inst_clean = institution.strip().upper() or "UNAD"

        if not email_clean or not password:
            raise ValueError("El correo y la contraseña son obligatorios.")

        pwd_hash = _hash_password(password)
        user_id = str(uuid.uuid4())[:12]
        now = datetime.now().isoformat()

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Blindaje anti-abuso: Comprobar si este dispositivo o IP ya reclamó el bono de bienvenida
        initial_balance = 2
        welcome_msg = "Registro exitoso. Se asignaron 2 créditos de bienvenida para tus pruebas."
        
        if device_fingerprint or client_ip:
            try:
                cur.execute("SELECT id FROM users WHERE (device_fingerprint = ? AND device_fingerprint != '') OR (client_ip = ? AND client_ip != '') LIMIT 1", (device_fingerprint, client_ip))
                existing_dev = cur.fetchone()
                if existing_dev:
                    initial_balance = 0
                    welcome_msg = "Cuenta creada. (Aviso: El bono gratuito de bienvenida ya fue reclamado previamente en este dispositivo)."
            except Exception:
                pass

        try:
            cur.execute("""
                INSERT INTO users (id, email, username_alias, institution, password_hash, balance, is_tester, device_fingerprint, client_ip, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """, (user_id, email_clean, alias_clean, inst_clean, pwd_hash, initial_balance, device_fingerprint, client_ip, now))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError("Este correo ya se encuentra registrado. Por favor inicia sesión.")
        
        conn.close()
        return {
            "id": user_id,
            "email": email_clean,
            "username_alias": alias_clean,
            "institution": inst_clean,
            "balance": initial_balance,
            "message": welcome_msg
        }

    def login(self, email: str, password: str) -> Dict[str, Any]:
        email_clean = email.strip().lower()
        pwd_hash = _hash_password(password)

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, email, username_alias, institution, balance, is_tester FROM users WHERE email = ? AND password_hash = ?", (email_clean, pwd_hash))
        row = cur.fetchone()
        conn.close()

        if not row:
            raise ValueError("Credenciales inválidas. Revisa tu correo o contraseña.")

        return {
            "id": row[0],
            "email": row[1],
            "username_alias": row[2],
            "institution": row[3],
            "balance": row[4],
            "is_tester": bool(row[5])
        }

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, email, username_alias, institution, balance, is_tester FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row[0],
            "email": row[1],
            "username_alias": row[2],
            "institution": row[3],
            "balance": row[4],
            "is_tester": bool(row[5])
        }

    def deduct_credits(self, user_id: str, cost: int) -> bool:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT balance, is_tester FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return False
        
        balance, is_tester = row
        # Si es tester activo, permitimos procesar sin trabar al usuario
        if is_tester:
            cur.execute("UPDATE users SET balance = MAX(0, balance - ?) WHERE id = ?", (cost, user_id))
            conn.commit()
            conn.close()
            return True

        if balance < cost:
            conn.close()
            return False

        cur.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (cost, user_id))
        conn.commit()
        conn.close()
        return True

    def add_credits_to_user(self, user_id_or_email: str, amount: int) -> bool:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("UPDATE users SET balance = balance + ? WHERE id = ? OR email = ?", (amount, user_id_or_email, user_id_or_email.lower()))
        affected = cur.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def list_all_users_for_admin(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, email, username_alias, institution, balance, created_at FROM users ORDER BY created_at DESC")
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "id": r[0],
                "email": r[1],
                "alias": r[2],
                "institution": r[3],
                "balance": r[4],
                "created_at": r[5]
            }
            for r in rows
        ]

    def record_user_task(self, user_id: str, email: str, title: str, mode: str, docx_filename: str, excel_filename: str, summary: str):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        task_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        cur.execute("""
            INSERT INTO user_tasks (id, user_id, email, title, mode, docx_filename, excel_filename, summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (task_id, user_id, email, title, mode, docx_filename, excel_filename, summary, now))
        conn.commit()
        conn.close()

    def list_all_tasks_for_admin(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, user_id, email, title, mode, docx_filename, excel_filename, summary, created_at FROM user_tasks ORDER BY created_at DESC")
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "id": r[0],
                "user_id": r[1],
                "email": r[2],
                "title": r[3],
                "mode": r[4],
                "docx_filename": r[5],
                "excel_filename": r[6],
                "summary": r[7],
                "created_at": r[8]
            }
            for r in rows
        ]

auth_service = AuthService()
