"""Light theme and small HTML helpers for the Streamlit app."""

from html import escape
from typing import List

import streamlit as st


CSS = """
<style>
:root {
  --bg: #f7f9fc;
  --surface: #ffffff;
  --surface-soft: #f2f6fb;
  --surface-warm: #fff7ed;
  --primary: #f59e0b;
  --primary-strong: #d97706;
  --accent: #2563eb;
  --text: #111827;
  --muted: #667085;
  --border: #d9e2ec;
  --success: #16803c;
  --warning: #b45309;
  --danger: #b42318;
  --shadow: 0 14px 34px rgba(16, 24, 40, 0.07);
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text) !important;
}

html, body, [class*="css"], p, span, label, div {
  color: var(--text);
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  letter-spacing: 0;
}

[data-testid="stHeader"] {
  background: rgba(247, 249, 252, 0.96) !important;
  border-bottom: 1px solid var(--border);
  box-shadow: 0 1px 0 rgba(16, 24, 40, 0.03);
}

[data-testid="stStatusWidget"],
[data-testid="stSpinner"] {
  display: none !important;
}

.block-container {
  max-width: 1420px;
  padding-top: 1rem;
  padding-bottom: 1.4rem;
}

section[data-testid="stSidebar"] {
  background: #ffffff !important;
  border-right: 1px solid var(--border);
  box-shadow: 8px 0 24px rgba(16, 24, 40, 0.035);
}

section[data-testid="stSidebar"] > div {
  overflow-y: auto !important;
  overflow-x: hidden !important;
  max-height: 100vh !important;
  padding: 0rem 1rem !important;
}

.css-10oheav {
  padding: 0rem 1rem !important;
}

section[data-testid="stSidebar"] * {
  color: var(--text) !important;
}

section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
  color: var(--text) !important;
}

.app-title {
  font-size: 18px;
  font-weight: 800;
  text-align: center;
  color: var(--text);
  margin-top: 0;
}

.app-subtitle {
  color: var(--muted);
  font-size: 11px;
  text-align: center;
  margin-top: 3px;
}

.sidebar-brand {
  padding: 4px 4px 10px;
}

.sidebar-logo-wrap {
  display: flex;
  justify-content: center;
  padding: 2px 0 8px;
}

.sidebar-logo {
  width: 116px;
  height: 116px;
  object-fit: cover;
  border-radius: 999px;
  border: 1px solid #edf2f7;
  box-shadow: 0 10px 26px rgba(16, 24, 40, 0.08);
}

.sidebar-section {
  padding: 4px 0 2px;
}

.sidebar-section-title {
  color: var(--text) !important;
  font-size: 13px !important;
  font-weight: 500;
  letter-spacing: 0;
  text-transform: none;
  margin-bottom: 10px;
}

.sidebar-footer {
  color: var(--muted);
  font-size: 12px;
  padding: 6px 2px 0;
}

.header-row {
  margin: 0 0 14px;
  padding: 6px 2px 10px;
  background: transparent;
  border: 0;
}

.header-title {
  font-size: 30px;
  line-height: 1.1;
  font-weight: 820;
  margin: 0;
  color: var(--text);
}

.header-subtitle {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 14px;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 18px;
  box-shadow: var(--shadow);
}

.section-title {
  font-size: 16px;
  line-height: 1.25;
  margin: 0 0 14px;
  font-weight: 780;
  color: var(--text);
}

.kpi-card {
  min-height: 116px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.kpi-number {
  color: var(--text);
  font-size: 34px;
  font-weight: 820;
  line-height: 1;
}

.kpi-label {
  color: var(--muted);
  font-size: 13px;
  margin-top: 10px;
}

.kpi-help {
  color: var(--muted);
  font-size: 12px;
  margin-top: 9px;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  background: var(--surface-soft);
  color: var(--text);
  border: 1px solid var(--border);
  white-space: nowrap;
}

.badge.success { color: var(--success); background: #ecfdf3; border-color: #abefc6; }
.badge.warning { color: var(--warning); background: #fffaeb; border-color: #fedf89; }
.badge.danger { color: var(--danger); background: #fef3f2; border-color: #fecdca; }
.badge.accent { color: var(--accent); background: #eff6ff; border-color: #bfdbfe; }

.chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 7px;
  font-size: 11px;
  color: var(--muted);
  background: var(--surface-soft);
  border: 1px solid var(--border);
  margin: 6px 6px 0 0;
}

.challenge-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 10px;
  box-shadow: 0 6px 18px rgba(16, 24, 40, 0.045);
}

.challenge-title {
  font-size: 14px;
  font-weight: 760;
  color: var(--text);
  margin-bottom: 4px;
}

.muted {
  color: var(--muted) !important;
}

[data-testid="stMetric"] {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  box-shadow: 0 8px 22px rgba(16, 24, 40, 0.055);
}

[data-testid="stMetric"] label,
[data-testid="stMetric"] [data-testid="stMetricLabel"] {
  color: var(--muted) !important;
}

[data-testid="stMetricValue"] {
  color: var(--text) !important;
}

.stButton > button {
  min-height: 38px;
  border-radius: 9px;
  border: 1px solid #e08a00;
  background: #f5a524;
  color: #111827 !important;
  font-weight: 760;
  box-shadow: 0 8px 18px rgba(245, 158, 11, 0.22);
}

.stButton > button:hover {
  border-color: var(--primary-strong);
  background: #f0a020;
  color: #111827 !important;
}

input, textarea, select {
  color: var(--text) !important;
  background: #ffffff !important;
}

section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
  gap: 0.42rem;
}

section[data-testid="stSidebar"] hr {
  margin: 0.55rem 0 !important;
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p {
  font-size: 14px !important;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label {
  min-height: 32px !important;
  padding: 1px 0 !important;
  border-radius: 8px;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
  background: #f7f9fc !important;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label p {
  font-size: 14px !important;
}

section[data-testid="stSidebar"] [data-testid="stSelectbox"] {
  margin-bottom: 0 !important;
}

section[data-testid="stSidebar"] [data-testid="stSelectbox"] > div {
  min-height: 42px !important;
}

section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
  font-size: 12px !important;
  color: var(--muted) !important;
}

.app-loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 999999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(247, 249, 252, 0.62);
  backdrop-filter: blur(5px) saturate(1.08);
  -webkit-backdrop-filter: blur(5px) saturate(1.08);
}

.app-loading-panel {
  width: min(420px, calc(100vw - 40px));
  padding: 28px 30px;
  border-radius: 16px;
  border: 1px solid rgba(217, 226, 236, 0.9);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 24px 70px rgba(16, 24, 40, 0.18);
  text-align: center;
}

.app-loading-spinner {
  width: 54px;
  height: 54px;
  margin: 0 auto 18px;
  border-radius: 999px;
  border: 6px solid #e4eaf2;
  border-top-color: var(--primary);
  border-right-color: var(--accent);
  animation: app-spin 0.85s linear infinite;
}

.app-loading-title {
  font-size: 20px;
  font-weight: 800;
  color: var(--text);
}

.app-loading-subtitle {
  margin-top: 7px;
  color: var(--muted);
  font-size: 13px;
}

.bar-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bar-row {
  display: grid;
  grid-template-columns: minmax(130px, 240px) 1fr auto;
  gap: 12px;
  align-items: center;
}

.bar-label {
  color: var(--text);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-track {
  height: 10px;
  border-radius: 999px;
  background: #e8eef6;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #f59e0b, #2563eb);
}

.bar-value {
  color: var(--muted);
  font-size: 12px;
  min-width: 52px;
  text-align: right;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
}

.summary-item {
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #fbfcff;
}

.summary-value {
  font-size: 24px;
  font-weight: 820;
  color: var(--text);
  line-height: 1;
}

.summary-label {
  margin-top: 8px;
  color: var(--muted);
  font-size: 12px;
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rank-item {
  display: grid;
  grid-template-columns: 34px 1fr auto;
  gap: 12px;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}

.rank-item:last-child {
  border-bottom: 0;
}

.rank-number {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-soft);
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.rank-title {
  color: var(--text);
  font-size: 13px;
  font-weight: 720;
  line-height: 1.25;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.rank-meta {
  margin-top: 4px;
  color: var(--muted);
  font-size: 11px;
}

.rank-value {
  color: var(--text);
  font-size: 16px;
  font-weight: 800;
  text-align: right;
  white-space: nowrap;
}

@keyframes app-spin {
  to { transform: rotate(360deg); }
}

[data-testid="stProgress"] > div > div > div > div {
  background: linear-gradient(90deg, #f59e0b, #2563eb) !important;
}

[data-testid="stProgress"] > div > div {
  background: #e5eaf1 !important;
}

div[data-testid="stDataFrame"],
div[data-testid="stTable"] {
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
}

code {
  background: #f2f4f7 !important;
  color: #175cd3 !important;
  border-radius: 6px;
}

hr {
  border-color: var(--border) !important;
}
</style>
"""


