// =========================================================================
// ACADEMICPRO - CONTROLLER FRONTEND COMPACTO EN 2 ESTADOS (ZERO SCROLL)
// =========================================================================

let currentMode = "correccion"; // 'correccion' | 'creacion'
let currentUploadedFile = null;
let currentSecondaryFile = null;
let userBalance = 4;
let currentQuote = {
  paginas: 30,
  creditos: 2,
  costo_cop: 20000,
  can_process: true
};
let selectedRechargePlan = "STANDARD_PACK_5";

document.addEventListener("DOMContentLoaded", () => {
  initDirectFileInputs();
  initModals();
  fetchInitialCredits();
});

/* =========================================================================
   1. SELECCIÓN INTERACTIVA DE TARJETAS Y DISPARADOR DE CARGA (ESTADO 1)
   ========================================================================= */
function selectSelectionCard(mode) {
  currentMode = mode;
  const cardCreacion = document.getElementById("card-creacion");
  const cardCorreccion = document.getElementById("card-correccion");
  const radioCreacion = document.getElementById("radio-circle-creacion");
  const radioCorreccion = document.getElementById("radio-circle-correccion");

  if (mode === "creacion") {
    if (cardCreacion) cardCreacion.classList.add("active");
    if (radioCreacion) radioCreacion.classList.add("active");
    if (cardCorreccion) cardCorreccion.classList.remove("active");
    if (radioCorreccion) radioCorreccion.classList.remove("active");
  } else {
    if (cardCorreccion) cardCorreccion.classList.add("active");
    if (radioCorreccion) radioCorreccion.classList.add("active");
    if (cardCreacion) cardCreacion.classList.remove("active");
    if (radioCreacion) radioCreacion.classList.remove("active");
  }
}

function triggerFileUpload(mode) {
  selectSelectionCard(mode);
  if (mode === "creacion") {
    const input = document.getElementById("file-guide-direct");
    if (input) input.click();
  } else {
    const input = document.getElementById("file-thesis-direct");
    if (input) input.click();
  }
}

function initDirectFileInputs() {
  const inputGuide = document.getElementById("file-guide-direct");
  const inputThesis = document.getElementById("file-thesis-direct");
  const inputSecondary = document.getElementById("file-rubric-secondary");

  // Al seleccionar archivo en Modo Creación
  if (inputGuide) {
    inputGuide.addEventListener("change", (e) => {
      if (inputGuide.files && inputGuide.files.length > 0) {
        handleFileSelected(inputGuide.files[0], "creacion");
      }
    });
  }

  // Al seleccionar archivo en Modo Corrección
  if (inputThesis) {
    inputThesis.addEventListener("change", (e) => {
      if (inputThesis.files && inputThesis.files.length > 0) {
        handleFileSelected(inputThesis.files[0], "correccion");
      }
    });
  }

  // Archivo secundario (Rúbrica opcional)
  if (inputSecondary) {
    inputSecondary.addEventListener("change", () => {
      if (inputSecondary.files && inputSecondary.files.length > 0) {
        currentSecondaryFile = inputSecondary.files[0];
        const lbl = document.getElementById("btn-secondary-label");
        if (lbl) lbl.textContent = "✅ Rúbrica: " + currentSecondaryFile.name;
      }
    });
  }

  // Comprobante Nequi
  const receiptInput = document.getElementById("file-nequi-receipt");
  const receiptLabel = document.getElementById("receipt-file-label");
  if (receiptInput && receiptLabel) {
    receiptInput.addEventListener("change", () => {
      if (receiptInput.files && receiptInput.files.length > 0) {
        receiptLabel.textContent = "✅ " + receiptInput.files[0].name;
        receiptLabel.style.color = "#0E8345";
        receiptLabel.style.fontWeight = "700";
      }
    });
  }
}

/* =========================================================================
   2. TRANSICIÓN LIMPIA AL ESTADO 2 (CONFIGURACIÓN Y CONFIRMACIÓN)
   ========================================================================= */
