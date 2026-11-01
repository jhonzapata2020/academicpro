# 🎓 AcademicPro AI

> **Plataforma Integral de Asistencia, Generación y Auditoría de Trabajos de Grado y Actividades Académicas (UNAD & SENA).**

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)
![Normas APA 7](https://img.shields.io/badge/Normas_APA-7a_Edición_UNAD-16A34A.svg)
![Wompi](https://img.shields.io/badge/Wompi-Bancolombia_Payments-242625.svg)
![Nequi](https://img.shields.io/badge/Nequi-OCR_Receipt_Validator-FF0077.svg)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-Wompi_Design_System-38BDF8.svg)

---

## 🌟 Descripción General

**AcademicPro AI** es una solución EdTech full-stack de alto rendimiento diseñada para resolver la fricción metodológica, ortotipográfica y de formato en la educación superior y tecnológica (UNAD, SENA, Normales Superiores y universidades de América Latina). 

A diferencia de herramientas genéricas de IA que entregan texto plano sin rigor, AcademicPro integra motores nativos de manipulación XML (`python-docx`, `openpyxl`, `pypdf`) que estructuran documentos Word completos bajo las directrices estrictas del **Instructivo Oficial de Normas APA 7a Edición (UNAD)**, cotejan observaciones del jurado en Excel y atienden requerimientos específicos de los asesores.

---

## 🚀 Características Principales

### 1. Arquitectura de UI en 2 Estados (Zero Scroll - Wompi Style)
* **Diseño Idéntico a Wompi Bancolombia:** Tarjetas de onboarding de alta jerarquía visual con bordes de color diferenciados (Azul Cielo para Creación y Verde Lima para Corrección con badge de ahorro del 45%).
* **Acceso Directo:** Botón prominente de carga dentro de cada tarjeta que abre inmediatamente el explorador de archivos nativo.
* **Flujo en una Sola Pantalla:** La vista inicial y la vista de confirmación ocurren en el mismo viewport (`100vh`) sin barras de desplazamiento vertical molestas.

### 2. Motor de Cotización Dinámica en Tiempo Real (`pricing_engine.py`)
* **Regla Institucional:** 1 Crédito = **$10.000 COP**.
* **Detección Asíncrona de Páginas:** Cuenta las páginas reales de archivos `.docx` y `.pdf` al instante.
* **Tarifas Diferenciadas:**
  * **Corrección (Tarifa Preferencial):**
    * Hasta 50 páginas: **1 Crédito ($10.000 COP)**
    * Hasta 75 páginas: **2 Créditos ($20.000 COP)**
    * Hasta 100 páginas: **3 Créditos ($30.000 COP)**
    * Hasta 140 páginas: **8 Créditos ($80.000 COP)** (Tesis de grado estándar)
    * Más de 140 páginas: **10 Créditos ($100.000 COP)** (Tesis macro / posgrado)
  * **Creación desde Cero:**
    * Hasta 30 págs: 1 Crédito | Hasta 50 págs: 2 Créditos | Hasta 75 págs: 3 Créditos | Hasta 100 págs: 5 Créditos | Hasta 140 págs: 15 Créditos.

### 3. Validador Antifraude OCR de Comprobantes Nequi (`nequi_receipt_validator.py`)
* Extracción estructurada mediante visión artificial de comprobantes digitales (App Nequi) y tirillas físicas de Corresponsal Bancolombia.
* **Validación en 4 Capas:**
  1. **Anti-Replay:** Hash SHA-256 e indexación de referencia `M...` y RRN en SQLite para impedir reusar comprobantes.
  2. **Monto Exacto:** Validación del valor transferido ($50.000 COP / $120.000 COP).
  3. **Destino Autorizado:** Comprobación estricta del número de destino oficial (**`320 710 5618`**).
  4. **Ventana Temporal:** Rechazo de comprobantes con más de 48 horas de antigüedad.
* **Liberación Inmediata de Créditos:** Alta automática en la billetera virtual del estudiante al aprobarse el recibo.

### 4. Soporte STEM para Tareas de Cálculo y Física
* Generación de recuadros formales de instrucción para comprobaciones externas en **GeoGebra Clásico** y código Python para **Google Colab**, con placeholders delimitados para insertar capturas de pantalla.

---

## 📂 Estructura del Repositorio

```text
academicpro/
├── backend/
│   ├── core/
│   │   ├── engine_generator.py       # Motor APA 7 UNAD/SENA + Inyección de plantillas DOCX
│   │   ├── engine_auditor.py         # Auditor de tesis + Generador de reporte Excel
│   │   └── pricing_engine.py         # Motor de tarifas por páginas y créditos COP
│   ├── routers/
│   │   ├── auditing.py               # Endpoints de auditoría de tesis
│   │   ├── credits.py                # Endpoints de billetera, Wompi y recibos Nequi
│   │   ├── generation.py             # Endpoints de generación desde guía
│   │   └── quote.py                  # Cotización asíncrona en tiempo real
│   ├── services/
│   │   ├── nequi_receipt_validator.py# Escáner OCR y prevención de fraude financiero
│   │   ├── supabase_client.py        # Gestión de créditos y perfiles (Cloud + Local)
│   │   └── wompi_service.py          # Firmas de integridad y checkout Wompi
│   └── main.py                       # Servidor central FastAPI
├── frontend/
│   ├── static/
│   │   ├── css/style.css             # Estilos oficiales Wompi Bancolombia (Zero Scroll)
│   │   └── js/app.js                 # Controlador interactivo en 2 estados y cotizador
│   └── index.html                    # Dashboard principal responsivo
├── storage/
│   ├── outputs/                      # Documentos DOCX y reportes XLSX generados
│   ├── uploads/                      # Manuscritos y rúbricas recibidas
│   └── vouchers/                     # Comprobantes Nequi auditados
├── supabase/
│   └── schema.sql                    # Schema PostgreSQL para Supabase con RLS y triggers
├── .env.example                      # Plantilla de variables de entorno
├── .gitignore                        # Reglas de exclusión Git
├── requirements.txt                  # Dependencias oficiales de Python
├── start_app.py                      # Lanzador local en 1 solo clic
└── README.md                         # Documentación técnica del proyecto
```

---

## 🛠️ Instalación y Puesta en Marcha

### Prerrequisitos
* Python 3.10 o superior (Probado en Python 3.13)
* Git

### 1. Clonar el repositorio
```bash
git clone https://github.com/jhonzapata2020/academicpro.git
cd academicpro
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno (Opcional)
```bash
cp .env.example .env
```
*(La aplicación cuenta con fallback local en memoria y SQLite, permitiendo correr de inmediato sin configuración externa obligatoria).*

### 4. Iniciar el servidor de desarrollo
```bash
python start_app.py
```
Abre tu navegador en: **`http://localhost:8000`**

---

## 📊 Integración con Supabase (Producción)

Si deseas sincronizar con la nube de **Supabase**:
1. Crea un proyecto en [supabase.com](https://supabase.com).
2. Ve al **SQL Editor** y ejecuta el script [`supabase/schema.sql`](supabase/schema.sql).
3. Añade tus credenciales en el archivo `.env`:
   ```env
   SUPABASE_URL=https://tu-proyecto.supabase.co
   SUPABASE_KEY=tu-anon-key
   ```
El sistema asignará automáticamente **1 crédito gratuito de bienvenida** a cada estudiante que se registre con Google OAuth o correo institucional.

---

## 💳 Pasarela de Pagos

* **Wompi Bancolombia:** Soporta pagos con tarjeta de crédito/débito, PSE, Botón Bancolombia y Nequi.
* **Transferencia Directa Nequi:** Pagos inmediatos a la cuenta autorizada **`320 710 5618`** con validación OCR y auditoría de comprobantes en tiempo real.

---

## 📄 Licencia

Desarrollado bajo licencia MIT. Uso académico y comercial autorizado para **AcademicPro AI**.
