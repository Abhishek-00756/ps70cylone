import { api, fmtTime } from "../services/api.js";
import { loadingHtml, errorHtml } from "../utils/dom.js";

export async function renderDashboard(container) {
  container.innerHTML = `
    <div class="page-title">Live Overview</div>
    <div class="page-subtitle">Bay of Bengal · North Indian Ocean basin — <span class="tag demo">Demo Scenario</span></div>
    <div class="grid grid-2">
      <div class="card"><h3>Cyclone Track &amp; Forecast Map</h3><div id="dash-map"></div>
        <div class="map-legend">
          <span><span class="swatch" style="background:#3aa0ff"></span>Historical track</span>
          <span><span class="swatch" style="background:#f0b93a"></span>Forecast track</span>
          <span><span class="swatch" style="background:rgba(240,185,58,0.25)"></span>Uncertainty cone</span>
          <span><span class="swatch" style="background:#ef5350"></span>Current position</span>
        </div>
      </div>
      <div style="display:flex; flex-direction:column; gap:14px;">
        <div class="card" id="current-system"><h3>Current System</h3>${loadingHtml()}</div>
        <div class="card" id="ai-assessment"><h3>AI Assessment</h3>${loadingHtml()}</div>
      </div>
    </div>
  `;

  const mapEl = document.getElementById("dash-map");
  mapEl.id = "map";

  try {
    const [dash, track, risk] = await Promise.all([api.dashboard(), api.track("DEMO-01"), api.risk("DEMO-01")]);
    renderCurrentSystem(dash);
    renderAiAssessment(dash, risk);
    renderMap(track);
  } catch (e) {
    document.getElementById("current-system").innerHTML = `<h3>Current System</h3>${errorHtml(e)}`;
    document.getElementById("ai-assessment").innerHTML = "";
    mapEl.innerHTML = `<div class="error-state">Map unavailable — backend not reachable.</div>`;
  }
}

function renderCurrentSystem(dash) {
  const c = dash.cyclone;
  const l = c.latest;
  document.getElementById("current-system").innerHTML = `
    <h3>Current System</h3>
    <div class="stat-row"><span class="label">Name</span><span class="value">${c.name}</span></div>
    <div class="stat-row"><span class="label">Classification</span><span class="value">${l.classification.replaceAll("_", " ")}</span></div>
    <div class="stat-row"><span class="label">Position</span><span class="value">${l.lat}°N, ${l.lon}°E</span></div>
    <div class="stat-row"><span class="label">Max sustained wind</span><span class="value">${l.wind_speed_kt} kt</span></div>
    <div class="stat-row"><span class="label">Central pressure</span><span class="value">${l.central_pressure_hpa} hPa</span></div>
    <div class="stat-row"><span class="label">Movement</span><span class="value">${c.movement_direction_deg ?? "—"}°</span></div>
    <div class="stat-row"><span class="label">Confidence</span><span class="value">${(l.classification_confidence * 100).toFixed(0)}%</span></div>
    <div class="stat-row"><span class="label">Last updated</span><span class="value">${fmtTime(c.last_updated)}</span></div>
  `;
}

function renderAiAssessment(dash, risk) {
  document.getElementById("ai-assessment").innerHTML = `
    <h3>AI Assessment</h3>
    <div class="stat-row"><span class="label">Cyclone probability</span><span class="value">${(dash.cyclone.latest.detection_confidence * 100).toFixed(0)}%</span></div>
    <div class="stat-row"><span class="label">Rapid intensification risk</span><span class="value">${dash.trend.rapid_intensification ? "HIGH" : "LOW"}</span></div>
    <div class="stat-row"><span class="label">Landfall probability (72h)</span><span class="value">${(dash.landfall_probability * 100).toFixed(0)}%</span></div>
    <div class="stat-row"><span class="label">Overall risk</span><span class="value"><span class="tag ${risk.risk_category.toLowerCase()}">${risk.risk_category}</span></span></div>
    <div class="stat-row"><span class="label">Active alerts</span><span class="value">${dash.active_alerts}</span></div>
  `;
}

function renderMap(track) {
  const map = L.map("map", { zoomControl: true }).setView([16, 84], 5);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: "&copy; OpenStreetMap contributors &copy; CARTO",
    maxZoom: 10,
  }).addTo(map);

  const histLatLngs = track.history.map((p) => [p.lat, p.lon]);
  L.polyline(histLatLngs, { color: "#3aa0ff", weight: 3 }).addTo(map);

  const last = track.history[track.history.length - 1];
  L.circleMarker([last.lat, last.lon], { radius: 7, color: "#ef5350", fillColor: "#ef5350", fillOpacity: 1 })
    .addTo(map)
    .bindPopup(`Current position<br/>${last.timestamp}`);

  const forecastLatLngs = [[last.lat, last.lon], ...track.forecast.map((f) => [f.lat, f.lon])];
  L.polyline(forecastLatLngs, { color: "#f0b93a", weight: 2, dashArray: "6,6" }).addTo(map);

  track.forecast.forEach((f) => {
    L.circle([f.lat, f.lon], {
      radius: f.uncertainty_radius_km * 1000,
      color: "#f0b93a",
      weight: 1,
      fillColor: "#f0b93a",
      fillOpacity: 0.08,
    }).addTo(map);
    L.circleMarker([f.lat, f.lon], { radius: 4, color: "#f0b93a", fillColor: "#f0b93a", fillOpacity: 1 })
      .addTo(map)
      .bindPopup(`+${f.horizon_hours}h forecast<br/>Uncertainty: ±${f.uncertainty_radius_km}km`);
  });

  const allPts = [...histLatLngs, ...track.forecast.map((f) => [f.lat, f.lon])];
  map.fitBounds(allPts, { padding: [30, 30] });
}
