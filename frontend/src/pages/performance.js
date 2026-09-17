import { api } from "../services/api.js";
import { loadingHtml, errorHtml } from "../utils/dom.js";

export async function renderPerformance(container) {
  container.innerHTML = `
    <div class="page-title">Model Performance</div>
    <div class="page-subtitle">Transparency page — <span class="tag demo">Prototype / Synthetic Dataset Evaluation</span></div>
    <div id="perf-body">${loadingHtml()}</div>
  `;

  try {
    const metrics = await api.modelMetrics();
    renderBody(metrics);
  } catch (e) {
    document.getElementById("perf-body").innerHTML = errorHtml(e);
  }
}

function renderBody(m) {
  const el = document.getElementById("perf-body");
  el.innerHTML = `
    <div class="card" style="margin-bottom:14px; border-color: var(--warn);">
      <h3 style="color:var(--warn);">⚠ ${m.dataset}</h3>
      <p style="font-size:12.5px; color:var(--text-1);">${m.disclaimer}</p>
    </div>

    <div class="grid grid-3" style="margin-bottom:14px;">
      <div class="card"><div class="big-stat">${(m.accuracy*100).toFixed(1)}%</div><div class="big-stat-label">Overall accuracy (synthetic)</div></div>
      <div class="card"><div class="big-stat">${m.n_samples}</div><div class="big-stat-label">Evaluation samples</div></div>
      <div class="card"><div class="big-stat">${m.classes.length}</div><div class="big-stat-label">Classes</div></div>
    </div>

    <div class="grid grid-2">
      <div class="card">
        <h3>Per-Class Metrics</h3>
        <table class="plain">
          <tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr>
          ${m.per_class.map((c) => `<tr><td>${c.class.replaceAll("_"," ")}</td><td>${c.precision}</td><td>${c.recall}</td><td>${c.f1}</td><td>${c.support}</td></tr>`).join("")}
        </table>
      </div>
      <div class="card">
        <h3>Confusion Matrix</h3>
        ${confusionTable(m.classes, m.confusion_matrix)}
      </div>
    </div>

    <div class="card" style="margin-top:14px;">
      <h3>Known Limitations</h3>
      <ul style="font-size:12.5px; color:var(--text-1); line-height:1.8; margin:0; padding-left:18px;">
        <li>Classifier trained and evaluated entirely on synthetically generated demo imagery — not real satellite data.</li>
        <li>No PyTorch/GPU training framework was available in the build environment; a scikit-learn RandomForest over engineered features is used in place of a CNN.</li>
        <li>Track forecasting is a simple linear-extrapolation prototype, not an operational NWP model.</li>
        <li>Intensity, risk exposure, and vulnerability values use documented but uncalibrated formulas — not fitted against real historical cyclone outcomes.</li>
      </ul>
    </div>
  `;
}

function confusionTable(classes, matrix) {
  const header = `<tr><th></th>${classes.map((c) => `<th>${c.split("_")[0]}</th>`).join("")}</tr>`;
  const rows = matrix
    .map((row, i) => `<tr><th>${classes[i].split("_")[0]}</th>${row.map((v, j) => `<td style="${i===j ? 'color:var(--good); font-weight:700;' : ''}">${v}</td>`).join("")}</tr>`)
    .join("");
  return `<table class="plain">${header}${rows}</table>`;
}
