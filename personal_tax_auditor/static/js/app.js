/* ─── KarMitra – app.js ─── */

// ── Utilities ──────────────────────────────────────────────────
const fmt = (n, decimals = 0) => {
  if (n === null || n === undefined) return '—';
  return Number(n).toLocaleString('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
};
const fmtNPR = (n) => `NPR ${fmt(n)}`;
const currentYear = () => new Date().getFullYear();
const currentMonth = () => new Date().getMonth() + 1;

async function api(path, method = 'GET', body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch('/api' + path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'API error');
  return data;
}

// ── Toast ───────────────────────────────────────────────────────
(function () {
  let container = null;
  window.toast = function (msg, type = 'success') {
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    const el = document.createElement('div');
    const icon = type === 'success' ? 'fa-circle-check' : 'fa-circle-xmark';
    el.className = `toast-item ${type}`;
    el.innerHTML = `<i class="fa-solid ${icon}"></i> ${msg}`;
    container.appendChild(el);
    setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity 0.3s'; setTimeout(() => el.remove(), 300); }, 3000);
  };
})();

// ── Chart.js defaults ──────────────────────────────────────────
if (typeof Chart !== 'undefined') {
  Chart.defaults.color = '#6b7280';
  Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
  Chart.defaults.font.family = "'Sora', sans-serif";
  Chart.defaults.font.size = 11;
}

// ── VAT calculator helper (reusable) ───────────────────────────
window.extractVAT = (amount) => {
  const vat = amount * 13 / 113;
  return { vat: vat.toFixed(2), base: (amount - vat).toFixed(2) };
};
