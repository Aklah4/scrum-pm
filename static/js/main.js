// ── Phase cycle (overview) ───────────────────────────────
const STATES = ["todo", "active", "done"];

function cyclePhase(btn) {
  const cur = STATES.findIndex(s => btn.classList.contains(s));
  const next = STATES[(cur + 1) % STATES.length];
  STATES.forEach(s => btn.classList.remove(s));
  btn.classList.add(next);
  document.getElementById("state_" + btn.dataset.label).value = next;
  updatePhaseProgress();
}

function updatePhaseProgress() {
  const pills   = document.querySelectorAll(".phase");
  const total   = pills.length;
  const done    = [...pills].filter(p => p.classList.contains("done")).length;
  const pct     = total ? Math.round((done / total) * 100) : 0;

  const bar     = document.querySelector(".progress-bar");
  const pctEl   = document.querySelector(".progress-meta .pct");

  if (bar)   bar.style.width = pct + "%";
  if (pctEl) pctEl.textContent = pct + "%";
}

// ── New story / new item button ──────────────────────────
function focusAddForm(inputId) {
  const el = document.getElementById(inputId);
  if (!el) return;
  el.scrollIntoView({ behavior: "smooth", block: "center" });
  el.focus();
  el.closest("form").classList.add("form-highlight");
  setTimeout(() => el.closest("form").classList.remove("form-highlight"), 1200);
}

// ── Dark mode ────────────────────────────────────────────
function applyTheme(dark) {
  document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.textContent = dark ? "☀ Light" : "☾ Dark";
}

function toggleTheme() {
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  localStorage.setItem("theme", isDark ? "light" : "dark");
  applyTheme(!isDark);
}

// Sync button label after DOM is ready (theme itself is set in <head>)
document.addEventListener("DOMContentLoaded", function () {
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.textContent = isDark ? "☀ Light" : "☾ Dark";
});
