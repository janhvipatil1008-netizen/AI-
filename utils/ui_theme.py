"""
ui_theme.py — Glassmorphism Dark theme for the AI² Streamlit app.

Call inject_css() at the top of every page (after st.set_page_config).
"""

import streamlit as st

_CSS = """
<style>
/* ── FONTS ── */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600;700&display=swap');

/* ── BASE — deep gradient background ── */
html, body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #080A12 0%, #10091E 100%) !important;
    background-attachment: fixed !important;
    color: #CDD6F4 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    line-height: 1.65 !important;
}
[data-testid="stMain"] {
    background: transparent !important;
    color: #CDD6F4 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.025) !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] li {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    color: #BAC2DE !important;
    line-height: 1.5 !important;
}
[data-testid="stSidebar"] label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    color: #BAC2DE !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    color: #CDD6F4 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
[data-testid="stSidebarNavLink"] {
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
}
[data-testid="stSidebarNavLink"]:hover {
    background: rgba(137, 220, 235, 0.08) !important;
}
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
}

/* ── TYPOGRAPHY ── */
h1 {
    font-family: 'Inter', sans-serif !important;
    font-size: 22px !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em !important;
    color: #CDD6F4 !important;
    border-bottom: 1px solid rgba(255,255,255,0.08) !important;
    padding-bottom: 12px !important;
    margin-bottom: 16px !important;
}

h2 {
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #BAC2DE !important;
    letter-spacing: 0.01em !important;
    margin-top: 20px !important;
}

h3 {
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #A6ADC8 !important;
}

p, li {
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    line-height: 1.7 !important;
    color: #CDD6F4 !important;
}

[data-testid="stMain"] label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    color: #BAC2DE !important;
}

small,
[data-testid="stCaptionContainer"] p,
.stCaption {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    color: #585B70 !important;
    line-height: 1.5 !important;
}

/* ── DIVIDER ── */
hr {
    border: none !important;
    border-top: 1px solid rgba(255,255,255,0.08) !important;
    margin: 16px 0 !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    color: #BAC2DE !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    padding: 7px 14px !important;
    transition: border-color 0.2s, color 0.2s, box-shadow 0.2s, background 0.2s !important;
}
.stButton > button:hover {
    border-color: rgba(137,220,235,0.5) !important;
    color: #89DCEB !important;
    background: rgba(137,220,235,0.07) !important;
    box-shadow: 0 0 14px rgba(137,220,235,0.15) !important;
}
.stButton > button:active {
    background: rgba(137,220,235,0.14) !important;
}

/* ── CHAT MESSAGES ── */
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-left: 3px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    padding: 14px 18px !important;
    margin-bottom: 10px !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    gap: 14px !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    border-left-color: #89DCEB !important;
}
[data-testid="stChatMessageAvatarUser"] span,
[data-testid="stChatMessageAvatarAssistant"] span {
    font-size: 0 !important;
}
[data-testid="stChatMessage"] p {
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    line-height: 1.7 !important;
    color: #CDD6F4 !important;
}

/* ── CHAT INPUT ── */
[data-testid="stChatInputContainer"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    padding: 8px 14px !important;
    backdrop-filter: blur(16px) !important;
}
[data-testid="stChatInputContainer"] textarea {
    background: transparent !important;
    color: #CDD6F4 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    border: none !important;
    outline: none !important;
}
[data-testid="stChatInputContainer"] textarea::placeholder {
    color: #45475A !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
}
[data-testid="stChatInputContainer"] button {
    background: rgba(137,220,235,0.1) !important;
    border: 1px solid rgba(137,220,235,0.3) !important;
    border-radius: 8px !important;
    color: #89DCEB !important;
}
[data-testid="stChatInputContainer"] button:hover {
    background: rgba(137,220,235,0.18) !important;
    box-shadow: 0 0 10px rgba(137,220,235,0.2) !important;
}

/* ── TEXT / SELECT INPUTS ── */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    color: #CDD6F4 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: rgba(137,220,235,0.6) !important;
    box-shadow: 0 0 0 2px rgba(137,220,235,0.12) !important;
    outline: none !important;
}
.stSelectbox > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    color: #CDD6F4 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
}

/* ── RADIO ── */
.stRadio label p {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    color: #BAC2DE !important;
    line-height: 1.5 !important;
}

/* ── CHECKBOX ── */
.stCheckbox label p {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    color: #BAC2DE !important;
}

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 10px !important;
    backdrop-filter: blur(12px) !important;
}
[data-testid="stExpander"] summary p {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    color: #BAC2DE !important;
    letter-spacing: 0.04em !important;
}
[data-testid="stExpander"] summary:hover p {
    color: #89DCEB !important;
}

/* ── METRIC ── */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 12px !important;
    padding: 16px 18px !important;
    backdrop-filter: blur(16px) !important;
}
[data-testid="stMetricLabel"] p {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    color: #585B70 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 26px !important;
    font-weight: 700 !important;
    color: #CDD6F4 !important;
}

/* ── ALERT BOXES ── */
[data-testid="stInfo"] {
    background: rgba(137,220,235,0.05) !important;
    border: 1px solid rgba(137,220,235,0.2) !important;
    border-left: 3px solid #89DCEB !important;
    border-radius: 10px !important;
    font-size: 14px !important;
}
[data-testid="stSuccess"] {
    background: rgba(166,227,161,0.05) !important;
    border: 1px solid rgba(166,227,161,0.2) !important;
    border-left: 3px solid #A6E3A1 !important;
    border-radius: 10px !important;
    font-size: 14px !important;
}
[data-testid="stWarning"] {
    background: rgba(249,226,175,0.05) !important;
    border: 1px solid rgba(249,226,175,0.2) !important;
    border-left: 3px solid #F9E2AF !important;
    border-radius: 10px !important;
    font-size: 14px !important;
}
[data-testid="stError"] {
    background: rgba(243,139,168,0.05) !important;
    border: 1px solid rgba(243,139,168,0.2) !important;
    border-left: 3px solid #F38BA8 !important;
    border-radius: 10px !important;
    font-size: 14px !important;
}

/* ── CODE BLOCKS ── */
pre {
    background: rgba(30,32,48,0.8) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-left: 3px solid #A6E3A1 !important;
    border-radius: 10px !important;
    padding: 14px 18px !important;
    font-size: 13px !important;
}
code {
    background: rgba(30,32,48,0.7) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 6px !important;
    color: #A6E3A1 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    padding: 2px 6px !important;
}

/* ── SPINNER ── */
[data-testid="stSpinner"] svg circle {
    stroke: #89DCEB !important;
}

/* ── PROGRESS BAR ── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #89DCEB, #A78BFA) !important;
    border-radius: 99px !important;
}
.stProgress > div > div > div {
    background: rgba(255,255,255,0.08) !important;
    border-radius: 99px !important;
}

/* ── TABS ── */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid rgba(255,255,255,0.08) !important;
    gap: 0 !important;
    background: transparent !important;
}
[data-testid="stTabs"] [role="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    color: #585B70 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    padding: 8px 18px !important;
    transition: color 0.15s !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #89DCEB !important;
    border-bottom-color: #89DCEB !important;
}
[data-testid="stTabs"] [role="tab"]:hover {
    color: #BAC2DE !important;
}

/* ── COLUMNS — remove divider (handled per-context) ── */
[data-testid="column"] + [data-testid="column"] {
    border-left: none;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

/* ── HIDE STREAMLIT CHROME ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stStatusWidget"] { display: none; }
</style>
"""


