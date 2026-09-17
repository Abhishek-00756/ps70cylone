import { renderSidebar } from "./components/sidebar.js";
import { renderTopbar } from "./components/topbar.js";
import { renderDashboard } from "./pages/dashboard.js";
import { renderSatellite } from "./pages/satellite.js";
import { renderDetection } from "./pages/detection.js";
import { renderIntensity } from "./pages/intensity.js";
import { renderTrack } from "./pages/track.js";
import { renderRisk } from "./pages/risk.js";
import { renderAlerts } from "./pages/alerts.js";
import { renderPerformance } from "./pages/performance.js";
import { renderSources } from "./pages/sources.js";

const ROUTES = {
  dashboard: renderDashboard,
  satellite: renderSatellite,
  detection: renderDetection,
  intensity: renderIntensity,
  track: renderTrack,
  risk: renderRisk,
  alerts: renderAlerts,
  performance: renderPerformance,
  sources: renderSources,
};

function currentRoute() {
  const hash = window.location.hash.replace(/^#\//, "");
  return ROUTES[hash] ? hash : "dashboard";
}

async function render() {
  const route = currentRoute();
  renderSidebar(route);
  await renderTopbar();
  const content = document.getElementById("content");
  await ROUTES[route](content);
}

window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", render);
