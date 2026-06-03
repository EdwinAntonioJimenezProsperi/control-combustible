// Helpers compartidos para llamadas a la API.
async function api(url, method = "GET", body = null) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Error ${res.status}`);
  }
  return data;
}

function showError(box, err) {
  box.hidden = false;
  box.className = "result err";
  box.textContent = err.message || String(err);
}
