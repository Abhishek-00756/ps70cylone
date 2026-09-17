import { api } from "../services/api.js";
import { loadingHtml, errorHtml } from "../utils/dom.js";

const CLASS_ORDER = [
  "DEPRESSION", "DEEP_DEPRESSION", "CYCLONIC_STORM", "SEVERE_CYCLONIC_STORM",
  "VERY_SEVERE_CYCLONIC_STORM", "EXTREMELY_SEVERE_CYCLONIC_STORM", "SUPER_CYCLONIC_STORM",
];

export async function renderDetection(container) {
  container.innerHTML = `
    <div class="page-title">AI Cyclone Detection</div>
    <div class="page-subtitle">Prototype feature classifier — <span class="tag demo">Trained on synthetic imagery</span></div>
    <div class="pipeline-flow" id="pipeline-flow"></div>
    <div id="detect-body">${loadingHtml()}</div>
  `;

  try {
    const [cyclone, features] = await Promise.all([api.cyclone("DEMO-01"), api.features("DEMO-01")]);
    renderPipeline();
    renderBody(cyclone, features);
  } catch (e) {
    document.getElementById("detect-body").innerHTML = errorHtml(e);
  }
}

function renderPipeline() {
  const steps = ["Satellite Input", "Preprocessing", "Feature Extraction", "Feature Classifier", "Temporal Analysis", "Classification"];
  document.getElementById("pipeline-flow").innerHTML = steps
    .map((s, i) => `<div class="pipeline-step"><span class="check">✓</span>${s}</div>${i < steps.length - 1 ? '<span class="pipeline-arrow">→</span>' : ""}`)
    .join("");
}

function renderBody(cyclone, featuresResp) {
  const latest = cyclone.latest;
  const el = document.getElementById("detect-body");
  el.innerHTML = `
    <div class="grid grid-2">
      <div class="card">
        <h3>Detection Result</h3>
        <div class="stat-row"><span class="label">Cyclone detected</span><span class="value">${latest.detected ? "YES" : "NO"}</span></div>
        <div class="stat-row"><span class="label">Detection confidence</span><span class="value">${(latest.detection_confidence*100).toFixed(1)}%</span></div>
        <div class="stat-row"><span class="label">Classification</span><span class="value">${latest.classification.replaceAll("_"," ")}</span></div>
        <div class="stat-row"><span class="label">Classifier confidence</span><span class="value">${(latest.classification_confidence*100).toFixed(1)}%</span></div>
        <p class="footer-note">Classification comes from <code>ml/classification/classifier.py</code>: a RandomForest trained on synthetic demo imagery over 12 extracted features (coarse classes only: NO_CYCLONE / DEPRESSION / CYCLONIC_STORM / SEVERE_CYCLONIC_STORM). The full 7-tier IMD scale shown below is applied deterministically to the estimated wind speed, not predicted by the model.</p>
      </div>
      <div class="card">
        <h3>IMD Classification Scale (estimated wind: ${cyclone.latest.wind_speed_kt} kt)</h3>
        <table class="plain">
          <tr><th>Category</th><th>Wind range (kt)</th></tr>
          <tr><td>Low Pressure Area</td><td>&lt; 17</td></tr>
          <tr><td>Depression</td><td>17 – 27</td></tr>
          <tr><td>Deep Depression</td><td>28 – 33</td></tr>
          <tr><td>Cyclonic Storm</td><td>34 – 47</td></tr>
          <tr><td>Severe Cyclonic Storm</td><td>48 – 63</td></tr>
          <tr><td>Very Severe Cyclonic Storm</td><td>64 – 89</td></tr>
          <tr><td>Extremely Severe Cyclonic Storm</td><td>90 – 119</td></tr>
          <tr><td>Super Cyclonic Storm</td><td>≥ 120</td></tr>
        </table>
      </div>
    </div>

    <div class="card" style="margin-top:14px;">
      <h3>Extracted Feature Vector (latest timestep)</h3>
      <div class="grid grid-4" id="feature-grid"></div>
    </div>

    <div class="card" style="margin-top:14px;">
      <h3>AI Reasoning — Prototype Feature-Based Explanation</h3>
      <div id="reasoning"></div>
    </div>
  `;

  const fg = document.getElementById("feature-grid");
  Object.entries(featuresResp.features).forEach(([k, v]) => {
    fg.appendChild(featureCard(k, v));
  });

  const reasoning = featuresResp.reasoning;
  const rEl = document.getElementById("reasoning");
  if (!reasoning.contributing_factors.length) {
    rEl.innerHTML = `<div class="empty-state">No dominant factors crossed the explanation threshold at this timestep.</div>`;
  } else {
    rEl.innerHTML = reasoning.contributing_factors
      .map(
        (f) => `<div class="factor-bar">
          <span class="name">${f.factor}</span>
          <span class="bar-bg"><span class="bar-fill ${f.direction === "+" ? "plus" : "minus"}" style="width:${Math.round(f.contribution*100)}%"></span></span>
          <span style="width:34px; text-align:right; font-family:var(--mono)">${f.direction}${Math.round(f.contribution*100)}%</span>
        </div>`
      )
      .join("");
  }
}

function featureCard(name, value) {
  const div = document.createElement("div");
  div.className = "card tight";
  div.innerHTML = `<div style="font-size:10.5px; color:var(--text-2); text-transform:uppercase; letter-spacing:0.04em;">${name.replaceAll("_"," ")}</div>
    <div style="font-family:var(--mono); font-size:17px; margin-top:4px;">${value}</div>`;
  return div;
}
