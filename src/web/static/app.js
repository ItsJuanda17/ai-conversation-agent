/* ─── DOM Elements ────────────────────────────────────────── */
const tabs = Array.from(document.querySelectorAll(".tab"));
const views = Array.from(document.querySelectorAll(".view"));
const viewTitle = document.querySelector("#viewTitle");
const viewSubtitle = document.querySelector("#viewSubtitle");
const resultPanel = document.querySelector("#resultPanel");
const apiStatus = document.querySelector("#apiStatus");
const sampleButton = document.querySelector("#sampleButton");
const sidebar = document.querySelector("#sidebar");
const menuToggle = document.querySelector("#menuToggle");
const sidebarOverlay = document.querySelector("#sidebarOverlay");

/* ─── Config ──────────────────────────────────────────────── */
const tabConfig = {
  emociones:    { title: "Emociones",       subtitle: "Análisis de sentimiento" },
  resumen:      { title: "Resumen",         subtitle: "Síntesis de hilos" },
  propagacion:  { title: "Propagación",     subtitle: "Árbol de respuestas" },
  rag:          { title: "Búsqueda RAG",    subtitle: "Búsqueda semántica vectorial" },
};

const samples = {
  emociones:    { query: "reforma laboral", limit: 8 },
  resumen:      { thread_id: "tikapi_7520430294948793606", limit: 25 },
  propagacion:  { root_id: "106064209472141_767905085584441", max_depth: 10 },
  rag:          { query: "preocupaciones sobre reforma laboral", limit: 6 },
};

const emotionIcons = {
  joy:     "😊",
  anger:   "😠",
  fear:    "😨",
  sadness: "😢",
  neutral: "😐",
};

let activeTab = "emociones";

/* ─── Utilities ───────────────────────────────────────────── */
function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr);
    if (isNaN(d)) return dateStr;
    return d.toLocaleDateString("es-CO", { day: "numeric", month: "short", year: "numeric" });
  } catch { return dateStr; }
}

/* ─── Tab Navigation ──────────────────────────────────────── */
function setActiveTab(tabName) {
  activeTab = tabName;
  tabs.forEach((t) => t.classList.toggle("active", t.dataset.tab === tabName));
  views.forEach((v) => v.classList.toggle("active", v.id === `view-${tabName}`));
  const cfg = tabConfig[tabName];
  viewTitle.textContent = cfg.title;
  viewSubtitle.textContent = cfg.subtitle;
  closeMobileSidebar();
}

/* ─── Mobile Sidebar ──────────────────────────────────────── */
function openMobileSidebar() {
  sidebar.classList.add("open");
  sidebarOverlay.classList.add("open");
}

function closeMobileSidebar() {
  sidebar.classList.remove("open");
  sidebarOverlay.classList.remove("open");
}

/* ─── Sample Data ─────────────────────────────────────────── */
function fillSample() {
  const form = document.querySelector(`#view-${activeTab} form`);
  const sample = samples[activeTab];
  Object.entries(sample).forEach(([name, value]) => {
    const input = form.elements.namedItem(name);
    if (input) input.value = value;
  });
}

/* ─── Health Check ────────────────────────────────────────── */
async function checkHealth() {
  try {
    const r = await fetch("/health");
    if (!r.ok) throw new Error();
    apiStatus.innerHTML = `<span class="status-dot"></span> API activa`;
    apiStatus.className = "status-pill ok";
  } catch {
    apiStatus.innerHTML = `<span class="status-dot"></span> Sin conexión`;
    apiStatus.className = "status-pill error";
  }
}

/* ─── Form Submission ─────────────────────────────────────── */
function formPayload(form) {
  return Object.fromEntries(
    Array.from(new FormData(form).entries()).map(([key, value]) => {
      const input = form.elements.namedItem(key);
      return [key, input?.type === "number" ? Number(value) : value];
    })
  );
}

async function submitForm(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const endpoint = form.dataset.endpoint;
  const renderer = form.dataset.renderer;
  const submitBtn = form.querySelector(".submit-btn");

  submitBtn.disabled = true;
  resultPanel.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <span class="loading-text">Procesando con IA...</span>
    </div>`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formPayload(form)),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || `Error ${response.status}`);
    resultPanel.innerHTML = renderResult(renderer, data);
  } catch (error) {
    resultPanel.innerHTML = `<div class="error-box">⚠ ${escapeHtml(error.message)}</div>`;
  } finally {
    submitBtn.disabled = false;
  }
}

/* ─── Renderers ───────────────────────────────────────────── */
function renderResult(renderer, data) {
  if (renderer === "emotions") return renderEmotions(data);
  if (renderer === "summary") return renderSummary(data);
  if (renderer === "propagation") return renderPropagation(data);
  if (renderer === "search") return renderSearch(data);
  return `<pre style="overflow:auto;padding:16px;font-size:12px">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
}

function renderMetrics(items) {
  return `
    <div class="metrics-grid">
      ${items.map(([label, value]) => `
        <div class="metric">
          <b>${escapeHtml(value)}</b>
          <span>${escapeHtml(label)}</span>
        </div>
      `).join("")}
    </div>`;
}

