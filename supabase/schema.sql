-- =========================================================================
-- 🎓 ACADEMICPRO AI - SUPABASE DATABASE SCHEMA (PRODUCTION-READY)
-- PostgreSQL + Row Level Security (RLS) + Onboarding Testers + Auditoría
-- =========================================================================

-- Habilitar extensión UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. TABLA DE PERFILES DE USUARIOS (Sincronizada con auth.users de Supabase)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    institution TEXT DEFAULT 'UNAD',
    phone TEXT,
    is_tester BOOLEAN DEFAULT TRUE,                     -- Habilitado para testers iniciales (Uso Gratuito)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. TABLA DE BILLETERA DE CRÉDITOS ACADÉMICOS
CREATE TABLE IF NOT EXISTS public.user_credits (
    user_id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    balance INT NOT NULL DEFAULT 10,                    -- 10 créditos de cortesía para testers iniciales
    premium_projects_balance INT NOT NULL DEFAULT 2,    -- 2 pases de proyectos de grado para pruebas
    total_earned INT NOT NULL DEFAULT 10,
    total_spent INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. TABLA DE ARCHIVOS Y GUÍAS SUBIDAS POR EL ESTUDIANTE
CREATE TABLE IF NOT EXISTS public.uploaded_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,                            -- 'guide_pdf', 'rubric_pdf', 'template_docx', 'template_xlsx'
    file_size_bytes BIGINT DEFAULT 0,
    storage_path TEXT NOT NULL,
    extracted_text TEXT,
    missing_fields JSONB DEFAULT '[]'::jsonb,           -- Preguntas o datos faltantes detectados por la IA
    status TEXT DEFAULT 'ANALYZED',                     -- 'UPLOADED', 'ANALYZING', 'ANALYZED', 'REQUIRES_INFO'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. HISTORIAL DE TRABAJOS GENERADOS Y AUDITADOS (WORD + EXCEL)
CREATE TABLE IF NOT EXISTS public.document_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    mode TEXT NOT NULL CHECK (mode IN ('generator', 'auditor', 'excel_filler')),
    title TEXT NOT NULL,
    institution TEXT NOT NULL DEFAULT 'UNAD',
    font_family TEXT DEFAULT 'Times New Roman',
    output_docx_path TEXT,
    output_excel_path TEXT,                             -- Reporte comparativo de auditoría o plantilla Excel llena
    pedagogical_summary TEXT,
    audit_score INT DEFAULT 100,                        -- Calificación de cumplimiento APA 7 (0 a 100%)
    audit_findings JSONB DEFAULT '[]'::jsonb,           -- Lista de correcciones aplicadas automáticamente
    bytes_generated BIGINT DEFAULT 0,                   -- Cantidad de bytes generados para control de métricas
    pages_count INT DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'COMPLETED',           -- 'PENDING', 'PROCESSING', 'REQUIRES_INFO', 'COMPLETED', 'FAILED'
    credits_cost INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. TABLA DE TRANSACCIONES Y PAGOS (WOMPI / NEQUI)
CREATE TABLE IF NOT EXISTS public.transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    reference TEXT NOT NULL UNIQUE,
    wompi_id TEXT UNIQUE,
    tier_type TEXT NOT NULL DEFAULT 'STANDARD_PACK_5',
    amount_in_cents BIGINT NOT NULL,
    currency TEXT DEFAULT 'COP',
    payment_method_type TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    credits_granted INT NOT NULL DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =========================================================================
-- TRIGGER AUTOMÁTICO: ONBOARDING CON ACCESO GRATIS PARA TESTERS
-- =========================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Crear perfil público
    INSERT INTO public.profiles (id, email, full_name, is_tester)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
        TRUE -- Marcado como tester para pruebas en tiempo real
    )
    ON CONFLICT (id) DO NOTHING;

    -- Asignar saldo inicial de pruebas (10 créditos estándar + 2 pases de proyectos)
    INSERT INTO public.user_credits (user_id, balance, premium_projects_balance, total_earned, total_spent)
    VALUES (NEW.id, 10, 2, 10, 0)
    ON CONFLICT (user_id) DO NOTHING;

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
    is_user_tester BOOLEAN;
BEGIN
    -- Verificar si es tester gratuito
    SELECT is_tester INTO is_user_tester FROM public.profiles WHERE id = p_user_id;
    
    IF is_user_tester IS TRUE THEN
        -- A los testers no se les bloquea la app
        UPDATE public.user_credits
        SET total_spent = total_spent + p_cost,
            updated_at = NOW()
        WHERE user_id = p_user_id;
        RETURN TRUE;
    END IF;

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
-- ROW LEVEL SECURITY (RLS) - SEGURIDAD DE DATOS
-- =========================================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_credits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.uploaded_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;

-- Políticas de perfiles
CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- Políticas de créditos
CREATE POLICY "Users can view own credits" ON public.user_credits FOR SELECT USING (auth.uid() = user_id);

-- Políticas de archivos subidos
CREATE POLICY "Users can view own uploaded files" ON public.uploaded_files FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own uploaded files" ON public.uploaded_files FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Políticas de tareas y documentos
CREATE POLICY "Users can view own document tasks" ON public.document_tasks FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own document tasks" ON public.document_tasks FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Políticas de transacciones
CREATE POLICY "Users can view own transactions" ON public.transactions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert pending transactions" ON public.transactions FOR INSERT WITH CHECK (auth.uid() = user_id);
