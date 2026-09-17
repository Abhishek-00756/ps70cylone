import { api } from "../services/api.js";
import { loadingHtml, errorHtml } from "../utils/dom.js";

export async function renderRisk(container) {
  container.innerHTML = `
    <div class="page-title">Risk &amp; Impact</div>
    <div class="page-subtitle">Disaster-management decision support — <span class="tag demo">Demo exposure/vulnerability layers</span></div>
    <div id="risk-body">${loadingHtml()}</div>
  `;

  try {
    const risk = await api.risk("DEMO-01");
    renderBody(risk);
  } catch (e) {
    document.getElementById("risk-body").innerHTML = errorHtml(e);
  }
}

function renderBody(risk) {
  const el = document.getElementById("risk-body");
  el.innerHTML = `
    <div class="grid grid-4" style="margin-bottom:14px;">
      <div class="card"><div class="big-stat"><span class="tag ${risk.risk_category.toLowerCase()}" style="font-size:16px; padding:6px 12px;">${risk.risk_category}</span></div><div class="big-stat-label">Overall risk category</div></div>
      <div class="card"><div class="big-stat">${risk.overall_risk_score}</div><div class="big-stat-label">Overall risk score</div></div>
      <div class="card"><div class="big-stat">${(risk.landfall_probability*100).toFixed(0)}%</div><div class="big-stat-label">Landfall probability</div></div>
      <div class="card"><div class="big-stat"><span class="tag ${risk.wind_risk.toLowerCase()}">${risk.wind_risk}</span></div><div class="big-stat-label">Wind risk</div></div>
    </div>

    <div class="grid grid-2">
      <div class="card">
        <h3>Hazard Breakdown</h3>
        <div class="stat-row"><span class="label">Wind risk</span><span class="value"><span class="tag ${risk.wind_risk.toLowerCase()}">${risk.wind_risk}</span></span></div>
        <div class="stat-row"><span class="label">Rainfall risk</span><span class="value"><span class="tag ${risk.rainfall_risk.toLowerCase()}">${risk.rainfall_risk}</span></span></div>
        <div class="stat-row"><span class="label">Storm surge risk</span><span class="value"><span class="tag ${risk.storm_surge_risk.toLowerCase()}">${risk.storm_surge_risk}</span></span></div>
      </div>
      <div class="card">
        <h3>Risk Formula (documented, traceable)</h3>
        <p style="font-family:var(--mono); font-size:13px; color:var(--text-0); background:var(--bg-2); padding:10px; border-radius:4px;">
          risk_score = hazard_intensity × exposure × vulnerability<br/>
          ${risk.overall_risk_score} = ${risk.hazard_intensity} × ${risk.exposure} × ${risk.vulnerability}
        </p>
        <div class="stat-row"><span class="label">Hazard intensity</span><span class="value">${risk.hazard_intensity}</span></div>
        <div class="stat-row"><span class="label">Exposure <span class="tag demo" style="margin-left:6px;">DEMO</span></span><span class="value">${risk.exposure}</span></div>
        <div class="stat-row"><span class="label">Vulnerability <span class="tag demo" style="margin-left:6px;">DEMO</span></span><span class="value">${risk.vulnerability}</span></div>
        <p class="footer-note">${risk.demo_layers.exposure}<br/>${risk.demo_layers.vulnerability}</p>
      </div>
    </div>
  `;
}
