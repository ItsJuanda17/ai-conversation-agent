const tabs = Array.from(document.querySelectorAll(".tab"));
const views = Array.from(document.querySelectorAll(".view"));
const viewTitle = document.querySelector("#viewTitle");
const resultPanel = document.querySelector("#resultPanel");
const apiStatus = document.querySelector("#apiStatus");
const sampleButton = document.querySelector("#sampleButton");

const titles = {
  emociones: "Emociones",
  resumen: "Resumen",
  propagacion: "Propagacion",
  rag: "Busqueda RAG",
};

const samples = {
  emociones: { query: "reforma laboral", limit: 8 },
  resumen: { thread_id: "tikapi_7520430294948793606", limit: 25 },
  propagacion: { root_id: "106064209472141_767905085584441", max_depth: 10 },
  rag: { query: "preocupaciones sobre reforma laboral", limit: 6 },
};

let activeTab = "emociones";

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setActiveTab(tabName) {
  activeTab = tabName;
  tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === tabName));
  views.forEach((view) => view.classList.toggle("active", view.id === `view-${tabName}`));
  viewTitle.textContent = titles[tabName];
}

function activeForm() {
  return document.querySelector(`#view-${activeTab} form`);
}

function fillSample() {
  const form = activeForm();
  const sample = samples[activeTab];
  Object.entries(sample).forEach(([name, value]) => {
    const input = form.elements.namedItem(name);
    if (input) input.value = value;
  });
}

async function checkHealth() {
  try {
    const response = await fetch("/health");
    if (!response.ok) throw new Error("API unavailable");
    apiStatus.textContent = "API activa";
    apiStatus.className = "status-pill ok";
  } catch {
    apiStatus.textContent = "API sin conexion";
    apiStatus.className = "status-pill error";
  }
}

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

  resultPanel.innerHTML = `<div class="empty-state">Procesando...</div>`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formPayload(form)),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Request failed");
    resultPanel.innerHTML = renderResult(renderer, data);
  } catch (error) {
    resultPanel.innerHTML = `<div class="error-box">${escapeHtml(error.message)}</div>`;
  }
}

function renderResult(renderer, data) {
  if (renderer === "emotions") return renderEmotions(data);
  if (renderer === "summary") return renderSummary(data);
  if (renderer === "propagation") return renderPropagation(data);
  if (renderer === "search") return renderSearch(data);
  return `<pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
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
    </div>
  `;
}

function renderBars(distribution) {
  const entries = Object.entries(distribution || {});
  const max = Math.max(...entries.map(([, value]) => value), 1);
  if (!entries.length) return `<p class="message-text">Sin datos.</p>`;

  return `
    <div class="bars">
      ${entries.map(([label, value]) => `
        <div class="bar-row">
          <span>${escapeHtml(label)}</span>
          <div class="bar-track">
            <div class="bar-fill" style="width: ${(value / max) * 100}%"></div>
          </div>
          <strong>${escapeHtml(value)}</strong>
        </div>
      `).join("")}
    </div>
  `;
}

function renderMessages(messages, limit = 8) {
  const items = (messages || []).slice(0, limit);
  if (!items.length) return `<p class="message-text">Sin mensajes para mostrar.</p>`;

  return `
    <div class="message-list">
      ${items.map((message) => `
        <article class="message-item">
          <div class="message-meta">
            <span>${escapeHtml(message.emotion || message.sentiment || "sin etiqueta")}</span>
            <span>${escapeHtml(message.social_type || "fuente no disponible")}</span>
            <span>${escapeHtml(message.created_at || "")}</span>
          </div>
          <p class="message-text">${escapeHtml(message.text)}</p>
        </article>
      `).join("")}
    </div>
  `;
}

function renderEmotions(data) {
  return `
    <section class="result-section">
      <div class="section-heading">
        <h3>Distribucion emocional</h3>
        <span>${escapeHtml(data.total_comments)} comentarios</span>
      </div>
      ${renderBars(data.emotion_distribution)}
    </section>
    <section class="result-section">
      <div class="section-heading">
        <h3>Comentarios</h3>
        <span>${escapeHtml(data.query)}</span>
      </div>
      ${renderMessages(data.comments)}
    </section>
  `;
}

function renderSummary(data) {
  return `
    <section class="result-section">
      <div class="section-heading">
        <h3>Resumen</h3>
        <span>${escapeHtml(data.total_messages)} mensajes</span>
      </div>
      <div class="message-list">
        ${(data.representative_messages || []).map((item) => `
          <article class="message-item"><p class="message-text">${escapeHtml(item)}</p></article>
        `).join("") || `<p class="message-text">Sin resumen disponible.</p>`}
      </div>
    </section>
    <section class="result-section">
      <div class="section-heading">
        <h3>Sentimiento</h3>
        <span>${escapeHtml(data.thread_id)}</span>
      </div>
      ${renderBars(data.sentiment_distribution)}
    </section>
  `;
}

function renderPropagation(data) {
  const metrics = data.metrics || {};
  return `
    <section class="result-section">
      <div class="section-heading">
        <h3>Metricas</h3>
        <span>${data.root_found ? "raiz encontrada" : "raiz externa"}</span>
      </div>
      ${renderMetrics([
        ["Respuestas directas", data.direct_replies],
        ["Descendientes", data.total_descendants],
        ["Profundidad maxima", data.max_depth_observed],
        ["Autores unicos", metrics.unique_authors ?? 0],
      ])}
    </section>
    <section class="result-section">
      <div class="section-heading">
        <h3>Ventana temporal</h3>
        <span>${escapeHtml(data.root_id)}</span>
      </div>
      ${renderMetrics([
        ["Primera respuesta", metrics.first_reply_at || "n/a"],
        ["Ultima respuesta", metrics.last_reply_at || "n/a"],
        ["Minutos", metrics.propagation_minutes ?? "n/a"],
        ["Resp/hora", Number(metrics.average_replies_per_hour ?? 0).toFixed(2)],
      ])}
    </section>
    <section class="result-section">
      <div class="section-heading">
        <h3>Arbol</h3>
        <span>${escapeHtml(data.total_descendants)} nodos</span>
      </div>
      ${renderMessages(data.descendants)}
    </section>
  `;
}

function renderSearch(data) {
  return `
    <section class="result-section">
      <div class="section-heading">
        <h3>Resultados semanticos</h3>
        <span>${escapeHtml(data.total_results)} coincidencias</span>
      </div>
      ${renderMessages(data.results, 10)}
    </section>
  `;
}

tabs.forEach((tab) => tab.addEventListener("click", () => setActiveTab(tab.dataset.tab)));
sampleButton.addEventListener("click", fillSample);
document.querySelectorAll(".query-form").forEach((form) => form.addEventListener("submit", submitForm));

checkHealth();
