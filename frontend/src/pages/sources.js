import { api } from "../services/api.js";
import { loadingHtml, errorHtml } from "../utils/dom.js";

export async function renderSources(container) {
  container.innerHTML = `
    <div class="page-title">Data Sources</div>
    <div class="page-subtitle">Multi-source architecture — connector status is reported honestly, not simulated as live</div>
    <div id="sources-body">${loadingHtml()}</div>
  `;

  try {
    const { sources } = await api.dataSources();
    renderBody(sources);
  } catch (e) {
    document.getElementById("sources-body").innerHTML = errorHtml(e);
  }
}

function renderBody(sources) {
  const el = document.getElementById("sources-body");
  el.innerHTML = `
    <div class="card">
      <table class="plain">
        <tr><th>Source</th><th>Status</th><th>Data Type</th><th>Purpose</th></tr>
        ${sources
          .map(
            (s) => `<tr>
              <td>${s.name}</td>
              <td><span class="tag ${s.status === "CONNECTED" ? "low" : s.status === "DEMO" ? "demo" : "severe"}">${s.status}</span></td>
              <td>${s.data_type}</td>
              <td style="color:var(--text-1)">${s.purpose}</td>
            </tr>`
          )
          .join("")}
      </table>
    </div>
    <div class="card" style="margin-top:14px;">
      <h3>Intended Multi-Source Architecture</h3>
      <p style="font-size:12.5px; color:var(--text-1); line-height:1.7;">
        The provider layer (<code>backend/app/providers/</code>) defines a common <code>SatelliteDataProvider</code>
        interface. In this prototype only the synthetic demo provider is implemented and active. IMD and MOSDAC
        providers exist as documented placeholders so real INSAT/MOSDAC imagery, SST, OLR, QPE, Cloud Motion Vectors,
        and historical cyclone-track feeds can be wired in later without changing any other part of the application.
      </p>
    </div>
  `;
}
