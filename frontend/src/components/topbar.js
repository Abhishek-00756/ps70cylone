import { api } from "../services/api.js";

export async function renderTopbar() {
  const el = document.getElementById("topbar");
  el.innerHTML = `<div class="status-group" id="status-group"><span class="status-pill"><span class="dot"></span>Connecting…</span></div>
    <div class="mode-badge" id="mode-badge">…</div>`;

  try {
    const status = await api.systemStatus();
    const dotClass = (v) => (v === "ONLINE" ? "on" : v === "DEMO" ? "demo" : "");
    document.getElementById("status-group").innerHTML = `
      <span class="status-pill"><span class="dot ${dotClass(status.components.satellite_feed)}"></span>Satellite Feed: ${status.components.satellite_feed}</span>
      <span class="status-pill"><span class="dot ${dotClass(status.components.ai_engine)}"></span>AI Engine: ${status.components.ai_engine}</span>
      <span class="status-pill"><span class="dot ${dotClass(status.components.weather_data)}"></span>Weather Data: ${status.components.weather_data}</span>
      <span class="status-pill"><span class="dot ${dotClass(status.components.prediction_engine)}"></span>Prediction Engine: ${status.components.prediction_engine}</span>
    `;
    document.getElementById("mode-badge").textContent = status.mode === "DEMO" ? "DEMO MODE" : "LIVE DATA";
  } catch (e) {
    document.getElementById("status-group").innerHTML = `<span class="status-pill" style="color:var(--bad)"><span class="dot" style="background:var(--bad)"></span>Backend unavailable</span>`;
    document.getElementById("mode-badge").textContent = "OFFLINE";
  }
}
