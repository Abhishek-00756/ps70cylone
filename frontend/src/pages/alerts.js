import { api, fmtTime } from "../services/api.js";
import { loadingHtml, errorHtml } from "../utils/dom.js";

export async function renderAlerts(container) {
  container.innerHTML = `
    <div class="page-title">Alert Center</div>
    <div class="page-subtitle">Rule-based alerts generated from live model outputs</div>
    <div id="alerts-body">${loadingHtml()}</div>
  `;

  try {
    const { alerts } = await api.alerts();
    renderBody(alerts);
  } catch (e) {
    document.getElementById("alerts-body").innerHTML = errorHtml(e);
  }
}

function renderBody(alerts) {
  const el = document.getElementById("alerts-body");
  if (!alerts.length) {
    el.innerHTML = `<div class="empty-state">No active alerts for the current demo scenario.</div>`;
    return;
  }
  el.innerHTML = alerts
    .map(
      (a) => `
    <div class="alert-card ${a.severity}">
      <div class="head">
        <strong>${a.type.replaceAll("_"," ")}</strong>
        <span class="tag ${a.severity.toLowerCase()}">${a.severity}</span>
      </div>
      <div class="reason">${a.reason}</div>
      <div class="stat-row"><span class="label">Affected region</span><span class="value" style="font-weight:400;">${a.affected_region}</span></div>
      <div class="stat-row"><span class="label">Recommended action</span><span class="value" style="font-weight:400;">${a.recommended_action}</span></div>
      <div class="meta">Confidence: ${(a.confidence*100).toFixed(0)}% · ${fmtTime(a.timestamp)}</div>
    </div>`
    )
    .join("");
}
