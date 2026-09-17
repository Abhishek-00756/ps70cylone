import { api, fmtTime } from "../services/api.js";
import { loadingHtml, errorHtml } from "../utils/dom.js";

export async function renderIntensity(container) {
  container.innerHTML = `
    <div class="page-title">Intensity Estimation</div>
    <div class="page-subtitle">Prototype Dvorak-inspired formula — <span class="tag demo">Not operationally calibrated</span></div>
    <div id="intensity-body">${loadingHtml()}</div>
  `;

  try {
    const data = await api.intensity("DEMO-01");
    renderBody(data);
  } catch (e) {
    document.getElementById("intensity-body").innerHTML = errorHtml(e);
  }
}

function renderBody(data) {
  const latest = data.series[data.series.length - 1];
  const el = document.getElementById("intensity-body");
  el.innerHTML = `
    <div class="grid grid-4" style="margin-bottom:14px;">
      <div class="card"><div class="big-stat">${latest.wind_speed_kt}</div><div class="big-stat-label">Max wind (kt)</div></div>
      <div class="card"><div class="big-stat">${latest.central_pressure_hpa}</div><div class="big-stat-label">Central pressure (hPa)</div></div>
      <div class="card"><div class="big-stat" style="font-size:20px;">${latest.classification.replaceAll("_"," ")}</div><div class="big-stat-label">Classification</div></div>
      <div class="card"><div class="big-stat" style="color:${data.rapid_intensification ? "var(--bad)" : "var(--good)"}">${data.rapid_intensification ? "HIGH" : "LOW"}</div><div class="big-stat-label">Rapid intensification risk</div></div>
    </div>

    <div class="grid grid-2">
      <div class="card"><h3>Wind Speed (kt) — Time Series</h3><div class="chart-wrap"><canvas id="wind-chart"></canvas></div></div>
      <div class="card"><h3>Central Pressure (hPa) — Time Series</h3><div class="chart-wrap"><canvas id="pressure-chart"></canvas></div></div>
    </div>

    <div class="card" style="margin-top:14px;">
      <h3>Rapid Intensification (RI)</h3>
      <p style="font-size:12.5px; color:var(--text-1); line-height:1.6;">
        <strong>Definition used:</strong> a wind-speed increase of ≥ ${data.ri_threshold_kt_per_24h} kt over the analysed ~24h window
        (the same threshold magnitude used operationally, e.g. by NHC, for RI classification).
      </p>
      <div class="stat-row"><span class="label">Δ Wind speed (window)</span><span class="value">${data.delta_wind_kt_24h > 0 ? "+" : ""}${data.delta_wind_kt_24h} kt</span></div>
      <div class="stat-row"><span class="label">Δ Central pressure (window)</span><span class="value">${data.delta_pressure_hpa_24h} hPa</span></div>
      <div class="stat-row"><span class="label">Current trend</span><span class="value">${data.trend.toUpperCase()}</span></div>
      <div class="stat-row"><span class="label">RI flagged</span><span class="value">${data.rapid_intensification ? "YES" : "NO"}</span></div>
    </div>
  `;

  const labels = data.series.map((s) => fmtTime(s.timestamp));
  new Chart(document.getElementById("wind-chart"), {
    type: "line",
    data: { labels, datasets: [{ label: "Wind (kt)", data: data.series.map((s) => s.wind_speed_kt), borderColor: "#3aa0ff", backgroundColor: "rgba(58,160,255,0.15)", fill: true, tension: 0.3 }] },
    options: chartOptions(),
  });
  new Chart(document.getElementById("pressure-chart"), {
    type: "line",
    data: { labels, datasets: [{ label: "Pressure (hPa)", data: data.series.map((s) => s.central_pressure_hpa), borderColor: "#f0b93a", backgroundColor: "rgba(240,185,58,0.15)", fill: true, tension: 0.3 }] },
    options: chartOptions(),
  });
}

function chartOptions() {
  return {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: "#9aa8bd", font: { size: 10 } }, grid: { color: "#263041" } },
      y: { ticks: { color: "#9aa8bd", font: { size: 10 } }, grid: { color: "#263041" } },
    },
  };
}
