"""
Módulo Core: Motor de Generación Académica UNAD / SENA / Proyectos Especiales
Implementa las normas exactas de:
    - Instructivo Oficial APA 7a Edición (UNAD, Vicerrectoría de Medios y Mediaciones)
    - Estándares Técnicos del SENA
    - Generador de Macroproyectos de Grado a la Medida (Tier 3 Premium)
"""

import os
import re
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def apply_unad_paragraph_style(p, line_spacing=1.5, first_line_indent=0.5, space_before=0, space_after=0, align=WD_ALIGN_PARAGRAPH.LEFT):
    """Aplica formato APA 7 UNAD: sin justificar (alineado a la izquierda), sangría de 1.27 cm."""
    p.alignment = align
    p.paragraph_format.line_spacing = line_spacing
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    if first_line_indent > 0:
        p.paragraph_format.first_line_indent = Inches(first_line_indent)
    else:
        p.paragraph_format.first_line_indent = Inches(0)

def add_assisted_instruction_box(doc, tool_name="GeoGebra", instructions=None, code_snippet=None):
    """
    Crea un cuadro formal de instrucción guiada para tareas de Cálculo/Física/STEM.
    Le indica al estudiante cómo graficar en GeoGebra o Colab y le deja el recuadro
    para insertar su captura de pantalla obligatoria.
    """
    tbl = doc.add_table(rows=1, cols=1)
    tbl.autofit = False
    tbl.columns[0].width = Inches(6.5)
    
    cell = tbl.cell(0, 0)
    # Fondo suave azul/grisáceo para destacar sin saturar
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'F0F4F8')
    tcPr.append(shd)

    p_header = cell.paragraphs[0]
    p_header.paragraph_format.space_before = Pt(6)
    p_header.paragraph_format.space_after = Pt(4)
    r_h = p_header.add_run(f"📍 PASO PRÁCTICO EXTERNO: COMPROBACIÓN EN {tool_name.upper()}")
    r_h.bold = True
    r_h.font.color.rgb = RGBColor(15, 41, 66) # Azul corporativo

    if instructions:
        for inst in instructions:
            p_inst = cell.add_paragraph()
            p_inst.paragraph_format.space_after = Pt(2)
            p_inst.paragraph_format.left_indent = Inches(0.2)
            p_inst.add_run(f"• {inst}")

    if code_snippet:
        p_c = cell.add_paragraph()
        p_c.paragraph_format.space_before = Pt(4)
        p_c.paragraph_format.space_after = Pt(4)
        p_c.paragraph_format.left_indent = Inches(0.2)
        r_code_t = p_c.add_run("Código Python para Google Colab:\n")
        r_code_t.bold = True
        r_code = p_c.add_run(code_snippet)
        r_code.font.name = "Courier New"
        r_code.font.size = Pt(9.5)

    p_box = cell.add_paragraph()
    p_box.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_box.paragraph_format.space_before = Pt(8)
    p_box.paragraph_format.space_after = Pt(8)
    r_ph = p_box.add_run(f"[ 👉 PEGA AQUÍ LA CAPTURA DE PANTALLA DE TU COMPROBACIÓN EN {tool_name.upper()} ]")
    r_ph.bold = True
    r_ph.font.color.rgb = RGBColor(0, 122, 135) # Verde azulado

    # Espacio tras la tabla
    p_sep = doc.add_paragraph()
    p_sep.paragraph_format.space_after = Pt(6)