_WELCOME_CSS = """
<style>
/* ── WELCOME PAGE ── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"] { display: none !important; }

.welcome-root [data-testid="stMain"] > div { padding-top: 0 !important; }

/* Typing cursor */
@keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0; }
}
.cursor { animation: blink 1s step-end infinite; color: #89DCEB; }

/* Feature bullets */
.feature-bullet {
    display: flex; align-items: flex-start; gap: 14px;
    margin-bottom: 18px;
}
.feature-icon {
    font-size: 20px; min-width: 30px; margin-top: 2px;
}
.feature-text {
    font-family: 'Inter', sans-serif; font-size: 14px;
    color: #A6ADC8; line-height: 1.6;
}
.feature-text strong { color: #CDD6F4; }

/* Login card — frosted glass */
.login-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 16px;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    padding: 36px 32px;
}
.login-card h3 {
    font-family: 'Inter', sans-serif !important;
    font-size: 18px !important; font-weight: 700 !important;
    color: #CDD6F4 !important;
    margin-bottom: 6px !important;
}
.login-card h3::before { content: none !important; }
.login-card-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; color: #45475A;
    margin-bottom: 24px; letter-spacing: 0.04em;
}

/* Skill picker buttons */
.skill-picker .stButton button {
    min-height: 90px !important;
    flex-direction: column !important;
    white-space: pre-wrap !important;
    text-align: center !important;
    font-size: 12px !important;
    line-height: 1.5 !important;
    padding: 12px 8px !important;
}

/* ── WORKSPACE HEADER ── */
.ws-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 20px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 14px;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    margin-bottom: 24px;
}
.ws-logo {
    font-family: 'Inter', sans-serif;
    font-size: 22px; font-weight: 800; color: #CDD6F4;
    letter-spacing: -0.02em; cursor: pointer; user-select: none;
}
.ws-logo span { color: #89DCEB; }
.ws-user {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px; color: #BAC2DE;
    display: flex; align-items: center; gap: 12px;
}
.ws-avatar {
    width: 32px; height: 32px; border-radius: 8px;
    background: linear-gradient(135deg, #89DCEB, #A78BFA);
    color: #0C0E14;
    font-weight: 700; font-size: 13px;
    display: flex; align-items: center; justify-content: center;
}
.xp-badge {
    color: #FBBF24;
    font-size: 11px; letter-spacing: 0.05em;
}
.streak-badge { color: #F472B6; font-size: 11px; }

/* Active nav button */
.nav-tabs .stButton button[kind="primary"] {
    background: rgba(137,220,235,0.10) !important;
    border: 1px solid rgba(137,220,235,0.4) !important;
    color: #89DCEB !important;
    border-radius: 8px !important;
    box-shadow: 0 0 10px rgba(137,220,235,0.12) !important;
}
.nav-tabs .stButton button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid transparent !important;
    color: #585B70 !important;
    border-radius: 8px !important;
}
.nav-tabs .stButton button:hover {
    color: #BAC2DE !important;
    border-color: rgba(255,255,255,0.15) !important;
}

/* ── AGENT VIEW LAYOUT ── */
.agent-ctrl {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    backdrop-filter: blur(16px);
    padding: 20px 16px;
    min-height: 80vh;
}
.ctrl-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; text-transform: uppercase;
    letter-spacing: 0.1em; color: #45475A;
    margin-bottom: 8px; margin-top: 20px;
}
.ctrl-label:first-child { margin-top: 0; }

/* Dashboard stat tiles */
.dash-stat {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 14px;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    padding: 20px 16px;
    text-align: center;
    transition: box-shadow 0.2s, transform 0.2s;
}
.dash-stat:hover {
    box-shadow: 0 0 24px rgba(137,220,235,0.1);
    transform: translateY(-2px);
}
.dash-stat-val {
    font-family: 'Inter', sans-serif;
    font-size: 28px; font-weight: 700;
    background: linear-gradient(135deg, #CDD6F4, #89DCEB);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.dash-stat-lbl {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; text-transform: uppercase;
    letter-spacing: 0.08em; color: #45475A; margin-top: 6px;
}

/* Dashboard agent cards */
.dash-agent-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 14px;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    padding: 20px 18px 16px;
    min-height: 170px;
    transition: box-shadow 0.2s, transform 0.2s, border-color 0.2s;
    cursor: pointer;
}
.dash-agent-card:hover {
    border-color: rgba(255,255,255,0.18);
    box-shadow: 0 4px 24px rgba(0,0,0,0.3), 0 0 20px var(--card-glow, rgba(137,220,235,0.12));
    transform: translateY(-3px);
}
</style>
"""


def inject_css() -> None:
    """Inject the glassmorphism dark theme. Call after st.set_page_config()."""
    st.markdown(_CSS, unsafe_allow_html=True)


def inject_welcome_css() -> None:
    """Inject additional CSS for the welcome page and workspace chrome."""
    st.markdown(_WELCOME_CSS, unsafe_allow_html=True)