async function handleFileSelected(file, mode) {
  currentUploadedFile = file;
  currentMode = mode;

  // Cambiar vista en el mismo viewport (sin scroll)
  const view1 = document.getElementById("view-state-1");
  const view2 = document.getElementById("view-state-2");
  const view3 = document.getElementById("view-state-3");

  if (view1) view1.style.display = "none";
  if (view3) view3.style.display = "none";
  if (view2) view2.style.display = "flex";

  // Actualizar metadatos del archivo en la UI
  const elName = document.getElementById("summary-file-name");
  const elSize = document.getElementById("summary-file-size");
  const elTag = document.getElementById("summary-service-tag");
  const elPill = document.getElementById("active-service-pill");
  const elFormat = document.getElementById("summary-format");

  if (elName) elName.textContent = file.name;
  if (elSize) elSize.textContent = `${(file.size / 1024).toFixed(1)} KB · Listo para procesar`;
  
  if (mode === "creacion") {
    if (elTag) elTag.textContent = "Guía o Rúbrica de Actividades";
    if (elPill) elPill.textContent = "Modo: Creación de Trabajo desde Guía";
    if (elFormat) elFormat.textContent = file.name.endsWith(".pdf") ? "PDF" : "Word (.docx)";
  } else {
    if (elTag) elTag.textContent = "Borrador de Tesis / Manuscrito";
    if (elPill) elPill.textContent = "Modo: Corrección y Auditoría APA 7";
    if (elFormat) elFormat.textContent = "Word (.docx)";
  }

  // Cotización asíncrona en tiempo real con páginas reales
  await updateRealtimeQuote(file);
}

function resetToInitialState() {
  currentUploadedFile = null;
  currentSecondaryFile = null;

  const view1 = document.getElementById("view-state-1");
  const view2 = document.getElementById("view-state-2");
  const view3 = document.getElementById("view-state-3");

  if (view2) view2.style.display = "none";
  if (view3) view3.style.display = "none";
  if (view1) view1.style.display = "flex";

  // Limpiar inputs
  const inGuide = document.getElementById("file-guide-direct");
  const inThesis = document.getElementById("file-thesis-direct");
  const inSec = document.getElementById("file-rubric-secondary");
  if (inGuide) inGuide.value = "";
  if (inThesis) inThesis.value = "";
  if (inSec) inSec.value = "";

  const secLbl = document.getElementById("btn-secondary-label");
  if (secLbl) secLbl.textContent = "📎 + Agregar Rúbrica u Observaciones (.xlsx/.pdf)";
}

/* =========================================================================
   3. COTIZACIÓN DINÁMICA ASÍNCRONA
   ========================================================================= */
