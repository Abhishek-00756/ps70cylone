import { api } from "../services/api.js";
import { loadingHtml, errorHtml } from "../utils/dom.js";

export async function renderTrack(container) {
  container.innerHTML = `
    <div class="page-title">Track Prediction</div>
    <div class="page-subtitle">Prototype Forecast Model — <span class="tag demo">Not operational NWP</span></div>
    <div class="grid grid-2">
      <div class="card">
        <h3>Forecast Map</h3>
        <div class="btn-group" style="margin-bottom:10px;">
          <button class="btn small" data-h="24">24h</button>
          <button class="btn small secondary" data-h="48">48h</button>
          <button class="btn small secondary" data-h="72">72h</button>
        </div>
        <div id="track-map"></div>
      </div>
      <div style="display:flex; flex-direction:column; gap:14px;">
        <div class="card" id="landfall-card"><h3>Landfall Estimate</h3>${loadingHtml()}</div>
        <div class="card" id="forecast-table-card"><h3>Forecast Points</h3>${loadingHtml()}</div>
      </div>
    </div>
  `;

  let trackData;
  try {
    trackData = await api.track("DEMO-01");
  } catch (e) {
    document.getElementById("track-map").innerHTML = "";
    document.getElementById("landfall-card").innerHTML = `<h3>Landfall Estimate</h3>${errorHtml(e)}`;
    document.getElementById("forecast-table-card").innerHTML = "";
    return;
  }

  document.getElementById("track-map").id = "map2";
  let horizonLimit = 24;
  const map = L.map("map2").setView([16, 84], 5);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", { attribution: "&copy; OpenStreetMap &copy; CARTO", maxZoom: 10 }).addTo(map);

  let layerGroup = L.layerGroup().addTo(map);

  function draw() {
    layerGroup.clearLayers();
    const hist = trackData.history.map((p) => [p.lat, p.lon]);
    L.polyline(hist, { color: "#3aa0ff", weight: 3 }).addTo(layerGroup);
    const last = trackData.history[trackData.history.length - 1];
    L.circleMarker([last.lat, last.lon], { radius: 7, color: "#ef5350", fillColor: "#ef5350", fillOpacity: 1 }).addTo(layerGroup);

    const shown = trackData.forecast.filter((f) => f.horizon_hours <= horizonLimit);
    const fLine = [[last.lat, last.lon], ...shown.map((f) => [f.lat, f.lon])];
    L.polyline(fLine, { color: "#f0b93a", weight: 2, dashArray: "6,6" }).addTo(layerGroup);
    shown.forEach((f) => {
      L.circle([f.lat, f.lon], { radius: f.uncertainty_radius_km * 1000, color: "#f0b93a", weight: 1, fillColor: "#f0b93a", fillOpacity: 0.08 }).addTo(layerGroup);
      L.circleMarker([f.lat, f.lon], { radius: 4, color: "#f0b93a", fillColor: "#f0b93a", fillOpacity: 1 }).addTo(layerGroup).bindPopup(`+${f.horizon_hours}h · ±${f.uncertainty_radius_km}km`);
    });
    const bounds = [...hist, ...shown.map((f) => [f.lat, f.lon])];
    map.fitBounds(bounds, { padding: [30, 30] });

    renderLandfall(shown[shown.length - 1]);
    renderForecastTable(shown);
  }

  document.querySelectorAll("[data-h]").forEach((btn) => {
    btn.addEventListener("click", () => {
      horizonLimit = parseInt(btn.dataset.h, 10);
      document.querySelectorAll("[data-h]").forEach((b) => b.classList.add("secondary"));
      btn.classList.remove("secondary");
      draw();
    });
  });

  draw();
}

function renderLandfall(point) {
  const el = document.getElementById("landfall-card");
  if (!point) {
    el.innerHTML = `<h3>Landfall Estimate</h3><div class="empty-state">No forecast point in selected window.</div>`;
    return;
  }
  el.innerHTML = `
    <h3>Landfall Estimate</h3>
    <div class="stat-row"><span class="label">Predicted region (lat/lon)</span><span class="value">${point.lat}°N, ${point.lon}°E</span></div>
    <div class="stat-row"><span class="label">Estimated time</span><span class="value">${new Date(point.timestamp).toLocaleString()}</span></div>
    <div class="stat-row"><span class="label">Forecast horizon</span><span class="value">+${point.horizon_hours}h</span></div>
    <div class="stat-row"><span class="label">Uncertainty radius</span><span class="value">±${point.uncertainty_radius_km} km</span></div>
    <p class="footer-note">Uncertainty grows with horizon per the documented prototype model (see <code>ml/tracking/track_generator.py</code>). This is not the IMD's official cone of uncertainty.</p>
  `;
}

function renderForecastTable(points) {
  const el = document.getElementById("forecast-table-card");
  if (!points.length) {
    el.innerHTML = `<h3>Forecast Points</h3><div class="empty-state">No points in window.</div>`;
    return;
  }
  el.innerHTML = `<h3>Forecast Points</h3>
    <table class="plain">
      <tr><th>Horizon</th><th>Lat</th><th>Lon</th><th>Uncertainty</th></tr>
      ${points.map((p) => `<tr><td>+${p.horizon_hours}h</td><td>${p.lat}</td><td>${p.lon}</td><td>±${p.uncertainty_radius_km}km</td></tr>`).join("")}
    </table>`;
}
