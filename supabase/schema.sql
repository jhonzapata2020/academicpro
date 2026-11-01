-- =========================================================================
-- ACADEMICPRO AI - SUPABASE DATABASE SCHEMA (PRODUCTION-READY)
-- PostgreSQL + Row Level Security (RLS) + Wompi Payment Sync + Credit Counter
-- =========================================================================

-- Habilitar extensión UUID si no está activa
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. TABLA DE PERFILES DE USUARIOS (Sincronizada con auth.users de Supabase)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    institution TEXT DEFAULT 'UNAD',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. TABLA DE BILLETERA DE CRÉDITOS ACADÉMICOS MULTI-TIER
CREATE TABLE IF NOT EXISTS public.user_credits (
    user_id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    balance INT NOT NULL DEFAULT 1,                     -- Créditos regulares (1 Gratis al registrarse)
    premium_projects_balance INT NOT NULL DEFAULT 0,    -- Pases de Proyectos de Grado / Tesis desde Cero
    total_earned INT NOT NULL DEFAULT 1,
    total_spent INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. TABLA DE TRANSACCIONES Y PAGOS (WOMPI / NEQUI / PSE)
CREATE TABLE IF NOT EXISTS public.transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    reference TEXT NOT NULL UNIQUE, -- Código de referencia único enviado a Wompi
    wompi_id TEXT UNIQUE,           -- ID oficial de la transacción en Wompi
    tier_type TEXT NOT NULL DEFAULT 'STANDARD_PACK_5', -- STANDARD_PACK_5 ($50k) o PREMIUM_PROJECT_PASS ($120k)
    amount_in_cents BIGINT NOT NULL, -- 5000000 ($50.000 COP) o 12000000 ($120.000 COP)
    currency TEXT DEFAULT 'COP',
    payment_method_type TEXT,       -- NEQUI, BANCOLOMBIA_COLLECT, PSE, CARD
    status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING, APPROVED, DECLINED, VOIDED
    credits_granted INT NOT NULL DEFAULT 5, -- 5 créditos estándar o 1 pase de macroproyecto
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. HISTORIAL DE TRABAJOS Y DOCUMENTOS PROCESADOS
CREATE TABLE IF NOT EXISTS public.document_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    mode TEXT NOT NULL CHECK (mode IN ('generator', 'auditor')), -- Generador desde Guía o Auditor de Tesis
    title TEXT NOT NULL,
    institution TEXT NOT NULL, -- UNAD, SENA, UNIVERSIDAD_GENERAL
    font_family TEXT DEFAULT 'Times New Roman',
    include_toc BOOLEAN DEFAULT FALSE,
    output_docx_path TEXT,
    output_excel_path TEXT,
    pedagogical_summary TEXT,
    status TEXT NOT NULL DEFAULT 'COMPLETED',
    credits_cost INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =========================================================================
-- TRIGGER AUTOMÁTICO: ONBOARDING CON 1 CRÉDITO GRATIS
-- =========================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Crear perfil público
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1))
    );

    -- Asignar automáticamente 1 crédito gratuito de prueba
    INSERT INTO public.user_credits (user_id, balance, total_earned, total_spent)
    VALUES (NEW.id, 1, 1, 0);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Disparador tras inserción en auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- =========================================================================
-- FUNCIÓN TRANSACCIONAL: DESCONTAR CRÉDITO AL PROCESAR
-- =========================================================================
CREATE OR REPLACE FUNCTION public.deduct_credit(p_user_id UUID, p_cost INT DEFAULT 1)
RETURNS BOOLEAN AS $$
DECLARE
    current_bal INT;
BEGIN
    SELECT balance INTO current_bal FROM public.user_credits WHERE user_id = p_user_id FOR UPDATE;

    IF current_bal IS NULL OR current_bal < p_cost THEN
        RETURN FALSE; -- Saldo insuficiente
    END IF;

    UPDATE public.user_credits
    SET balance = balance - p_cost,
        total_spent = total_spent + p_cost,
        updated_at = NOW()
    WHERE user_id = p_user_id;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =========================================================================