async function updateRealtimeQuote(file) {
  try {
    const formData = new FormData();
    formData.append("modalidad", currentMode);
    if (file) {
      formData.append("file", file);
    }

    const res = await fetch("/api/quote/estimate", {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    if (data.status === "success") {
      currentQuote = data.quote;
      userBalance = data.current_balance;

      // Actualizar métricas en el widget
      const elPages = document.getElementById("q-pages");
      const elCredits = document.getElementById("q-credits");
      const elCost = document.getElementById("q-cost");
      const elBalance = document.getElementById("q-user-balance");
      const summaryPages = document.getElementById("summary-pages-count");
      const btnProcess = document.getElementById("btn-process-doc");
      const btnText = document.getElementById("btn-process-text");
      const btnTag = document.getElementById("btn-process-tag");

      if (elPages) elPages.textContent = data.quote.paginas;
      if (summaryPages) summaryPages.textContent = data.quote.paginas;
      if (elCredits) elCredits.textContent = data.quote.creditos;
      if (elCost) elCost.textContent = data.quote.costo_formateado;
      if (elBalance) elBalance.textContent = data.current_balance;

      if (btnProcess) {
        if (data.can_process) {
          btnProcess.className = "wompi-btn-action";
          btnText.textContent = "🚀 Iniciar Procesamiento";
          btnTag.textContent = `${data.quote.creditos} Créditos`;
        } else {
          btnProcess.className = "wompi-btn-action buy-credits";
          btnText.textContent = `Comprar Créditos (Faltan ${data.missing_credits})`;
          btnTag.textContent = `$${data.missing_credits * 10000} COP`;
        }
      }
    }
  } catch (err) {
    console.error("Error en cotización asíncrona:", err);
  }
}

/* =========================================================================
   4. INICIAR PROCESAMIENTO
   ========================================================================= */
async function executeDocumentProcess() {
  if (!currentUploadedFile) {
    alert("No se ha seleccionado ningún archivo.");
    return;
  }

  // Verificar saldo
  if (!currentQuote.can_process && userBalance < currentQuote.creditos) {
    alert(`Tu saldo es de ${userBalance} créditos y este documento requiere ${currentQuote.creditos} créditos. Por favor recarga para continuar.`);
    openRechargeModal();
    return;
  }

  const instructions = document.getElementById("tutor-instructions")?.value?.trim() || "";
  const btn = document.getElementById("btn-process-doc");
  const originalText = btn.innerHTML;
  btn.innerHTML = "⏳ Procesando documento con normas APA 7...";
  btn.disabled = true;

  try {
    const formData = new FormData();
    formData.append("modalidad", currentMode);
    formData.append("tutor_instructions", instructions);

    let endpoint = currentMode === "correccion" ? "/api/auditing/audit-thesis" : "/api/generation/create-from-guide";

    if (currentMode === "correccion") {
      formData.append("thesis_file", currentUploadedFile);
      if (currentSecondaryFile) {
        formData.append("feedback_file", currentSecondaryFile);
      }
    } else {
      formData.append("title", "Actividad Académica Desarrollada");
      formData.append("institution", "UNAD");
      formData.append("guide_file", currentUploadedFile);
      if (currentSecondaryFile) {
        formData.append("rubric_file", currentSecondaryFile);
      }
    }

    const res = await fetch(endpoint, {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    if (!res.ok) {
      alert("❌ Error: " + (data.detail || "No se pudo procesar el documento."));
      return;
    }

    // Mostrar Estado 3 (Resultados)
    showResultsView({
      docxUrl: data.download_docx_url || data.download_url,
      excelUrl: data.download_excel_url || null,
      summary: data.pedagogical_summary + (instructions ? `\n\nInstrucciones del Tutor Atendidas: "${instructions.substring(0, 100)}..."` : "")
    });

    await fetchInitialCredits();
  } catch (err) {
    alert("Error de conexión durante el procesamiento.");
    console.error(err);
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

function showResultsView({ docxUrl, excelUrl, summary }) {
  const view1 = document.getElementById("view-state-1");
  const view2 = document.getElementById("view-state-2");
  const view3 = document.getElementById("view-state-3");

  if (view1) view1.style.display = "none";
  if (view2) view2.style.display = "none";
  if (view3) view3.style.display = "flex";

  const linkDocx = document.getElementById("link-download-docx");
  const linkExcel = document.getElementById("link-download-excel");
  const textSummary = document.getElementById("pedagogical-text");

  if (linkDocx && docxUrl) linkDocx.href = docxUrl;

  if (linkExcel && excelUrl) {
    linkExcel.style.display = "flex";
    linkExcel.href = excelUrl;
  } else if (linkExcel) {
    linkExcel.style.display = "none";
  }

  if (textSummary) textSummary.textContent = summary;
}

/* =========================================================================
   5. BILLETERA Y PAGOS
   ========================================================================= */
function initModals() {
  const modal = document.getElementById("modal-recharge");
  const btnOpen = document.getElementById("btn-open-recharge");
  const btnClose = document.getElementById("btn-close-modal");

  if (btnOpen) btnOpen.addEventListener("click", openRechargeModal);
  if (btnClose && modal) btnClose.addEventListener("click", closeRechargeModal);
  window.addEventListener("click", (e) => {
    if (e.target === modal) closeRechargeModal();
    const modalAuth = document.getElementById("modal-auth");
    if (e.target === modalAuth) closeLoginModal();
    const modalReg = document.getElementById("modal-register");
    if (e.target === modalReg) closeRegisterModal();
  });
}

function openRechargeModal() {
  const modal = document.getElementById("modal-recharge");
  if (modal) modal.style.display = "flex";
}

function closeRechargeModal() {
  const modal = document.getElementById("modal-recharge");
  if (modal) modal.style.display = "none";
}

function handleReceiptFileChange(input) {
  const label = document.getElementById("receipt-file-label");
  if (input && input.files && input.files.length > 0) {
    if (label) label.textContent = input.files[0].name;
  } else {
    if (label) label.textContent = "Seleccionar comprobante (PDF o Foto)";
  }
}

function selectPlanQuote(credits, amount, el) {
  const display = document.getElementById("nequi-amount-display");
  if (display) display.textContent = "$" + Number(amount).toLocaleString("es-CO") + " COP";
  
  const planLabel = document.getElementById("recharge-plan-label");
  if (planLabel) planLabel.textContent = `Paquete ${credits} Crédito${credits > 1 ? 's' : ''}`;

  if (credits === 10) {
    selectedRechargePlan = "PREMIUM_PROJECT_PASS";
  } else if (credits === 1) {
    selectedRechargePlan = "MICRO_PACK_1";
  } else if (credits === 2) {
    selectedRechargePlan = "BASIC_PACK_2";
  } else {
    selectedRechargePlan = "STANDARD_PACK_5";
  }

  // Actualizar estado visual activo en las tarjetas
  document.querySelectorAll(".modal-plan-card, .modal-plan-row").forEach(row => {
    row.classList.remove("active");
  });
  if (el) {
    el.classList.add("active");
  } else if (window.event && window.event.currentTarget) {
    window.event.currentTarget.classList.add("active");
  }
}

function copyNequiNumber() {
  const num = document.getElementById("nequi-number-text")?.textContent?.replace(/\s+/g, '') || "3207105618";
  navigator.clipboard.writeText(num).then(() => {
    alert("¡Número Nequi copiado al portapapeles: " + num + "!");
  });
}

async function uploadAndVerifyReceipt() {
  const receiptInput = document.getElementById("file-nequi-receipt");
  if (!receiptInput || !receiptInput.files || receiptInput.files.length === 0) {
    alert("Por favor selecciona tu comprobante Nequi (PDF o Imagen).");
    return;
  }

  const btn = document.getElementById("btn-scan-receipt");
  const originalText = btn.innerHTML;
  btn.innerHTML = "⏳ Escaneando comprobante con Visión Artificial...";
  btn.disabled = true;

  try {
    const formData = new FormData();
    formData.append("package_id", selectedRechargePlan);
    formData.append("voucher_file", receiptInput.files[0]);

    const res = await fetch("/api/credits/upload-voucher", {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    if (!res.ok) {
      alert("❌ " + (data.detail?.message || data.detail || "Comprobante rechazado por inconsistencia."));
      return;
    }

    alert("🎉 " + data.message + "\n\n• Monto: $" + data.extraction.monto + "\n• Destino: " + data.extraction.numero_destino + "\n• Ref: " + data.extraction.referencia_aprobacion);
    await fetchInitialCredits();

    const modal = document.getElementById("modal-recharge");
    if (modal) modal.style.display = "none";
  } catch (err) {
    alert("Error conectando con el servicio de verificación.");
    console.error(err);
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

async function fetchInitialCredits() {
  try {
    const res = await fetch("/api/credits/balance");
    const data = await res.json();
    if (data.status === "success") {
      userBalance = data.credits.balance;
      const creditEl = document.getElementById("credit-count");
      const quoteBalance = document.getElementById("q-user-balance");
      if (creditEl) creditEl.textContent = userBalance;
      if (quoteBalance) quoteBalance.textContent = userBalance;
    }
  } catch (err) {
    console.error("Error consultando balance:", err);
  }
}

/* =========================================================================
   6. SPEED DIAL (FLOATING ACTION BUTTON CON 3 ACCIONES)
   ========================================================================= */
let isSpeedDialOpen = false;

function toggleSpeedDial() {
  const wrapper = document.getElementById("speed-dial");
  const trigger = document.getElementById("speed-dial-trigger");
  if (!wrapper || !trigger) return;

  isSpeedDialOpen = !isSpeedDialOpen;
  if (isSpeedDialOpen) {
    wrapper.classList.add("open");
    trigger.classList.add("active");
  } else {
    wrapper.classList.remove("open");
    trigger.classList.remove("active");
  }
}

// Cerrar speed dial al hacer clic en cualquier parte fuera
window.addEventListener("click", (e) => {
  const speedDial = document.getElementById("speed-dial");
  if (isSpeedDialOpen && speedDial && !speedDial.contains(e.target)) {
    toggleSpeedDial();
  }
});

/* =========================================================================
   7. VISOR DE MUESTRA EFÍMERA Y BLINDAJE ANTI-CAPTURA
   ========================================================================= */
let isEphemeralViewerOpen = false;
let ephemeralSecurityActive = false;

function openEphemeralViewer() {
  const modal = document.getElementById("modal-ephemeral-viewer");
  const body = document.getElementById("ephemeral-sample-body");
  if (!modal || !body) return;

  const docTitle = currentUploadedFile ? currentUploadedFile.name.replace(/\.[^/.]+$/, "") : "Monografía de Grado";
  const instructions = document.getElementById("tutor-instructions")?.value?.trim() || "Formato APA 7ma Edición y normas institucionales UNAD.";

  // Renderizar muestra de hoja estilo carta con sangría de 1.27 cm y estructura APA 7
  body.innerHTML = `
    <div style="text-align: center; margin-bottom: 40px;">
      <h2 style="font-size: 18px; font-weight: bold; margin-bottom: 12px; text-transform: uppercase;">UNIVERSIDAD NACIONAL ABIERTA Y A DISTANCIA – UNAD</h2>
      <h3 style="font-size: 15px; font-weight: bold; margin-bottom: 24px;">ESCUELA DE CIENCIAS BÁSICAS, TECNOLOGÍA E INGENIERÍA</h3>
      <div style="margin: 45px 0;">
        <h1 style="font-size: 19px; font-weight: bold; text-decoration: underline;">${escapeHtml(docTitle.toUpperCase())}</h1>
        <p style="font-size: 13px; font-style: italic; margin-top: 8px;">Muestra de desarrollo metodológico bajo normas APA 7ma edición</p>
      </div>
      <div style="margin-top: 50px; font-size: 13px;">
        <p><strong>Autor:</strong> Estudiante Asistido (AcademicPro ID: ${Math.floor(1000 + Math.random() * 9000)})</p>
        <p><strong>Tutor Asesor:</strong> Asesoría Académica Especializada (+57 320 710 5618)</p>
        <p><strong>Fecha de Emisión:</strong> Noviembre de 2026</p>
      </div>
    </div>

    <hr style="border: none; border-top: 1px solid #CCC; margin: 30px 0;" />

    <div style="margin-bottom: 30px;">
      <h3 style="text-align: center; font-size: 15px; font-weight: bold; margin-bottom: 14px;">TABLA DE CONTENIDO (OFICIAL APA 7)</h3>
      <div style="display: flex; justify-content: space-between; border-bottom: 1px dotted #999; padding: 4px 0;">
        <span>1. INTRODUCCIÓN GENERAL Y CONTEXTUALIZACIÓN</span>
        <span>Pág. 3</span>
      </div>
      <div style="display: flex; justify-content: space-between; border-bottom: 1px dotted #999; padding: 4px 0;">
        <span>2. PLANTEAMIENTO DEL PROBLEMA Y JUSTIFICACIÓN</span>
        <span>Pág. 6</span>
      </div>
      <div style="display: flex; justify-content: space-between; border-bottom: 1px dotted #999; padding: 4px 0;">
        <span>3. OBJETIVOS (GENERAL Y ESPECÍFICOS SIN NUMERACIÓN NI VIÑETAS)</span>
        <span>Pág. 9</span>
      </div>
      <div style="display: flex; justify-content: space-between; border-bottom: 1px dotted #999; padding: 4px 0;">
        <span>4. MARCO METODOLÓGICO Y MATRIZ DE CONSISTENCIA</span>
        <span>Pág. 14</span>
      </div>
    </div>

    <hr style="border: none; border-top: 1px solid #CCC; margin: 30px 0;" />

    <div>
      <h3 style="font-size: 15px; font-weight: bold; text-align: center; margin-bottom: 14px;">INTRODUCCIÓN</h3>
      <p style="text-indent: 1.27cm; text-align: left; margin-bottom: 14px;">
        El presente trabajo de investigación se desarrolla en estricto cumplimiento con los lineamientos metodológicos exigidos por la institución y las disposiciones vigentes del Manual de Publicaciones de la American Psychological Association (APA), séptima edición. La problemática abordada responde a las observaciones formuladas por el cuerpo docente: <em>"${escapeHtml(instructions.substring(0, 160))}..."</em>.
      </p>
      <p style="text-indent: 1.27cm; text-align: left; margin-bottom: 14px;">
        Para garantizar la rigurosidad científica, cada acápite conceptual cuenta con citas parentéticas y narrativas verificables en bases de datos indexadas (Scopus, Dialnet, Redalyc). La estructura visual garantiza márgenes simétricos de 2.54 cm, interlineado doble uniforme y tablas con tres líneas horizontales reglamentarias sin bordes verticales.
      </p>
    </div>
  `;

  modal.style.display = "flex";
  isEphemeralViewerOpen = true;

  // Activar blindaje anti-captura
  attachAntiCaptureShield();
}

function destroyAndCloseEphemeralViewer() {
  const modal = document.getElementById("modal-ephemeral-viewer");
  const body = document.getElementById("ephemeral-sample-body");
  const postCard = document.getElementById("post-preview-summary-card");
  const postPages = document.getElementById("post-preview-pages");

  // 1. Destrucción total del contenido en memoria (evita extracción desde consola)
  if (body) {
    body.innerHTML = "";
  }

  // 2. Desactivar blindaje de eventos
  detachAntiCaptureShield();

  // 3. Ocultar modal
  if (modal) {
    modal.style.display = "none";
  }
  isEphemeralViewerOpen = false;

  // 4. Mostrar tarjeta compacta de cobro posterior
  if (postCard) {
    postCard.style.display = "flex";
    if (postPages) {
      postPages.textContent = currentQuote.paginas || 65;
    }
  }
}

// Cierre al hacer clic en el backdrop
window.addEventListener("click", (e) => {
  const modal = document.getElementById("modal-ephemeral-viewer");
  if (isEphemeralViewerOpen && e.target === modal) {
    destroyAndCloseEphemeralViewer();
  }
});

/* =========================================================================
   BLINDAJE EN CALIENTE: ATAJOS DE TECLADO Y PÉRDIDA DE FOCO (WINDOW.BLUR)
   ========================================================================= */
function onWindowBlurSecurity() {
  if (isEphemeralViewerOpen) {
    const shield = document.getElementById("curtain-security-shield");
    if (shield) shield.classList.add("active");
  }
}

function onWindowFocusSecurity() {
  if (isEphemeralViewerOpen) {
    const shield = document.getElementById("curtain-security-shield");
    if (shield) shield.classList.remove("active");
  }
}

function onVisibilityChangeSecurity() {
  if (isEphemeralViewerOpen && document.hidden) {
    const shield = document.getElementById("curtain-security-shield");
    if (shield) shield.classList.add("active");
  } else if (isEphemeralViewerOpen && !document.hidden) {
    const shield = document.getElementById("curtain-security-shield");
    if (shield) shield.classList.remove("active");
  }
}

function onKeydownAntiCapture(e) {
  if (!isEphemeralViewerOpen) return;

  // Bloqueo de PrintScreen, F12, Ctrl+Shift+I, Ctrl+S, Ctrl+P
  if (e.key === "PrintScreen" || e.keyCode === 44) {
    e.preventDefault();
    triggerSecurityAlarm();
    return false;
  }

  if (e.keyCode === 123) { // F12
    e.preventDefault();
    return false;
  }

  // Ctrl o Cmd + teclas protegidas
  if (e.ctrlKey || e.metaKey) {
    const key = e.key.toLowerCase();
    if (key === "s" || key === "p" || key === "u") {
      e.preventDefault();
      return false;
    }
    // DevTools: Ctrl+Shift+I / Ctrl+Shift+C / Ctrl+Shift+J
    if (e.shiftKey && (key === "i" || key === "c" || key === "j")) {
      e.preventDefault();
      return false;
    }
  }

  // Mac / Windows recorte: Cmd+Shift+3, Cmd+Shift+4, Win+Shift+S
  if (e.shiftKey && (e.metaKey || e.ctrlKey) && (e.key === "3" || e.key === "4" || e.key === "s")) {
    e.preventDefault();
    triggerSecurityAlarm();
    return false;
  }
}

function onContextMenuPrevent(e) {
  if (isEphemeralViewerOpen) {
    e.preventDefault();
    return false;
  }
}

function triggerSecurityAlarm() {
  const shield = document.getElementById("curtain-security-shield");
  if (shield) {
    shield.classList.add("active");
    setTimeout(() => {
      if (document.hasFocus()) shield.classList.remove("active");
    }, 2500);
  }
}

function attachAntiCaptureShield() {
  window.addEventListener("blur", onWindowBlurSecurity);
  window.addEventListener("focus", onWindowFocusSecurity);
  document.addEventListener("visibilitychange", onVisibilityChangeSecurity);
  window.addEventListener("keydown", onKeydownAntiCapture);
  document.addEventListener("contextmenu", onContextMenuPrevent);
}

function detachAntiCaptureShield() {
  window.removeEventListener("blur", onWindowBlurSecurity);
  window.removeEventListener("focus", onWindowFocusSecurity);
  document.removeEventListener("visibilitychange", onVisibilityChangeSecurity);
  window.removeEventListener("keydown", onKeydownAntiCapture);
  document.removeEventListener("contextmenu", onContextMenuPrevent);
  const shield = document.getElementById("curtain-security-shield");
  if (shield) shield.classList.remove("active");
}

/* =========================================================================
   8. ENLACE INTERACTIVO WHATSAPP DIRECTO (+57 320 710 5618)
   ========================================================================= */
async function requestPersonalizedAssistance() {
  const fileName = currentUploadedFile ? currentUploadedFile.name : "mi_trabajo.docx";
  const pages = currentQuote.paginas || 65;
  const tutorNotes = document.getElementById("tutor-instructions")?.value?.trim() || "";

  try {
    const res = await fetch("/api/automation/generate-whatsapp-link", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nombre: "Estudiante",
        celular: "573207105618",
        nombre_archivo: fileName,
        paginas: pages,
        instrucciones: tutorNotes
      })
    });

    const data = await res.json();
    if (data.status === "success" && data.whatsapp_url) {
      window.open(data.whatsapp_url, "_blank");
    } else {
      fallbackWhatsApp(fileName, pages, tutorNotes);
    }
  } catch (err) {
    fallbackWhatsApp(fileName, pages, tutorNotes);
  }
}

function fallbackWhatsApp(fileName, pages, tutorNotes) {
  const msg = encodeURIComponent(
    `Hola, acabo de subir mi trabajo (${fileName}, ${pages} págs) a AcademicPro y me gustaría cotizar la revisión personalizada. Observaciones: '${tutorNotes || "Revisión general y formato APA 7"}'.`
  );
  window.open(`https://wa.me/573207105618?text=${msg}`, "_blank");
}

function togglePasswordVisibility(id = "auth-pwd-input") {
  const input = document.getElementById(id);
  if (!input) return;
  input.type = input.type === "password" ? "text" : "password";
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/* =========================================================================
   6. GESTIÓN DE AUTENTICACIÓN ANÓNIMA (ALIAS Y SESIÓN)
   ========================================================================= */
function openLoginModal() {
  const modalReg = document.getElementById("modal-register");
  if (modalReg) modalReg.style.display = "none";
  const modalLogin = document.getElementById("modal-auth");
  if (modalLogin) {
    modalLogin.style.display = "flex";
    const email = document.getElementById("auth-email-input");
    if (email) setTimeout(() => email.focus(), 50);
  }
}

function closeLoginModal() {
  const modalLogin = document.getElementById("modal-auth");
  if (modalLogin) modalLogin.style.display = "none";
}

function openRegisterModal() {
  const modalLogin = document.getElementById("modal-auth");
  if (modalLogin) modalLogin.style.display = "none";
  const modalReg = document.getElementById("modal-register");
  if (modalReg) {
    modalReg.style.display = "flex";
    const email = document.getElementById("reg-email-input");
    if (email) setTimeout(() => email.focus(), 50);
  }
}

function closeRegisterModal() {
  const modalReg = document.getElementById("modal-register");
  if (modalReg) modalReg.style.display = "none";
}

function openAuthModal(mode = "login") {
  if (mode === "register") {
    openRegisterModal();
  } else {
    openLoginModal();
  }
}

function closeAuthModal() {
  closeLoginModal();
  closeRegisterModal();
}

function switchAuthMode(mode) {
  if (mode === "register") {
    openRegisterModal();
  } else {
    openLoginModal();
  }
}

function getDeviceFingerprint() {
  let fp = localStorage.getItem("academicpro_device_id");
  if (!fp) {
    fp = "dev_" + Math.random().toString(36).substring(2, 12) + "_" + Date.now().toString(36);
    localStorage.setItem("academicpro_device_id", fp);
  }
  return fp;
}

function toggleUserDropdown(e) {
  e.stopPropagation();
  const saved = localStorage.getItem("academicpro_user");
  if (!saved) {
    openLoginModal();
    return;
  }
  const menu = document.getElementById("user-profile-menu");
  if (menu) {
    menu.style.display = (menu.style.display === "none" || !menu.style.display) ? "block" : "none";
  }
}

function handleLogout() {
  localStorage.removeItem("academicpro_user");
  const menu = document.getElementById("user-profile-menu");
  if (menu) menu.style.display = "none";

  const btnLogin = document.getElementById("btn-navbar-login");
  const btnRegister = document.getElementById("btn-navbar-register");
  const btnUser = document.getElementById("btn-user-avatar");
  if (btnLogin) btnLogin.style.display = "inline-flex";
  if (btnRegister) btnRegister.style.display = "inline-flex";
  if (btnUser) btnUser.style.display = "none";

  applyUserSession(null);
  alert("Sesión cerrada correctamente.");
}

// Cerrar menú al hacer clic fuera
window.addEventListener("click", (e) => {
  const menu = document.getElementById("user-profile-menu");
  const avatar = document.getElementById("btn-user-avatar");
  if (menu && menu.style.display === "block" && !menu.contains(e.target) && (!avatar || !avatar.contains(e.target))) {
    menu.style.display = "none";
  }
});

async function handleLoginSubmit(e) {
  if (e) e.preventDefault();
  const emailInput = document.getElementById("auth-email-input");
  const pwdInput = document.getElementById("auth-pwd-input");
  const feedback = document.getElementById("auth-msg-feedback");
  const submitBtn = document.getElementById("auth-submit-btn");

  const email = emailInput ? emailInput.value.trim() : "";
  const password = pwdInput ? pwdInput.value.trim() : "";

  if (feedback) {
    feedback.style.display = "block";
    feedback.style.color = "#014165";
    feedback.textContent = "Verificando credenciales...";
  }
  if (submitBtn) submitBtn.disabled = true;

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) {
      if (feedback) {
        feedback.style.color = "#DC2626";
        feedback.textContent = data.detail || "Credenciales inválidas. Revisa tu correo o contraseña.";
      }
      return;
    }

    const user = data.user;
    localStorage.setItem("academicpro_user", JSON.stringify(user));

    if (feedback) {
      feedback.style.color = "#16A34A";
      feedback.textContent = "¡Sesión iniciada con éxito! Bienvenido.";
    }

    setTimeout(() => {
      closeAuthModal();
      applyUserSession(user);
    }, 600);

  } catch (err) {
    if (feedback) {
      feedback.style.color = "#DC2626";
      feedback.textContent = "Error al conectar con el servidor.";
    }
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

async function handleRegisterSubmit(e) {
  if (e) e.preventDefault();
  const emailInput = document.getElementById("reg-email-input");
  const aliasInput = document.getElementById("reg-alias-input");
  const instSelect = document.getElementById("reg-inst-select");
  const pwdInput = document.getElementById("reg-pwd-input");
  const confirmPwdInput = document.getElementById("reg-pwd-confirm-input");
  const feedback = document.getElementById("auth-reg-feedback");
  const submitBtn = document.getElementById("auth-reg-submit-btn");

  const email = emailInput ? emailInput.value.trim() : "";
  const username_alias = aliasInput ? aliasInput.value.trim() : "Estudiante";
  const institution = instSelect ? instSelect.value : "UNAD";
  const password = pwdInput ? pwdInput.value.trim() : "";
  const confirmPassword = confirmPwdInput ? confirmPwdInput.value.trim() : "";

  if (password.length < 4) {
    if (feedback) {
      feedback.style.display = "block";
      feedback.style.color = "#DC2626";
      feedback.textContent = "La contraseña debe tener al menos 4 caracteres.";
    }
    return;
  }

  if (password !== confirmPassword) {
    if (feedback) {
      feedback.style.display = "block";
      feedback.style.color = "#DC2626";
      feedback.textContent = "Las contraseñas no coinciden. Por favor verifícalas.";
    }
    return;
  }

  if (feedback) {
    feedback.style.display = "block";
    feedback.style.color = "#014165";
    feedback.textContent = "Creando tu cuenta y asignando tus 2 créditos de bienvenida...";
  }
  if (submitBtn) submitBtn.disabled = true;

  try {
    const res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        username_alias,
        institution,
        password,
        device_fingerprint: getDeviceFingerprint()
      })
    });
    const data = await res.json();
    if (!res.ok) {
      if (feedback) {
        feedback.style.color = "#DC2626";
        feedback.textContent = data.detail || "Error al crear la cuenta. Intenta de nuevo.";
      }
      return;
    }

    const user = data.user;
    localStorage.setItem("academicpro_user", JSON.stringify(user));

    if (feedback) {
      feedback.style.color = "#16A34A";
      feedback.textContent = user.message || "¡Cuenta creada con éxito! 2 Créditos asignados.";
    }

    setTimeout(() => {
      closeRegisterModal();
      applyUserSession(user);
    }, 700);

  } catch (err) {
    if (feedback) {
      feedback.style.color = "#DC2626";
      feedback.textContent = "Error de red al procesar el registro.";
    }
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

async function handleAuthSubmit(e) {
  if (currentAuthMode === "register") {
    return handleRegisterSubmit(e);
  } else {
    return handleLoginSubmit(e);
  }
}

function applyUserSession(user) {
  const btnLogin = document.getElementById("btn-navbar-login");
  const btnRegister = document.getElementById("btn-navbar-register");
  const btnUser = document.getElementById("btn-user-avatar");

  if (user && user.email) {
    // Modo autenticado: ocultar botones de login y registro, mostrar chip de usuario
    if (btnLogin) btnLogin.style.display = "none";
    if (btnRegister) btnRegister.style.display = "none";
    if (btnUser) btnUser.style.display = "inline-flex";

    const initials = user.username_alias ? user.username_alias.substring(0, 2).toUpperCase() : "ES";
    const avatarEl = document.getElementById("user-avatar-initials");
    if (avatarEl) avatarEl.textContent = initials;

    const navAlias = document.getElementById("navbar-user-alias");
    if (navAlias) navAlias.textContent = user.username_alias || "Estudiante";

    userBalance = user.balance !== undefined ? user.balance : 0;
    const countEl = document.getElementById("credit-count");
    if (countEl) countEl.textContent = userBalance;

    const dropAlias = document.getElementById("drop-user-alias");
    const dropInst = document.getElementById("drop-user-inst");
    const dropEmail = document.getElementById("drop-user-email");
    const dropBalance = document.getElementById("drop-user-balance");

    if (dropAlias) dropAlias.textContent = `👤 ${user.username_alias}`;
    if (dropInst) dropInst.textContent = user.institution || "UNAD";
    if (dropEmail) dropEmail.textContent = user.email;
    if (dropBalance) dropBalance.textContent = `${userBalance} Créditos`;

    if (btnUser) btnUser.title = `${user.username_alias} (${user.email}) - ${userBalance} Créditos`;
  } else {
    // Modo anónimo: mostrar botones de login y registro, ocultar chip de usuario
    if (btnLogin) btnLogin.style.display = "inline-flex";
    if (btnRegister) btnRegister.style.display = "inline-flex";
    if (btnUser) btnUser.style.display = "none";

    userBalance = 0;
    const countEl = document.getElementById("credit-count");
    if (countEl) countEl.textContent = "0";
  }
}

function restoreUserSession() {
  try {
    const saved = localStorage.getItem("academicpro_user");
    if (saved) {
      const user = JSON.parse(saved);
      applyUserSession(user);
    } else {
      applyUserSession(null);
    }
  } catch (e) {
    applyUserSession(null);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  restoreUserSession();
});