function renderBars(distribution, emotionColored = false) {
  const entries = Object.entries(distribution || {});
  const max = Math.max(...entries.map(([, v]) => v), 1);
  if (!entries.length) return `<p class="message-text" style="color:var(--ink-muted)">Sin datos de distribución.</p>`;

  return `
    <div class="bars">
      ${entries.map(([label, value]) => {
        const emotionAttr = emotionColored ? `data-emotion="${escapeHtml(label)}"` : `data-emotion="default"`;
        return `
        <div class="bar-row">
          <span class="bar-label">${emotionIcons[label] || ""} ${escapeHtml(label)}</span>
          <div class="bar-track">
            <div class="bar-fill" ${emotionAttr} style="width: ${(value / max) * 100}%"></div>
          </div>
          <strong class="bar-value">${escapeHtml(value)}</strong>
        </div>`;
      }).join("")}
    </div>`;
}

function renderMessages(messages, limit = 8) {
  const items = (messages || []).slice(0, limit);
  if (!items.length) return `<p class="message-text" style="color:var(--ink-muted)">Sin mensajes para mostrar.</p>`;

  return `
    <div class="message-list">
      ${items.map((msg) => {
        const emotion = msg.emotion || "";
        const sentiment = msg.sentiment || "";
        const tagClass = emotion || sentiment;
        const tagText = emotion || sentiment || "sin etiqueta";

        return `
        <article class="message-item">
          <div class="message-meta">
            ${emotion
              ? `<span class="emotion-tag ${escapeHtml(emotion)}">${emotionIcons[emotion] || ""} ${escapeHtml(emotion)}</span>`
              : sentiment
                ? `<span class="sentiment-tag ${escapeHtml(sentiment)}">${escapeHtml(sentiment)}</span>`
                : `<span class="meta-label">sin etiqueta</span>`
            }
            ${msg.social_type ? `<span class="meta-label">${escapeHtml(msg.social_type)}</span>` : ""}
            ${msg.created_at ? `<span class="meta-label">${formatDate(msg.created_at)}</span>` : ""}
          </div>
          <p class="message-text">${escapeHtml(msg.text)}</p>
        </article>`;
      }).join("")}
    </div>`;
}

/* ─── Specific Renderers ──────────────────────────────────── */
function renderEmotions(data) {
  return `
    <section class="result-section">
      <div class="section-heading">
        <h3>Distribución emocional</h3>
        <span>${escapeHtml(data.total_comments)} comentarios</span>
      </div>
      ${renderBars(data.emotion_distribution, true)}
    </section>
    <section class="result-section">
      <div class="section-heading">
        <h3>Comentarios</h3>
        <span>Tema: ${escapeHtml(data.query)}</span>
      </div>
      ${renderMessages(data.comments)}
    </section>`;
}

function renderSummary(data) {
  const summaryHtml = (data.representative_messages || []).length > 0
    ? `<div class="message-list">
        ${data.representative_messages.map((item) => `
          <div class="summary-item">
            <p class="message-text">${escapeHtml(item)}</p>
          </div>
        `).join("")}
       </div>`
    : `<p class="message-text" style="color:var(--ink-muted)">Sin resumen disponible.</p>`;

  return `
    <section class="result-section">
      <div class="section-heading">
        <h3>Resumen del hilo</h3>
        <span>${escapeHtml(data.total_messages)} mensajes</span>
      </div>
      ${summaryHtml}
    </section>
    <section class="result-section">
      <div class="section-heading">
        <h3>Distribución de sentimiento</h3>
        <span>${escapeHtml(data.thread_id)}</span>
      </div>
      ${renderBars(data.sentiment_distribution)}
    </section>`;
}

function renderPropagation(data) {
  const m = data.metrics || {};
  return `
    <section class="result-section">
      <div class="section-heading">
        <h3>Métricas de propagación</h3>
        <span>${data.root_found ? "✓ Raíz encontrada" : "⊘ Raíz externa"}</span>
      </div>
      ${renderMetrics([
        ["Respuestas directas", data.direct_replies],
        ["Total descendientes", data.total_descendants],
        ["Profundidad máxima", data.max_depth_observed],
        ["Autores únicos", m.unique_authors ?? 0],
      ])}
    </section>
    <section class="result-section">
      <div class="section-heading">
        <h3>Ventana temporal</h3>
        <span>${escapeHtml(data.root_id)}</span>
      </div>
      ${renderMetrics([
        ["Primera respuesta", m.first_reply_at || "n/a"],
        ["Última respuesta", m.last_reply_at || "n/a"],
        ["Minutos totales", m.propagation_minutes ?? "n/a"],
        ["Resp/hora", Number(m.average_replies_per_hour ?? 0).toFixed(2)],
      ])}
    </section>
    <section class="result-section">
      <div class="section-heading">
        <h3>Árbol de respuestas</h3>
        <span>${escapeHtml(data.total_descendants)} nodos</span>
      </div>
      ${renderMessages(data.descendants)}
    </section>`;
}

function renderSearch(data) {
  return `
    <section class="result-section">
      <div class="section-heading">
        <h3>Resultados semánticos</h3>
        <span>${escapeHtml(data.total_results)} coincidencias para "${escapeHtml(data.query)}"</span>
      </div>
      ${renderMessages(data.results, 10)}
    </section>`;
}

/* ─── Event Listeners ─────────────────────────────────────── */
tabs.forEach((t) => t.addEventListener("click", () => setActiveTab(t.dataset.tab)));
sampleButton.addEventListener("click", fillSample);
document.querySelectorAll(".query-form").forEach((f) => f.addEventListener("submit", submitForm));
menuToggle?.addEventListener("click", openMobileSidebar);
sidebarOverlay?.addEventListener("click", closeMobileSidebar);

/* ─── Init ────────────────────────────────────────────────── */
checkHealth();
setInterval(checkHealth, 30000);
