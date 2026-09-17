export function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

export function loadingHtml(msg = "Loading…") {
  return `<div class="loading">${msg}</div>`;
}

export function errorHtml(err) {
  const msg = err?.message || "Something went wrong.";
  return `<div class="error-state">⚠ Backend unavailable — ${msg}<br/><span style="color:var(--text-2)">Is the backend running on the expected port? See README for setup.</span></div>`;
}

export async function withLoading(container, loader, render) {
  container.innerHTML = loadingHtml();
  try {
    const data = await loader();
    container.innerHTML = "";
    render(data);
  } catch (e) {
    container.innerHTML = errorHtml(e);
  }
}

export function riskTagClass(level) {
  return (level || "").toLowerCase();
}