def inject_theme():
    st.markdown(CSS, unsafe_allow_html=True)


def render_header(title: str, subtitle: str = ""):
    subtitle_html = f"<p class='header-subtitle'>{escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class='header-row'>
            <h1 class='header-title'>{escape(title)}</h1>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(number: str, label: str, color: str = "text", help_text: str = "") -> str:
    color_var = f"var(--{color})" if color != "text" else "var(--text)"
    help_html = f"<div class='kpi-help'>{escape(help_text)}</div>" if help_text else ""
    return f"""
    <div class='card kpi-card'>
        <div class='kpi-number' style='color:{color_var}'>{escape(str(number))}</div>
        <div class='kpi-label'>{escape(label)}</div>
        {help_html}
    </div>
    """


def render_status_badge(status: str) -> str:
    labels = {
        "not_started": ("Nao iniciado", ""),
        "in_progress": ("Em andamento", "accent"),
        "done": ("Concluido", "success"),
        "review": ("Revisar", "warning"),
    }
    label, cls = labels.get(status, ("Nao iniciado", ""))
    return f"<span class='badge {cls}'>{label}</span>"


def render_challenge_card(
    title: str,
    tags: List[str],
    difficulty: int,
    avg_time: int,
    services: List[str] = None,
    status: str = "not_started",
    personal_difficulty: int = 0,
    time_spent: int = 0,
) -> str:
    services = services or []
    tags_html = "".join(f"<span class='chip'>{escape(str(t))}</span>" for t in tags[:5])
    services_html = "".join(f"<span class='chip'>{escape(str(s))}</span>" for s in services[:4])
    status_html = render_status_badge(status)
    subtitle = f"Nivel AWS {difficulty or 0} | Medio global {avg_time or 0}s"
    if personal_difficulty or time_spent:
        subtitle += f" | Seu nivel {personal_difficulty or 0} | {time_spent or 0}min"

    return f"""
    <div class='challenge-card'>
        <div style='display:flex;justify-content:space-between;gap:12px;align-items:flex-start'>
            <div style='min-width:0'>
                <div class='challenge-title'>{escape(str(title or "Sem titulo"))}</div>
                <div class='muted' style='font-size:12px'>{escape(subtitle)}</div>
                <div>{tags_html}{services_html}</div>
            </div>
            <div>{status_html}</div>
        </div>
    </div>
    """