def add_ai_image_prompt_box(doc, figure_num=1, figure_title="Esquema conceptual de la temática", prompt_text="", note="Elaboración propia con apoyo de Inteligencia Artificial."):
    """
    Inserta un recuadro formal según Norma APA 7 para figuras e imágenes:
    Incluye:
        - Número de figura (Negrita)
        - Título de figura (Cursiva)
        - Recuadro contenedor con instrucción y Prompt exacto para IA
        - Nota de figura APA 7 al pie
    """
    # 1. Encabezado de Figura según APA 7
    p_fig = doc.add_paragraph()
    p_fig.paragraph_format.space_before = Pt(8)
    p_fig.paragraph_format.space_after = Pt(2)
    r_f = p_fig.add_run(f"Figura {figure_num}\n")
    r_f.bold = True
    r_t = p_fig.add_run(figure_title)
    r_t.italic = True

    # 2. Contenedor recuadrado para la imagen y el Prompt
    tbl = doc.add_table(rows=1, cols=1)
    tbl.autofit = False
    tbl.columns[0].width = Inches(6.5)

    cell = tbl.cell(0, 0)
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'F9FAFB') # Gris suave
    tcPr.append(shd)

    p_inst = cell.paragraphs[0]
    p_inst.paragraph_format.space_before = Pt(8)
    p_inst.paragraph_format.space_after = Pt(4)
    r_head = p_inst.add_run("🎨 ESPACIO PARA IMAGEN O DIAGRAMA ACADÉMICO")
    r_head.bold = True
    r_head.font.size = Pt(10)
    r_head.font.color.rgb = RGBColor(15, 41, 66)

    p_desc = cell.add_paragraph()
    p_desc.paragraph_format.space_after = Pt(4)
    r_desc = p_desc.add_run("Copia el siguiente prompt en tu generador de imágenes favorito (ChatGPT Plus, Midjourney, Bing Image Creator) y pega la imagen generada en este recuadro:")
    r_desc.font.size = Pt(9.5)

    p_pr = cell.add_paragraph()
    p_pr.paragraph_format.space_before = Pt(4)
    p_pr.paragraph_format.space_after = Pt(8)
    p_pr.paragraph_format.left_indent = Inches(0.2)
    r_pr_tag = p_pr.add_run("Prompt sugerido para IA:\n")
    r_pr_tag.bold = True
    r_pr_tag.font.size = Pt(9.5)
    r_pr_txt = p_pr.add_run(f"\"{prompt_text}\"")
    r_pr_txt.font.name = "Courier New"
    r_pr_txt.font.size = Pt(9)
    r_pr_txt.font.color.rgb = RGBColor(0, 102, 153)

    p_box_holder = cell.add_paragraph()
    p_box_holder.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_box_holder.paragraph_format.space_before = Pt(12)
    p_box_holder.paragraph_format.space_after = Pt(12)
    r_holder = p_box_holder.add_run("[ 🖼️ PEGA AQUÍ LA IMAGEN GENERADA ]")
    r_holder.bold = True
    r_holder.font.size = Pt(10.5)
    r_holder.font.color.rgb = RGBColor(100, 116, 139)

    # 3. Nota APA 7 al pie
    p_note = doc.add_paragraph()
    p_note.paragraph_format.space_before = Pt(4)
    p_note.paragraph_format.space_after = Pt(8)
    r_n = p_note.add_run("Nota. ")
    r_n.italic = True
    p_note.add_run(note)

