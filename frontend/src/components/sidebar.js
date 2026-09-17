const NAV = [
  { section: "Monitor" },
  { id: "dashboard", label: "Dashboard", icon: "◈" },
  { id: "satellite", label: "Satellite Analysis", icon: "☁" },
  { id: "detection", label: "AI Detection", icon: "◎" },
  { id: "intensity", label: "Intensity", icon: "≋" },
  { id: "track", label: "Track Forecast", icon: "➤" },
  { section: "Decision Support" },
  { id: "risk", label: "Risk & Impact", icon: "▲" },
  { id: "alerts", label: "Alerts", icon: "⚠" },
  { section: "System" },
  { id: "performance", label: "Model Performance", icon: "▤" },
  { id: "sources", label: "Data Sources", icon: "⟐" },
];

export function renderSidebar(activeRoute) {
  const el = document.getElementById("sidebar");
  const items = NAV.map((item) => {
    if (item.section) return `<div class="nav-section-label">${item.section}</div>`;
    const active = item.id === activeRoute ? "active" : "";
    return `<a class="nav-item ${active}" href="#/${item.id}"><span>${item.icon}</span><span class="label">${item.label}</span></a>`;
  }).join("");

  el.innerHTML = `
    <div class="brand">
      <div class="name">CycloneAI</div>
      <div class="sub">AI-Powered Tropical Cyclone Intelligence &amp; Early Warning System</div>
    </div>
    <nav>${items}</nav>
    <div style="margin-top:auto; padding: 12px 16px; color: var(--text-2); font-size: 10.5px;">
      SIH 2026 · PS 26070 · MoES / IMD<br/>Prototype — not operationally certified
    </div>
  `;
}
