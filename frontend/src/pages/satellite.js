import { api, fmtTime } from "../services/api.js";
import { loadingHtml, errorHtml } from "../utils/dom.js";

export async function renderSatellite(container) {
  container.innerHTML = `
    <div class="page-title">Satellite Analysis</div>
    <div class="page-subtitle">Multi-source imagery workspace — <span class="tag demo">Synthetic Demo Imagery, not real satellite data</span></div>
    <div id="sat-body">${loadingHtml()}</div>
  `;

  try {
    const meta = await api.satelliteMeta("DEMO-01");
    const featuresResp0 = await api.features("DEMO-01"); // for initial feature panel shape
    renderBody(meta, featuresResp0);
  } catch (e) {
    document.getElementById("sat-body").innerHTML = errorHtml(e);
  }
}

function renderBody(meta, featuresResp) {
  const body = document.getElementById("sat-body");
  const timestamps = meta.available_timestamps;
  let idx = timestamps.length - 1;

  body.innerHTML = `
    <div class="card" style="margin-bottom:14px;">
      <h3>Provider</h3>
      <div class="stat-row"><span class="label">Source</span><span class="value">${meta.provider.name}</span></div>
      <div class="stat-row"><span class="label">Status</span><span class="value"><span class="tag demo">${meta.provider.status}</span></span></div>
      <div class="stat-row"><span class="label">Purpose</span><span class="value" style="font-weight:400; text-align:right;">${meta.provider.purpose}</span></div>
    </div>

    <div class="card" style="margin-bottom:14px;">
      <h3>Timeline</h3>
      <div class="timeline">
        <button class="btn small secondary" id="tl-prev">◀</button>
        <input type="range" id="tl-range" min="0" max="${timestamps.length - 1}" value="${idx}" />
        <button class="btn small secondary" id="tl-next">▶</button>
        <span class="timeline-ts" id="tl-ts"></span>
      </div>
    </div>

    <div class="grid grid-2">
      <div class="card">
        <h3>Multi-Channel Imagery</h3>
        <div class="satellite-grid">
          <div class="sat-frame"><img id="img-ir" /><div class="label">Infrared (cloud-top temp proxy)</div></div>
          <div class="sat-frame"><img id="img-vis" /><div class="label">Visible</div></div>
          <div class="sat-frame"><img id="img-wv" /><div class="label">Water Vapour</div></div>
        </div>
        <p class="footer-note">SST, Rainfall/QPE, Wind/CMV, and Vertical Wind Shear are represented as extracted numeric proxies in the AI Feature Extraction panel (right) rather than separate demo imagery layers in this prototype.</p>
      </div>
      <div class="card">
        <h3>AI Feature Extraction</h3>
        <div id="feature-list"></div>
      </div>
    </div>
  `;

  const range = document.getElementById("tl-range");
  const tsLabel = document.getElementById("tl-ts");

  async function update(i) {
    idx = Math.max(0, Math.min(timestamps.length - 1, i));
    range.value = idx;
    const ts = timestamps[idx];
    tsLabel.textContent = fmtTime(ts) + `  (t${idx - (timestamps.length - 1) === 0 ? "" : idx - (timestamps.length - 1) + "h*3"})`;
    document.getElementById("img-ir").src = api.satelliteFrameUrl("DEMO-01", ts, "infrared");
    document.getElementById("img-vis").src = api.satelliteFrameUrl("DEMO-01", ts, "visible");
    document.getElementById("img-wv").src = api.satelliteFrameUrl("DEMO-01", ts, "water_vapor");

    try {
      const cyclone = await api.cyclone("DEMO-01");
      const step = cyclone.history[idx];
      renderFeatureList(step);
    } catch (_) {}
  }

  range.addEventListener("input", (e) => update(parseInt(e.target.value, 10)));
  document.getElementById("tl-prev").addEventListener("click", () => update(idx - 1));
  document.getElementById("tl-next").addEventListener("click", () => update(idx + 1));

  update(idx);
}

function renderFeatureList(step) {
  const el = document.getElementById("feature-list");
  el.innerHTML = `
    <div class="stat-row"><span class="label">Classification (at this timestep)</span><span class="value">${step.classification.replaceAll("_"," ")}</span></div>
    <div class="stat-row"><span class="label">Detection confidence</span><span class="value">${(step.detection_confidence*100).toFixed(0)}%</span></div>
    <div class="stat-row"><span class="label">Wind speed (est.)</span><span class="value">${step.wind_speed_kt} kt</span></div>
    <div class="stat-row"><span class="label">Central pressure (est.)</span><span class="value">${step.central_pressure_hpa} hPa</span></div>
    <p class="footer-note" style="margin-top:12px;">Full 12-dimension feature vector (symmetry, circularity, spiral bands, eye probability, SST/shear proxies, etc.) is computed per-frame and used identically by classification, intensity, and risk — see the AI Detection page for the complete vector.</p>
  `;
}