def generate_document_core(
    project_type="standard", # "standard" (Actividad/Ensayo) o "macro_project" (Proyecto de Grado Completo)
    title="La Dimensión Ética y la Responsabilidad Social en la Era Digital",
    student_name="Estudiante Universitario",
    student_code="1024567890",
    group_number="Grupo 40002_145",
    tutor_name="Tutor / Asesor Académico",
    institution="UNAD", # UNAD, SENA, UNIVERSIDAD_GENERAL
    school="Escuela de Ciencias Sociales, Artes y Humanidades - ECSAH",
    program="Programa de Formación Profesional",
    year="2026",
    font_family="Times New Roman",
    font_size=12,
    line_spacing=1.5,
    include_toc=False,
    guide_summary="",
    custom_sections=None,
    template_path=None,
    output_path="output_generated.docx"
):
    """
    Genera un documento Word completo y riguroso.
    Respeta la arquitectura canónica:
        - Pág 1: Portada
        - Pág 2: Introducción
        - Pág 3: Objetivos (sin viñetas según manual UNAD pág. 20)
        - Pág 4+: Desarrollo de la temática / Macroproyecto
        - Penúltima Pág: Conclusiones (sin viñetas según manual UNAD pág. 24)
        - Última Pág: Referencias con Sangría Francesa de 1.27 cm
    """
    # 1. Cargar plantilla o crear documento nuevo
    if template_path and os.path.exists(template_path):
        doc = docx.Document(template_path)
    else:
        doc = docx.Document()

    # Configuración de márgenes estándar APA 7 (2.54 cm / 1 pulgada en los 4 costados)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

    # Configurar estilo Normal
    style = doc.styles['Normal']
    style.font.name = font_family
    style.font.size = Pt(font_size)
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.line_spacing = line_spacing
    style.paragraph_format.space_after = Pt(0)
    style.paragraph_format.space_before = Pt(0)

    inst_label = "Universidad Nacional Abierta y a Distancia - UNAD" if institution == "UNAD" else ("Servicio Nacional de Aprendizaje - SENA" if institution == "SENA" else institution)

    # =========================================================================
    # PÁGINA 1: PORTADA INSTITUCIONAL (Instructivo UNAD pág. 9)
    # =========================================================================
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(80)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.line_spacing = line_spacing
    p_title.paragraph_format.space_after = Pt(36)
    r_title = p_title.add_run(title)
    r_title.bold = True
    r_title.font.name = font_family
    r_title.font.size = Pt(font_size + 1)

    p_students = doc.add_paragraph()
    p_students.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_students.paragraph_format.line_spacing = line_spacing
    p_students.paragraph_format.space_after = Pt(36)
    r_st = p_students.add_run(f"{student_name} - Código: {student_code}\n{group_number}")
    r_st.font.name = font_family
    r_st.font.size = Pt(font_size)

    p_tutor = doc.add_paragraph()
    p_tutor.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tutor.paragraph_format.line_spacing = line_spacing
    p_tutor.paragraph_format.space_after = Pt(48)
    r_tut = p_tutor.add_run(f"Tutor / Asesor:\n{tutor_name}")
    r_tut.font.name = font_family
    r_tut.font.size = Pt(font_size)

    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.line_spacing = line_spacing
    r_inst = p_inst.add_run(f"{inst_label}\n{school}\n{program}\n{year}")
    r_inst.font.name = font_family
    r_inst.font.size = Pt(font_size)

    doc.add_page_break()

    # =========================================================================
    # TABLA DE CONTENIDO (Opcional si la rúbrica lo solicita - Instructivo pág. 14)
    # =========================================================================
    if include_toc:
        p_toc = doc.add_paragraph()
        p_toc.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_toc.paragraph_format.space_before = Pt(12)
        p_toc.paragraph_format.space_after = Pt(18)
        r_toc = p_toc.add_run("Tabla de Contenido")
        r_toc.bold = True
        r_toc.font.name = font_family
        
        toc_items = [
            ("Introducción", "2"),
            ("Objetivos", "3"),
            ("Contenido del Trabajo / Desarrollo", "4"),
            ("Conclusiones", "6"),
            ("Referencias", "7")
        ]
        for item, pg in toc_items:
            p_ti = doc.add_paragraph()
            p_ti.paragraph_format.line_spacing = line_spacing
            r_ti = p_ti.add_run(f"{item} " + "." * max(10, 65 - len(item)) + f" {pg}")
            r_ti.font.name = font_family
        doc.add_page_break()

    # =========================================================================
    # PÁGINA 2: INTRODUCCIÓN (En su propia hoja - Instructivo pág. 18)
    # =========================================================================
    p_hi = doc.add_paragraph()
    p_hi.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_hi.paragraph_format.space_before = Pt(12)
    p_hi.paragraph_format.space_after = Pt(18)
    r_hi = p_hi.add_run("Introducción")
    r_hi.bold = True
    r_hi.font.name = font_family

    p_i1 = doc.add_paragraph()
    apply_unad_paragraph_style(p_i1, line_spacing=line_spacing, first_line_indent=0.5)
    r_i1 = p_i1.add_run(
        f"El presente trabajo da cabal cumplimiento a los criterios estipulados en la guía de actividades y rúbrica "
        f"institucional de {inst_label}. En el marco formativo del curso, el desarrollo de competencias críticas "
        f"permite a los participantes articular los fundamentos teóricos con las realidades prácticas del entorno social y productivo. "
        f"A través de este documento se aborda con rigurosidad académica la problemática planteada, asegurando coherencia metodológica "
        f"y apego riguroso a las directrices de las Normas APA 7a edición."
    )
    r_i1.font.name = font_family

    p_i2 = doc.add_paragraph()
    apply_unad_paragraph_style(p_i2, line_spacing=line_spacing, first_line_indent=0.5, space_before=6)
    r_i2 = p_i2.add_run(
        "A lo largo del manuscrito se sintetizan los aportes provenientes de las fuentes bibliográficas obligatorias, "
        "las orientaciones compartidas en los foros colaborativos y los requerimientos de la rúbrica evaluativa. "
        "El propósito central consiste en aportar un análisis sustentado que no solo responda a los interrogantes orientadores, "
        "sino que estimule la reflexión ética y disciplinar del futuro profesional."
    )
    r_i2.font.name = font_family

    doc.add_page_break()

    # =========================================================================
    # PÁGINA 3: OBJETIVOS (En su propia hoja - Instructivo pág. 20)
    # REGLA UNAD: SIN VIÑETAS NI NÚMEROS
    # =========================================================================
    p_ho = doc.add_paragraph()
    p_ho.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ho.paragraph_format.space_before = Pt(12)
    p_ho.paragraph_format.space_after = Pt(18)
    r_ho = p_ho.add_run("Objetivos")
    r_ho.bold = True
    r_ho.font.name = font_family

    p_og_title = doc.add_paragraph()
    p_og_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_og_title.paragraph_format.space_before = Pt(6)
    p_og_title.paragraph_format.space_after = Pt(6)
    r_og_t = p_og_title.add_run("Objetivo General")
    r_og_t.bold = True
    r_og_t.font.name = font_family

    p_og = doc.add_paragraph()
    apply_unad_paragraph_style(p_og, line_spacing=line_spacing, first_line_indent=0.5)
    r_og = p_og.add_run(
        f"Evaluar de manera crítica e integral la temática central del proyecto ({title}) mediante el análisis conceptual, "
        f"el contraste empírico y la aplicación de los lineamientos pedagógicos e investigativos de {inst_label}."
    )
    r_og.font.name = font_family

    p_oe_title = doc.add_paragraph()
    p_oe_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_oe_title.paragraph_format.space_before = Pt(12)
    p_oe_title.paragraph_format.space_after = Pt(6)
    r_oe_t = p_oe_title.add_run("Objetivos Específicos")
    r_oe_t.bold = True
    r_oe_t.font.name = font_family

    oe_list = [
        "Identificar las variables teóricas y normativas fundamentales asociadas a la problemática a partir de la literatura académica recomendada.",
        "Examinar los dilemas y oportunidades contextuales identificados en las comunidades de estudio a la luz de los criterios de la rúbrica.",
        "Formular propuestas de intervención y reflexiones conclusivas que fortalezcan el desempeño profesional y la transformación social comunitaria."
    ]
    for oe in oe_list:
        p_oe = doc.add_paragraph()
        apply_unad_paragraph_style(p_oe, line_spacing=line_spacing, first_line_indent=0.5, space_before=4)
        r_oe = p_oe.add_run(oe)
        r_oe.font.name = font_family

    doc.add_page_break()

    # =========================================================================
    # PÁGINAS 4+: DESARROLLO DEL TRABAJO O MACROPROYECTO
    # =========================================================================
    p_hd = doc.add_paragraph()
    p_hd.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_hd.paragraph_format.space_before = Pt(12)
    p_hd.paragraph_format.space_after = Pt(18)
    r_hd = p_hd.add_run("Contenido del Trabajo" if project_type == "standard" else "Planteamiento y Desarrollo del Macroproyecto")
    r_hd.bold = True
    r_hd.font.name = font_family

    # Si es un Macroproyecto de Grado (Tier 3), estructura extensa de tesis
    if project_type == "macro_project":
        macro_sections = [
            ("1. Planteamiento del Problema y Justificación", 
             "La formulación del problema parte de las brechas evidenciadas en el contexto regional colombiano, donde la falta de articulación entre los modelos teóricos y las dinámicas socioeconómicas limita la efectividad de las soluciones comunitarias. Siguiendo las directrices metodológicas de Hernández-Sampieri y Mendoza (2018), la investigación se justifica por su pertinencia social, viabilidad técnica y relevancia epistémica."),
            ("2. Marco Teórico y Estado del Arte", 
             "La fundamentación teórica se apoya en los autores de mayor indexación académica en el área. Como sostiene Cortina (2018), los marcos institucionales cobran legitimidad únicamente cuando incorporan la ética dialógica y la corresponsabilidad social. Asimismo, se integran los postulados de Vallaeys (2021) sobre la gestión de impactos cognitivos y formativos en las instituciones de educación superior."),
            ("3. Diseño Metodológico y Técnicas de Recolección", 
             "El presente estudio adopta un enfoque mixto (cualitativo-descriptivo), orientado a la comprensión situada de los fenómenos. Para la recolección de información se establecen instrumentos estandarizados validados por juicio de expertos, garantizando confiabilidad y validez de constructo según los estándares investigativos de la universidad."),
            ("4. Análisis de Resultados Preliminares y Discusión", 
             "Los hallazgos derivados de la aplicación de los instrumentos evidencian una alta correlación entre la capacitación sistemática y la mitigación de inconsistencias procedimentales. Estos resultados concuerdan con los estudios sectoriales recientes del SENA y el Ministerio de Educación Nacional.")
        ]
        for sec_title, sec_content in macro_sections:
            p_st = doc.add_paragraph()
            p_st.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_st.paragraph_format.space_before = Pt(14)
            p_st.paragraph_format.space_after = Pt(6)
            r_st = p_st.add_run(sec_title)
            r_st.bold = True
            r_st.font.name = font_family

            p_sc = doc.add_paragraph()
            apply_unad_paragraph_style(p_sc, line_spacing=line_spacing, first_line_indent=0.5)
            r_sc = p_sc.add_run(sec_content)
            r_sc.font.name = font_family
    else:
        # Actividad estándar universitaria (Fases UNAD / SENA)
        p_t1 = doc.add_paragraph()
        p_t1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_t1.paragraph_format.space_before = Pt(10)
        p_t1.paragraph_format.space_after = Pt(10)
        r_t1 = p_t1.add_run("Fundamentación Conceptual y Análisis de la Guía")
        r_t1.bold = True
        r_t1.font.name = font_family

        p_b1 = doc.add_paragraph()
        apply_unad_paragraph_style(p_b1, line_spacing=line_spacing, first_line_indent=0.5)
        r_b1 = p_b1.add_run(
            "El abordaje sistemático de la temática solicitada permite constatar la relevancia de los conceptos orientadores. "
            "De acuerdo con Cortina (2018), toda acción formativa o productiva adquiere verdadero valor cuando se ejerce "
            "con sentido de responsabilidad social y transparencia. En congruencia con la rúbrica de calificación en su Nivel Alto, "
            "se articulan a continuación las respuestas a las preguntas orientadoras del foro y los ejercicios analíticos requeridos."
        )
        r_b1.font.name = font_family

        p_t2 = doc.add_paragraph()
        p_t2.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_t2.paragraph_format.space_before = Pt(12)
        p_t2.paragraph_format.space_after = Pt(6)
        r_t2 = p_t2.add_run("Articulación Teórica y Resultados del Ejercicio")
        r_t2.bold = True
        r_t2.font.name = font_family

        p_b2 = doc.add_paragraph()
        apply_unad_paragraph_style(p_b2, line_spacing=line_spacing, first_line_indent=0.5)
        r_b2 = p_b2.add_run(
            "En concordancia con los aportes de Vallaeys (2021) y Kant (1785/2012), la interiorización de principios sólidos "
            "evita que el profesional incurra en conductas asistenciales o superficiales, garantizando un impacto sostenible "
            "y una trazabilidad verificable en cada una de las metas de aprendizaje alcanzadas."
        )
        r_b2.font.name = font_family

    doc.add_page_break()

    # =========================================================================
    # PENÚLTIMA PÁGINA: CONCLUSIONES (Instructivo pág. 24)
    # REGLA UNAD: SIN VIÑETAS NI NÚMEROS
    # =========================================================================
    p_hc = doc.add_paragraph()
    p_hc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_hc.paragraph_format.space_before = Pt(12)
    p_hc.paragraph_format.space_after = Pt(18)
    r_hc = p_hc.add_run("Conclusiones")
    r_hc.bold = True
    r_hc.font.name = font_family

    conclusions = [
        "El desarrollo exhaustivo de la actividad corrobora que la aplicación de principios teóricos rigurosos fortalece de manera determinante la capacidad resolutiva y la solvencia analítica de los estudiantes en su respectivo campo de formación.",
        "Se demostró que el seguimiento puntual de las guías institucionales y el cumplimiento de las normas APA 7 optimiza la presentación científica del conocimiento, eliminando ambigüedades y potenciando la transparencia discursiva.",
        "Las reflexiones emanadas del estudio permiten concluir que los proyectos con vocación transformadora generan sinergias directas con las necesidades del entorno, robusteciendo la legitimidad institucional y el compromiso ético ante la comunidad."
    ]
    for c_text in conclusions:
        p_c = doc.add_paragraph()
        apply_unad_paragraph_style(p_c, line_spacing=line_spacing, first_line_indent=0.5, space_before=6)
        r_c = p_c.add_run(c_text)
        r_c.font.name = font_family

    doc.add_page_break()

    # =========================================================================
    # ÚLTIMA PÁGINA: REFERENCIAS (Instructivo pág. 26-38)
    # Sangría francesa de 1.27 cm y orden alfabético estricto
    # =========================================================================
    p_href = doc.add_paragraph()
    p_href.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_href.paragraph_format.space_before = Pt(12)
    p_href.paragraph_format.space_after = Pt(18)
    r_href = p_href.add_run("Referencias")
    r_href.bold = True
    r_href.font.name = font_family

    refs = [
        "Cortina, A. (2018). ¿Para qué sirve realmente la ética? Paidós Ibérica.",
        "Hernández-Sampieri, R., & Mendoza, C. P. (2018). Metodología de la investigación: Las rutas cuantitativa, cualitativa y mixta. McGraw-Hill Education.",
        "Kant, I. (2012). Fundamentación para una metafísica de las costumbres (R. R. Aramayo, Trad.). Alianza Editorial. (Obra original publicada en 1785).",
        "Universidad Nacional Abierta y a Distancia. (2023). Instructivo para el uso de Normas APA 7a Edición. Red de Gestión Tecnopedagógica de Contenidos.",
        "Vallaeys, F. (2021). Manual de primeros pasos en responsabilidad social universitaria. UNESCO - IESALC."
    ]
    for ref in refs:
        p_r = doc.add_paragraph()
        p_r.paragraph_format.left_indent = Inches(0.5)
        p_r.paragraph_format.first_line_indent = Inches(-0.5)
        p_r.paragraph_format.line_spacing = line_spacing
        p_r.paragraph_format.space_after = Pt(6)
        r_ref = p_r.add_run(ref)
        r_ref.font.name = font_family

    # Guardar documento
    doc.save(output_path)
    return output_path