-- FUNCIÓN TRANSACCIONAL: ACREDITAR CRÉDITOS TRAS APROBACIÓN WOMPI (WEBHOOK)
-- =========================================================================
CREATE OR REPLACE FUNCTION public.process_wompi_payment(
    p_reference TEXT,
    p_wompi_id TEXT,
    p_status TEXT,
    p_payment_type TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_user_id UUID;
    v_credits INT;
    v_curr_status TEXT;
BEGIN
    SELECT user_id, credits_granted, status 
    INTO v_user_id, v_credits, v_curr_status
    FROM public.transactions
    WHERE reference = p_reference
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    -- Si ya fue aprobada previamente, evitar duplicidad
    IF v_curr_status = 'APPROVED' THEN
        RETURN TRUE;
    END IF;

    -- Actualizar estado de la transacción
    UPDATE public.transactions
    SET wompi_id = p_wompi_id,
        status = p_status,
        payment_method_type = p_payment_type,
        updated_at = NOW()
    WHERE reference = p_reference;

    -- Si el pago fue aprobado, sumar los créditos
    IF p_status = 'APPROVED' THEN
        UPDATE public.user_credits
        SET balance = balance + v_credits,
            total_earned = total_earned + v_credits,
            updated_at = NOW()
        WHERE user_id = v_user_id;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =========================================================================
-- ROW LEVEL SECURITY (SEGURIDAD PARA EL FRONTEND)
-- =========================================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_credits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_tasks ENABLE ROW LEVEL SECURITY;

-- Políticas de acceso para el usuario autenticado
CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own credits" ON public.user_credits FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own transactions" ON public.transactions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert pending transactions" ON public.transactions FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own document tasks" ON public.document_tasks FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create document tasks" ON public.document_tasks FOR INSERT WITH CHECK (auth.uid() = user_id);

-- =========================================================================
-- 5. TABLAS ESPECÍFICAS PARA AUTOMATIZACIÓN DE INTEGROMAT (MAKE)
-- Sincronización directa con Webhooks, Nequi y WhatsApp Directo de Jhon
-- =========================================================================

-- Tabla de Usuarios consumida por Make
CREATE TABLE IF NOT EXISTS public.usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre TEXT NOT NULL,
    celular TEXT NOT NULL,
    email TEXT UNIQUE,
    creditos_disponibles INT DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de Trabajos Académicos
CREATE TABLE IF NOT EXISTS public.trabajos_academicos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES public.usuarios(id) ON DELETE CASCADE,
    tipo_servicio TEXT NOT NULL CHECK (tipo_servicio IN ('creacion', 'correccion')),
    nombre_archivo TEXT,
    paginas_generadas INT NOT NULL DEFAULT 1,
    instrucciones_tutor TEXT,
    estado_pago TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado_pago IN ('pendiente', 'aprobado', 'rechazado')),
    url_docx_protegido TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de Pagos Nequi y Verificación Semi-Asistida
CREATE TABLE IF NOT EXISTS public.pagos_nequi (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trabajo_id UUID REFERENCES public.trabajos_academicos(id) ON DELETE SET NULL,
    monto INT NOT NULL,
    rrn_aprobacion TEXT NOT NULL UNIQUE,
    comprobante_url TEXT,
    estado_verificacion TEXT NOT NULL DEFAULT 'PENDIENTE_REVISION' CHECK (estado_verificacion IN ('PENDIENTE_REVISION', 'APROBADO_AUTOMATICO', 'APROBADO_MANUAL', 'RECHAZADO')),
    verificado_por TEXT DEFAULT 'Jhon Zapata (+57 320 710 5618)',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Habilitar RLS para tablas Make
ALTER TABLE public.usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trabajos_academicos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pagos_nequi ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public insert to usuarios" ON public.usuarios FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow service role full access to usuarios" ON public.usuarios FOR ALL USING (true);
CREATE POLICY "Allow service role full access to trabajos_academicos" ON public.trabajos_academicos FOR ALL USING (true);
CREATE POLICY "Allow service role full access to pagos_nequi" ON public.pagos_nequi FOR ALL USING (true);

