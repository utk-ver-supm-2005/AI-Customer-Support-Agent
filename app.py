"""
Streamlit Web Frontend — AI Customer Support Knowledge Agent
Primary visual reference : Smartpro.ai SaaS Dashboard (light sidebar, white cards, cool-grey BG)
Secondary references     : AI customer-support inbox/analysis panels
Demonstrating Objectives 1 (NLP extraction) and 2 (workflow routing) end-to-end.
"""

import json
import base64
from pathlib import Path
from PIL import Image
import streamlit as st

ASSETS_DIR = Path(__file__).parent / "assets"
ICON_PATH = ASSETS_DIR / "bot_icon.png"

# Load 3D Bot page icon image if available, fallback to emoji
page_icon = Image.open(ICON_PATH) if ICON_PATH.exists() else "🤖"

def get_bot_icon_base64() -> str:
    """Return base64 data URI of the 3D bot icon for HTML embedding."""
    if ICON_PATH.exists():
        with open(ICON_PATH, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    return ""

from workflow_router import TicketPriority
from main import process_and_route_ticket
from sample_scenarios import SCENARIOS
from gmail_service import get_gmail_status
from ticket_tracker import (
    TicketStage,
    STAGE_PROGRESS,
    STAGE_ORDER,
    STAGE_BADGE_CLASSES,
    get_ticket,
    update_ticket_stage,
    get_all_tickets,
    reset_ticket,
    normalize_stage,
)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Customer Support Knowledge Agent",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS  —  Smartpro.ai light-theme recreation
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Keyframe animations ──────────────────────────────────────────────── */
@keyframes orb-drift-a {
    0%   { transform: translate(0px, 0px) scale(1); }
    33%  { transform: translate(40px, -30px) scale(1.08); }
    66%  { transform: translate(-25px, 20px) scale(0.95); }
    100% { transform: translate(0px, 0px) scale(1); }
}
@keyframes orb-drift-b {
    0%   { transform: translate(0px, 0px) scale(1); }
    40%  { transform: translate(-35px, 25px) scale(1.05); }
    80%  { transform: translate(20px, -15px) scale(0.97); }
    100% { transform: translate(0px, 0px) scale(1); }
}
@keyframes pipeline-pulse {
    0%   { box-shadow: 0 0 0 0 rgba(0,102,255,0.18); }
    60%  { box-shadow: 0 0 0 7px rgba(0,102,255,0); }
    100% { box-shadow: 0 0 0 0 rgba(0,102,255,0); }
}
@keyframes glow-node {
    0%, 100% { box-shadow: 0 0 6px 1px rgba(0,102,255,0.35); }
    50%       { box-shadow: 0 0 14px 4px rgba(0,102,255,0.55); }
}
@keyframes connector-flow {
    0%   { background-position: 0% 50%; }
    100% { background-position: 200% 50%; }
}
@keyframes result-appear {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes badge-pop {
    0%   { transform: scale(1); }
    40%  { transform: scale(1.12); }
    100% { transform: scale(1); }
}
@keyframes scan-line {
    0%   { top: 0%; opacity: 0.6; }
    100% { top: 100%; opacity: 0; }
}
@keyframes processing-ring {
    0%   { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* ── Respect prefers-reduced-motion ──────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}

/* ── Ambient background orbs ──────────────────────────────────────────── */
.stApp::before {
    content: '';
    position: fixed;
    top: -120px; left: -120px;
    width: 480px; height: 480px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(0,102,255,0.06) 0%, transparent 70%);
    animation: orb-drift-a 22s ease-in-out infinite;
    pointer-events: none; z-index: 0;
}
.stApp::after {
    content: '';
    position: fixed;
    top: 30%; right: -80px;
    width: 360px; height: 360px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(124,58,237,0.05) 0%, transparent 70%);
    animation: orb-drift-b 28s ease-in-out infinite;
    pointer-events: none; z-index: 0;
}

/* ── Reset & base ─────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 Helvetica, Arial, sans-serif;
    color: #1E293B;
}
.stApp { background-color: #F1F5F9 !important; }
.block-container {
    padding-top: 0 !important;
    padding-bottom: 2rem !important;
    padding-left: 1.1rem !important;
    padding-right: 1.1rem !important;
    max-width: 1480px !important;
    position: relative; z-index: 1;
}

/* ── White light sidebar ──────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
    min-width: 210px !important;
    max-width: 210px !important;
}
[data-testid="stSidebar"] * { color: #334155 !important; }

/* ── Sidebar radio nav items ─────────────────────────────────────────── */
[data-testid="stSidebar"] .stRadio > div { gap: 0.05rem !important; }
[data-testid="stSidebar"] .stRadio label {
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 0.42rem 0.6rem !important;
    border-radius: 7px !important;
    cursor: pointer;
    transition: background 0.12s;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: #F1F5F9 !important;
}

/* ── Sidebar brand ────────────────────────────────────────────────────── */
.sb-brand {
    display: flex; align-items: center; gap: 0.55rem;
    padding: 0.85rem 0.7rem 0.85rem 0.7rem;
    border-bottom: 1px solid #F1F5F9;
    margin-bottom: 0.5rem;
}
.sb-icon {
    background: #0066FF; color: #fff; border-radius: 8px;
    width: 30px; height: 30px; display: flex; align-items: center;
    justify-content: center; font-size: 1rem; font-weight: 700;
    flex-shrink: 0;
}
.sb-title { font-size: 1.1rem; font-weight: 800; color: #0F172A !important; letter-spacing: -0.02em; }
.sb-title-dot { color: #0066FF !important; }

/* ── Sidebar group labels ────────────────────────────────────────────── */
.sb-group {
    font-size: 0.67rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.07em; color: #94A3B8 !important;
    margin: 0.75rem 0 0.25rem 0.45rem;
}

/* ── Sidebar system status box ───────────────────────────────────────── */
.sb-status {
    background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;
    padding: 0.7rem 0.85rem; margin-top: 1.2rem;
}
.sb-status-hdr {
    font-size: 0.67rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em; color: #64748B !important; margin-bottom: 0.45rem;
}
.sb-status-row {
    display: flex; align-items: center; justify-content: space-between;
    font-size: 0.77rem; margin-bottom: 0.3rem; color: #475569 !important;
}
.tag-green  { color: #059669 !important; font-weight: 700; font-size: 0.73rem; }
.tag-amber  { color: #D97706 !important; font-weight: 700; font-size: 0.73rem; }
.tag-gray   { color: #94A3B8 !important; font-size: 0.73rem; }

/* ── Top navigation bar ──────────────────────────────────────────────── */
.topbar {
    display: flex; align-items: center; justify-content: space-between;
    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
    padding: 0.6rem 1.2rem; margin-bottom: 0.9rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.topbar-search {
    display: flex; align-items: center; gap: 0.5rem;
    background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;
    padding: 0.38rem 0.9rem; font-size: 0.85rem; color: #94A3B8; flex: 1;
    max-width: 420px;
}
.topbar-right { display: flex; align-items: center; gap: 0.9rem; }
.topbar-badge {
    font-size: 0.78rem; font-weight: 700; background: #EFF6FF;
    color: #1E40AF; border-radius: 9999px; padding: 0.2rem 0.6rem;
}
.topbar-notif { font-size: 1.05rem; cursor: pointer; }
.topbar-avatar {
    background: #7C3AED; color: white; border-radius: 50%;
    width: 30px; height: 30px; display: flex; align-items: center;
    justify-content: center; font-size: 0.78rem; font-weight: 700;
}
.topbar-username { font-size: 0.86rem; font-weight: 700; color: #0F172A; }
.topbar-role    { font-size: 0.72rem; color: #64748B; }

/* ── Page heading strip ──────────────────────────────────────────────── */
.pg-hdr { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 0.9rem; }
.pg-title { font-size: 1.5rem; font-weight: 800; color: #0F172A; letter-spacing: -0.025em; margin: 0; }
.pg-sub   { font-size: 0.85rem; color: #64748B; margin-top: 0.12rem; }

/* ── Summary cards row ───────────────────────────────────────────────── */
.card-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 0.85rem; margin-bottom: 1rem; }
.sum-card {
    border-radius: 12px; padding: 0.9rem 1.1rem;
    border: 1px solid transparent;
    box-shadow: 0 1px 2px rgba(0,0,0,0.025);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.sum-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.05);
}
.sum-card.blue   { background:#F0F7FF; border-color:#DBEAFE; }
.sum-card.purple { background:#FAF5FF; border-color:#F3E8FF; }
.sum-card.teal   { background:#F0FDF4; border-color:#DCFCE7; }
.sum-card.orange { background:#FFF7ED; border-color:#FFEDD5; }
.sc-label {
    display: flex; align-items: center; justify-content: space-between;
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.05em; margin-bottom: 0.2rem;
}
.sc-label.blue   { color: #1E40AF; }
.sc-label.purple { color: #6B21A8; }
.sc-label.teal   { color: #166534; }
.sc-label.orange { color: #9A3412; }
.sc-val  { font-size: 1.8rem; font-weight: 800; color: #0F172A; line-height: 1.1; }
.sc-note { font-size: 0.75rem; color: #64748B; margin-top: 0.15rem; }

/* ── White panel cards ───────────────────────────────────────────────── */
.wp {
    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
    padding: 1rem 1.1rem; margin-bottom: 0.9rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.025);
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.wp:hover {
    box-shadow: 0 4px 14px rgba(0,0,0,0.04);
}
.wp-hdr {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 0.8rem;
}
.wp-title { font-size: 1rem; font-weight: 700; color: #0F172A; }
.wp-badge {
    font-size: 0.7rem; font-weight: 700; border-radius: 9999px;
    padding: 0.15rem 0.55rem;
}
.wp-badge.green  { background:#D1FAE5; color:#065F46; }
.wp-badge.blue   { background:#DBEAFE; color:#1E40AF; }
.wp-badge.amber  { background:#FEF3C7; color:#92400E; }
.wp-badge.gray   { background:#F1F5F9; color:#475569; }

/* ── Inbox list items & Clickable Cards ──────────────────────────────── */
div[class*="st-key-inbox_card_"] {
    position: relative !important;
    cursor: pointer !important;
    margin-bottom: 0.55rem !important;
}

.inbox-item {
    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px;
    padding: 0.7rem 0.85rem; margin-bottom: 0.55rem;
    transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
    cursor: pointer;
    user-select: none;
}
div[class*="st-key-inbox_card_"] .inbox-item {
    margin-bottom: 0 !important;
}
div[class*="st-key-inbox_card_"]:hover .inbox-item,
.inbox-item:hover {
    border-color: #0066FF !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(0, 102, 255, 0.15) !important;
}
.inbox-item.active {
    border-color: #0066FF !important;
    background: #F0F7FF !important;
    box-shadow: 0 2px 8px rgba(0, 102, 255, 0.12) !important;
}

/* Position the button wrapper over the entire card */
div[class*="st-key-inbox_card_"] > div:last-child,
div[class*="st-key-inbox_card_"] div[data-testid="stElementContainer"]:has(button),
div[class*="st-key-inbox_card_"] div[data-testid="element-container"]:has(button),
div[class*="st-key-inbox_card_"] div.element-container:has(button),
div[class*="st-key-inbox_card_"] div[data-testid="stButton"],
div[class*="st-key-inbox_card_"] div.stButton {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    z-index: 10 !important;
}

/* Completely transparent button overlay covering 100% of the card */
div[class*="st-key-inbox_card_"] button,
div[class*="st-key-inbox_card_"] .stButton > button {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    opacity: 0 !important;
    z-index: 10 !important;
    cursor: pointer !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    transform: none !important;
}

div[class*="st-key-inbox_card_"] button:hover,
div[class*="st-key-inbox_card_"] button:active,
div[class*="st-key-inbox_card_"] button:focus,
div[class*="st-key-inbox_card_"] .stButton > button:hover,
div[class*="st-key-inbox_card_"] .stButton > button:active,
div[class*="st-key-inbox_card_"] .stButton > button:focus {
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    border: none !important;
    outline: none !important;
    transform: none !important;
}
.inbox-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.15rem; }
.inbox-name { font-size: 0.88rem; font-weight: 700; color: #0F172A; }
.inbox-time { font-size: 0.7rem; color: #94A3B8; }
.inbox-subject { font-size: 0.8rem; font-weight: 600; color: #1E293B; margin-bottom: 0.1rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.inbox-snippet { font-size: 0.75rem; color: #64748B; margin-bottom: 0.3rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.inbox-footer { display: flex; justify-content: space-between; align-items: center; }
.inbox-avatar {
    width: 24px; height: 24px; border-radius: 50%;
    color: white; font-size: 0.65rem; font-weight: 700;
    display: inline-flex; align-items: center; justify-content: center;
    margin-right: 0.4rem; flex-shrink: 0;
}

/* ── Category mini-badges ────────────────────────────────────────────── */
.badge {
    display: inline-block; padding: 0.14rem 0.52rem;
    font-size: 0.72rem; font-weight: 700; border-radius: 4px;
    border: 1px solid transparent;
    transition: transform 0.15s ease;
}
.badge:hover {
    transform: scale(1.04);
}
.badge.billing { background:#FEE2E2; color:#991B1B; border-color:#FECACA; }
.badge.api     { background:#DBEAFE; color:#1E40AF; border-color:#BFDBFE; }
.badge.account { background:#DCFCE7; color:#166534; border-color:#BBF7D0; }
.badge.export  { background:#FFEDD5; color:#9A3412; border-color:#FED7AA; }
.badge.feature { background:#CCFBF1; color:#0F766E; border-color:#99F6E4; }
.badge.review  { background:#F1F5F9; color:#475569; border-color:#CBD5E1; }

/* ── Result appearance animation container ──────────────────────────── */
.result-container {
    animation: result-appear 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

/* ── Animated Pipeline Grid ──────────────────────────────────────────── */
.pipeline-grid {
    display: grid;
    grid-template-columns: 1fr 40px 1fr 40px 1fr 40px 1fr;
    align-items: stretch;
    gap: 0;
    margin: 0.65rem 0 0.25rem 0;
}
@media (max-width: 900px) {
    .pipeline-grid {
        grid-template-columns: 1fr;
        gap: 0.75rem;
    }
    .pipeline-arrow-slot {
        display: none;
    }
}
.pipeline-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 0.85rem 1rem;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 102px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.pipeline-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,102,255,0.08);
}
.pipeline-card.completed {
    background: #F8FAFC;
    border-color: #CBD5E1;
    border-left: 3.5px solid #10B981;
}
.pipeline-card.active-stage {
    background: #F0F7FF;
    border-color: #93C5FD;
    border-left: 3.5px solid #0066FF;
    animation: pipeline-pulse 2.5s infinite;
}
.pipeline-card.preview-stage {
    background: #FAFAFA;
    border: 1px dashed #CBD5E1;
    border-left: 3.5px dashed #F59E0B;
}
.stage-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.4rem;
}
.stage-step-lbl {
    font-size: 0.68rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #475569;
}
.stage-pill {
    font-size: 0.68rem;
    font-weight: 700;
    padding: 0.12rem 0.5rem;
    border-radius: 9999px;
    white-space: nowrap;
}
.pill-completed { background: #DCFCE7; color: #15803D; border: 1px solid #BBF7D0; }
.pill-active    { background: #DBEAFE; color: #1D4ED8; border: 1px solid #BFDBFE; }
.pill-ready     { background: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; }
.pill-preview   { background: #FEF3C7; color: #B45309; border: 1px solid #FDE68A; }
.pill-high      { background: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; }
.pill-medium    { background: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }
.pill-low       { background: #DCFCE7; color: #166534; border: 1px solid #BBF7D0; }

.stage-body {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
}
.stage-icon {
    font-size: 1.3rem;
    line-height: 1.1;
    flex-shrink: 0;
    margin-top: 0.05rem;
}
.stage-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.25;
}
.stage-desc {
    font-size: 0.74rem;
    color: #475569;
    margin-top: 0.2rem;
    line-height: 1.35;
}
.pipeline-arrow-slot {
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    padding: 0 4px;
}
.connector-line {
    width: 100%;
    height: 3px;
    background: #CBD5E1;
    border-radius: 2px;
    position: relative;
}
.connector-line.animated-flow {
    background: linear-gradient(90deg, #0066FF, #7C3AED, #0066FF);
    background-size: 200% 100%;
    animation: connector-flow 2.8s linear infinite;
}
.connector-line.dashed-flow {
    background: transparent;
    border-top: 2px dashed #CBD5E1;
    height: 0;
}
.flow-node-dot {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #0066FF;
    animation: glow-node 2s infinite ease-in-out;
}

/* ── Issue / Intent pill display ─────────────────────────────────────── */
.pill-issue {
    background:#FEF2F2; color:#991B1B; border:1px solid #FECACA;
    border-radius:6px; padding:0.42rem 0.7rem;
    font-size:0.88rem; font-weight:600; line-height:1.4; display:block;
}
.pill-intent {
    background:#EFF6FF; color:#1E40AF; border:1px solid #BFDBFE;
    border-radius:6px; padding:0.42rem 0.7rem;
    font-size:0.88rem; font-weight:600; line-height:1.4; display:block;
}

/* ── Entity tags ─────────────────────────────────────────────────────── */
.entity-wrap { display:flex; flex-wrap:wrap; gap:0.35rem; margin-bottom:0.5rem; }
.etag {
    display:inline-flex; align-items:center; gap:0.2rem;
    background:#F1F5F9; border:1px solid #CBD5E1; border-radius:4px;
    padding:0.22rem 0.55rem; font-size:0.78rem; color:#0F172A;
}
.etag-k { font-weight:700; color:#0066FF; margin-right:0.15rem; }

/* ── AI field label ──────────────────────────────────────────────────── */
.afl {
    font-size:0.68rem; font-weight:700; text-transform:uppercase;
    letter-spacing:0.055em; color:#64748B; margin-bottom:0.25rem;
}

/* ── Context box ─────────────────────────────────────────────────────── */
.ctx-box {
    background:#F8FAFC; border:1px solid #E2E8F0; border-radius:7px;
    padding:0.6rem 0.8rem; font-size:0.82rem; color:#334155; line-height:1.45;
    margin-bottom:0.5rem;
}

/* ── Priority badge ──────────────────────────────────────────────────── */
.pri-high   { color:#DC2626; font-weight:800; font-size:0.82rem; }
.pri-medium { color:#D97706; font-weight:800; font-size:0.82rem; }
.pri-low    { color:#16A34A; font-weight:800; font-size:0.82rem; }

/* ── Route box ───────────────────────────────────────────────────────── */
.route-box {
    background:#EFF6FF; border:1px solid #BFDBFE; border-radius:8px;
    padding:0.6rem 0.85rem; margin-bottom:0.55rem;
}
.route-label { font-size:0.67rem; font-weight:700; color:#1E40AF; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.1rem; }
.route-val   { font-size:0.95rem; font-weight:700; color:#0F172A; }

/* ── Routing reason strip ────────────────────────────────────────────── */
.reason-strip {
    background:#F0FDF4; border-left:3px solid #16A34A;
    border-radius:0 7px 7px 0; padding:0.55rem 0.8rem;
    font-size:0.82rem; color:#166534; line-height:1.4;
    margin-bottom:0.55rem;
}

/* ── Action list rows ────────────────────────────────────────────────── */
.action-row {
    display:flex; align-items:flex-start; gap:0.55rem;
    font-size:0.83rem; color:#334155; line-height:1.4; margin-bottom:0.38rem;
}
.action-num {
    background:#DBEAFE; color:#1E40AF; border-radius:50%;
    width:19px; height:19px; display:flex; align-items:center;
    justify-content:center; font-size:0.68rem; font-weight:700;
    flex-shrink:0; margin-top:2px;
}

/* ── KB article row ──────────────────────────────────────────────────── */
.kb-row {
    display:flex; align-items:center; gap:0.5rem;
    font-size:0.82rem; color:#0066FF; font-weight:500;
    padding:0.35rem 0; border-bottom:1px solid #F1F5F9;
}
.kb-row:last-child { border-bottom:none; }
.kb-icon { color:#94A3B8; font-size:0.85rem; }

/* ── Customer info strip ─────────────────────────────────────────────── */
.cust-strip {
    display:flex; align-items:center; gap:0.6rem;
    background:#F8FAFC; border:1px solid #E2E8F0; border-radius:6px;
    padding:0.42rem 0.75rem; margin-bottom:0.75rem; font-size:0.82rem;
}
.cust-name  { font-weight:700; color:#0F172A; }
.cust-email { color:#64748B; }
.cust-plan  { margin-left:auto; color:#94A3B8; font-size:0.76rem; }

/* ── Attachment strip ────────────────────────────────────────────────── */
.attach-strip {
    display:flex; align-items:center; gap:0.45rem;
    background:#F8FAFC; border:1px solid #E2E8F0; border-radius:6px;
    padding:0.38rem 0.7rem; margin-top:0.5rem; font-size:0.8rem; color:#475569;
}

/* ── Priority meter box ──────────────────────────────────────────────── */
.pri-box {
    background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px;
    padding:0.55rem 0.7rem; text-align:center;
}

/* ── Pipeline steps ──────────────────────────────────────────────────── */
.pipeline { display:flex; align-items:center; gap:0.5rem; overflow-x:auto; padding:0.35rem 0; }
.ps {
    background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px;
    padding:0.7rem 0.85rem; flex:1; min-width:155px;
}
.ps.active { background:#EFF6FF; border-color:#0066FF; }
.ps-step  { font-size:0.67rem; font-weight:700; text-transform:uppercase; color:#0066FF; margin-bottom:0.12rem; }
.ps-step.dim { color:#94A3B8; }
.ps-title { font-size:0.86rem; font-weight:700; color:#0F172A; }
.ps-title.dim { color:#64748B; }
.ps-desc  { font-size:0.72rem; color:#64748B; margin-top:0.1rem; }
.ps-arrow { color:#CBD5E1; font-size:1.2rem; font-weight:700; flex-shrink:0; }

/* ── Table header ────────────────────────────────────────────────────── */
.tbl-hdr {
    display:grid; grid-template-columns:90px 1fr 120px 80px 90px;
    gap:0.5rem; padding:0.35rem 0.5rem;
    font-size:0.67rem; font-weight:700; text-transform:uppercase;
    letter-spacing:0.05em; color:#94A3B8; border-bottom:1px solid #E2E8F0;
    margin-bottom:0.35rem;
}

/* ── Buttons override ────────────────────────────────────────────────── */
.stButton > button {
    background-color: #0066FF !important;
    color: #FFFFFF !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.18s ease-in-out !important;
}
.stButton > button:hover {
    background-color: #0052CC !important;
    box-shadow: 0 4px 12px rgba(0,102,255,0.25) !important;
    transform: translateY(-1px);
}
.stButton > button:active {
    transform: translateY(1px) scale(0.99) !important;
}

/* ── Awaiting placeholder ────────────────────────────────────────────── */
.await-box {
    background:#F8FAFC; border:2px dashed #E2E8F0; border-radius:8px;
    padding:2rem 1rem; text-align:center; color:#94A3B8; margin-top:0.3rem;
}
.await-icon  { font-size:1.8rem; margin-bottom:0.35rem; }
.await-title { font-size:0.92rem; font-weight:700; color:#1E293B; margin-bottom:0.2rem; }
.await-sub   { font-size:0.78rem; }

/* ── Status indicator dots ───────────────────────────────────────────── */
.dot-green { color:#10B981; }
.dot-amber { color:#F59E0B; }
.dot-gray  { color:#94A3B8; }

/* ── Divider ─────────────────────────────────────────────────────────── */
.thin-divider { border:none; border-top:1px solid #F1F5F9; margin:0.6rem 0; }

/* ── Streamlit element tweaks ────────────────────────────────────────── */
[data-testid="stTextArea"] textarea {
    font-size:0.83rem !important;
    border-radius:8px !important;
    border:1px solid #E2E8F0 !important;
    background:#F8FAFC !important;
    color:#1E293B !important;
}
[data-testid="stTextArea"] textarea:focus {
    border-color:#0066FF !important;
    background:#FFFFFF !important;
}
.stSelectbox select, [data-testid="stSelectbox"] {
    font-size: 0.85rem !important;
}

/* ── Modern Support Inbox Ticket Dropdown (Inspiration Reference) ── */
.inbox-dropdown-wrap {
    margin-bottom: 0.85rem;
}
.inbox-dropdown-wrap [data-testid="stSelectbox"] {
    margin-bottom: 0 !important;
}
.inbox-dropdown-wrap [data-testid="stSelectbox"] > div {
    border: none !important;
    background: transparent !important;
}
/* Main select input box */
.inbox-dropdown-wrap [data-baseweb="select"] {
    background-color: #FFFFFF !important;
    border: 1.5px solid #BFDBFE !important; /* subtle light-blue border */
    border-radius: 12px !important;
    min-height: 50px !important;
    height: 50px !important;
    box-shadow: 0 1px 3px rgba(0, 102, 255, 0.04) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
}
.inbox-dropdown-wrap [data-baseweb="select"]:hover {
    border-color: #60A5FA !important;
    background-color: #F8FAFC !important;
    box-shadow: 0 2px 6px rgba(0, 102, 255, 0.08) !important;
}
.inbox-dropdown-wrap [data-baseweb="select"]:focus-within {
    border-color: #2563EB !important;
    background-color: #FFFFFF !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.16) !important; /* soft blue focus ring */
}
/* Selected value text container */
.inbox-dropdown-wrap [data-baseweb="select"] > div:first-child {
    padding-left: 0.75rem !important;
    padding-right: 0.5rem !important;
    font-size: 0.86rem !important;
    font-weight: 600 !important;
    color: #0F172A !important; /* dark navy text */
    height: 100% !important;
    display: flex !important;
    align-items: center !important;
}
/* Selectbox text / placeholder */
.inbox-dropdown-wrap [data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
.inbox-dropdown-wrap [data-baseweb="select"] span {
    color: #0F172A !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
/* Chevron icon aligned to the right with refined blue styling */
.inbox-dropdown-wrap [data-baseweb="select"] svg {
    color: #2563EB !important;
    fill: #2563EB !important;
    width: 20px !important;
    height: 20px !important;
    transition: transform 0.2s ease !important;
    margin-right: 0.4rem !important;
}

/* Global styling for Streamlit dropdown menus (BaseWeb popover/menu) */
div[data-baseweb="popover"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.12), 0 8px 10px -6px rgba(15, 23, 42, 0.08) !important;
    border: 1px solid #E2E8F0 !important;
}
div[data-baseweb="popover"] ul[role="listbox"] {
    background-color: #FFFFFF !important;
    padding: 0.35rem !important;
    border-radius: 12px !important;
}
div[data-baseweb="popover"] li[role="option"] {
    padding: 0.65rem 0.85rem !important;
    border-radius: 8px !important;
    font-size: 0.84rem !important;
    color: #0F172A !important;
    font-weight: 500 !important;
    transition: background-color 0.15s ease, color 0.15s ease !important;
    margin-bottom: 2px !important;
}
/* Light blue hover on dropdown items matching user inspiration */
div[data-baseweb="popover"] li[role="option"]:hover,
div[data-baseweb="popover"] li[role="option"][aria-selected="false"]:hover {
    background-color: #EFF6FF !important; /* very light blue hover */
    color: #1D4ED8 !important;
}
/* Selected option highlighted */
div[data-baseweb="popover"] li[role="option"][aria-selected="true"] {
    background-color: #DBEAFE !important; /* distinguished active blue */
    color: #1E40AF !important;
    font-weight: 700 !important;
}
[data-testid="stExpander"] { background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; }

/* ── Complaint Lifecycle Stepper Progress Bar (Inspiration Reference) ── */
.stepper-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 0.85rem 1.15rem 0.75rem 1.15rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.025);
}
.stepper-hdr {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
}
.stepper-title {
    font-size: 0.86rem;
    font-weight: 700;
    color: #0F172A;
    display: flex;
    align-items: center;
    gap: 0.45rem;
}
.stepper-sub {
    font-size: 0.7rem;
    color: #64748B;
    margin-top: 0.1rem;
}
.stepper-flow {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    width: 100%;
}
.step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    position: relative;
}
.step-caret {
    height: 11px;
    font-size: 0.72rem;
    line-height: 11px;
    color: #16A34A;
    font-weight: 900;
    margin-bottom: 1px;
    visibility: hidden;
}
.step-caret.active {
    visibility: visible;
}
.step-connector-row {
    display: flex;
    align-items: center;
    width: 100%;
    margin-bottom: 0.35rem;
}
.step-line {
    flex: 1;
    height: 3px;
    background: #E2E8F0;
    border-radius: 2px;
}
.step-line.completed {
    background: #22C55E;
}
.step-line.hidden {
    visibility: hidden;
}
.step-node {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.74rem;
    font-weight: 800;
    flex-shrink: 0;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    z-index: 2;
}
.step-node.completed {
    background: #22C55E;
    color: #FFFFFF;
    box-shadow: 0 2px 6px rgba(34, 197, 94, 0.35);
}
.step-node.active {
    background: #16A34A;
    color: #FFFFFF;
    box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.22);
}
.step-node.pending {
    background: #FFFFFF;
    border: 2px solid #CBD5E1;
    color: #94A3B8;
}
.step-label {
    font-size: 0.71rem;
    text-align: center;
    color: #64748B;
    line-height: 1.25;
    max-width: 86px;
}
.step-label.active {
    color: #0F172A;
    font-weight: 700;
}
.step-label.completed {
    color: #1E293B;
    font-weight: 600;
}
.step-pct {
    font-size: 0.67rem;
    font-weight: 700;
    margin-top: 0.1rem;
}
.step-pct.active {
    color: #16A34A;
}
.step-pct.completed {
    color: #22C55E;
}
.step-pct.pending {
    color: #94A3B8;
}

/* ── Lifecycle Stage Badges ───────────────────────────────────────────── */
.stage-badge {
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.16rem 0.55rem;
    border-radius: 9999px;
    white-space: nowrap;
}
.stage-badge-mini {
    font-size: 0.66rem;
    font-weight: 700;
    padding: 0.1rem 0.4rem;
    border-radius: 9999px;
    white-space: nowrap;
}
.stage-badge-received  { background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }
.stage-badge-analyzed  { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.stage-badge-routed    { background: #F3E8FF; color: #7E22CE; border: 1px solid #E9D5FF; }
.stage-badge-progress  { background: #FEF3C7; color: #B45309; border: 1px solid #FDE68A; }
.stage-badge-resolved  { background: #DCFCE7; color: #15803D; border: 1px solid #BBF7D0; }

/* ── Progress Bars on Cards & Tables ──────────────────────────────────── */
.card-pbar-bg {
    width: 100%;
    height: 4px;
    background: #E2E8F0;
    border-radius: 9999px;
    overflow: hidden;
    margin-top: 0.35rem;
}
.card-pbar-fill {
    height: 100%;
    background: linear-gradient(90deg, #10B981, #22C55E);
    border-radius: 9999px;
    transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.table-pbar-wrap {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    padding-top: 0.25rem;
}
.table-pbar-lbl {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.72rem;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
def _cat_badge(cat: str) -> str:
    c = cat.lower()
    if "billing" in c:   return '<span class="badge billing">Billing</span>'
    if "api" in c or "technical" in c: return '<span class="badge api">Technical</span>'
    if "account" in c or "login" in c: return '<span class="badge account">Account</span>'
    if "export" in c or "product" in c: return '<span class="badge export">Product</span>'
    if "feature" in c:   return '<span class="badge feature">Feature</span>'
    return '<span class="badge review">Review</span>'


def _pri_class(priority) -> str:
    v = str(priority).lower()
    if "high" in v:   return "pri-high"
    if "medium" in v: return "pri-medium"
    return "pri-low"


def _pri_label(priority) -> str:
    return str(priority.value if hasattr(priority, "value") else priority).upper()


def _init_state():
    if "selected_inbox_key" not in st.session_state:
        st.session_state.selected_inbox_key = list(SCENARIOS.keys())[0]
    if "analysis_cache" not in st.session_state:
        st.session_state.analysis_cache = {}


def render_complaint_stepper(ticket_data: dict) -> None:
    """
    Renders an independent horizontal multi-stage complaint progress stepper
    directly matching the inspiration design (media_1793290150580_e5ec1ce4.jpg):
    - 5 stages: Received (0%), Analyzed (25%), Classified & Routed (50%), In Progress (75%), Resolved (100%)
    - Completed nodes: Green circle with checkmark (✓)
    - Active node: Vibrant green circle with step number and active indicator caret (▾) above it
    - Pending nodes: Clean gray ring with step number
    - Horizontal green connecting lines for completed progress, gray for pending
    """
    current_stage = normalize_stage(ticket_data.get("stage", TicketStage.RECEIVED))
    current_idx = STAGE_ORDER.index(current_stage) if current_stage in STAGE_ORDER else 0
    progress = ticket_data.get("progress", STAGE_PROGRESS.get(current_stage, 0))
    t_id = ticket_data.get("ticket_id", "")

    badge_class = STAGE_BADGE_CLASSES.get(current_stage, "stage-badge-received")

    steps_html = []
    num_steps = len(STAGE_ORDER)
    for i, stage in enumerate(STAGE_ORDER):
        step_num = i + 1
        pct = STAGE_PROGRESS[stage]
        is_completed = (i < current_idx)
        is_active = (i == current_idx)

        caret_class = " active" if is_active else ""

        if is_completed:
            node_class = "completed"
            node_content = "✓"
            pct_class = "completed"
            lbl_class = "completed"
        elif is_active:
            node_class = "active"
            node_content = "✓" if stage == TicketStage.RESOLVED else str(step_num)
            pct_class = "active"
            lbl_class = "active"
        else:
            node_class = "pending"
            node_content = str(step_num)
            pct_class = "pending"
            lbl_class = "pending"

        if i == 0:
            left_line = '<div class="step-line hidden"></div>'
        else:
            line_status = "completed" if i <= current_idx else ""
            left_line = f'<div class="step-line {line_status}"></div>'

        if i == num_steps - 1:
            right_line = '<div class="step-line hidden"></div>'
        else:
            line_status = "completed" if i < current_idx else ""
            right_line = f'<div class="step-line {line_status}"></div>'

        steps_html.append(
            f'<div class="step-item">'
            f'<div class="step-caret{caret_class}">▾</div>'
            f'<div class="step-connector-row">'
            f'{left_line}'
            f'<div class="step-node {node_class}">{node_content}</div>'
            f'{right_line}'
            f'</div>'
            f'<div class="step-label {lbl_class}">{stage.value}</div>'
            f'<div class="step-pct {pct_class}">{pct}%</div>'
            f'</div>'
        )

    stepper_body = "".join(steps_html)

    stepper_html = (
        f'<div class="stepper-card">'
        f'<div class="stepper-hdr">'
        f'<div>'
        f'<div class="stepper-title">'
        f'<span>📌 Complaint Lifecycle Stage</span>'
        f'<span style="font-size:0.75rem;color:#0066FF;font-weight:700;">{t_id}</span>'
        f'</div>'
        f'<div class="stepper-sub">Predefined stages: Received (0%) → Analyzed (25%) → Classified &amp; Routed (50%) → In Progress (75%) → Resolved (100%)</div>'
        f'</div>'
        f'<span class="stage-badge {badge_class}">● {current_stage.value} ({progress}%)</span>'
        f'</div>'
        f'<div class="stepper-flow">'
        f'{stepper_body}'
        f'</div>'
        f'</div>'
    )

    if hasattr(st, "html"):
        st.html(stepper_html)
    else:
        st.markdown(stepper_html, unsafe_allow_html=True)


def render_ticket_status_controls(ticket_id: str, current_stage: str, panel_prefix: str = "dash") -> None:
    """
    Renders working controls for authorized demo users to transition ticket
    lifecycle to 'In Progress' (75%) or 'Resolved' (100%), or reset for demonstration.
    """
    controls_hdr_html = (
        '<div style="display:flex;align-items:center;justify-content:space-between;margin-top:0.35rem;margin-bottom:0.25rem;">'
        '<span style="font-size:0.73rem;font-weight:800;color:#334155;letter-spacing:0.04em;text-transform:uppercase;">'
        '🛡️ Authorized Demo Lifecycle Controls'
        '</span>'
        '<span style="font-size:0.69rem;color:#64748B;">Overrides persist to SQLite</span>'
        '</div>'
    )
    if hasattr(st, "html"):
        st.html(controls_hdr_html)
    else:
        st.markdown(controls_hdr_html, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.25, 1.25, 0.9], gap="small")

    with c1:
        is_ip = (current_stage == TicketStage.IN_PROGRESS.value)
        if st.button("▶ Mark In Progress (75%)", key=f"btn_mark_ip_{panel_prefix}_{ticket_id}", disabled=is_ip, use_container_width=True):
            update_ticket_stage(ticket_id, TicketStage.IN_PROGRESS, note="Demo supervisor marked In Progress")
            st.rerun()

    with c2:
        is_res = (current_stage == TicketStage.RESOLVED.value)
        if st.button("✔ Mark Resolved (100%)", key=f"btn_mark_res_{panel_prefix}_{ticket_id}", disabled=is_res, use_container_width=True):
            update_ticket_stage(ticket_id, TicketStage.RESOLVED, note="Demo supervisor marked Resolved")
            st.rerun()

    with c3:
        if st.button("↺ Reset (0%)", key=f"btn_mark_reset_{panel_prefix}_{ticket_id}", help="Reset this ticket back to Received (0%)", use_container_width=True):
            reset_ticket(ticket_id)
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar(gmail_info: dict) -> str:
    bot_b64 = get_bot_icon_base64()
    icon_html = (
        f'<img src="{bot_b64}" style="width:32px;height:32px;border-radius:8px;object-fit:cover;box-shadow:0 2px 8px rgba(0,102,255,0.18);flex-shrink:0;" />'
        if bot_b64 else '<div class="sb-icon">🤖</div>'
    )
    with st.sidebar:
        st.markdown(f"""
        <div class="sb-brand">
            {icon_html}
            <div class="sb-title">SmartSupport<span class="sb-title-dot">.ai</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sb-group">Overview</div>', unsafe_allow_html=True)
        nav = st.radio(
            "nav",
            [
                "🏠  Dashboard",
                "📥  Support Inbox",
                "🧭  Workflow Routing",
                "🎫  Tickets Queue",
                "📚  Knowledge Base",
                "👥  Customers",
                "⚡  Automations",
                "📈  Analytics",
                "⚙️  Settings & API",
            ],
            index=0,
            label_visibility="collapsed",
        )

        # System-status box
        st.markdown(f"""
        <div class="sb-status">
            <div class="sb-status-hdr">System Status</div>
            <div class="sb-status-row">
                <span><span class="dot-green">●</span> LLM (Gemini 3.5)</span>
                <span class="tag-green">Online</span>
            </div>
            <div class="sb-status-row">
                <span><span class="dot-green">●</span> Rule Engine</span>
                <span class="tag-green">Active</span>
            </div>
            <div class="sb-status-row">
                <span><span class="dot-amber">●</span> Gmail Intake</span>
                <span class="tag-amber">Fallback</span>
            </div>
            <div class="sb-status-row">
                <span><span class="dot-gray">○</span> Knowledge Base</span>
                <span class="tag-gray">Obj 3</span>
            </div>
            <div class="sb-status-row">
                <span><span class="dot-gray">○</span> Auto-Dispatch</span>
                <span class="tag-gray">Obj 4</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.caption("Objectives 1 & 2 are live. Obj 3 & 4 are preview/not implemented.")

    return nav


# ─────────────────────────────────────────────────────────────────────────────
# TOP BAR
# ─────────────────────────────────────────────────────────────────────────────
def render_topbar():
    st.markdown("""
    <div class="topbar">
        <div class="topbar-search">
            🔍&nbsp; Search support requests, customers, tickets…
        </div>
        <div class="topbar-right">
            <span class="topbar-badge">📧&nbsp;Fallback Mode</span>
            <span class="topbar-notif">🔔</span>
            <span class="topbar-notif">💬</span>
            <div style="display:flex;align-items:center;gap:0.45rem;">
                <div class="topbar-avatar">UV</div>
                <div>
                    <div class="topbar-username">Utkarsh Verma ▾</div>
                    <div class="topbar-role">Support Team</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY CARDS ROW
# ─────────────────────────────────────────────────────────────────────────────
def render_summary_cards():
    st.markdown("""
    <div class="card-grid">
        <div class="sum-card blue">
            <div class="sc-label blue"><span>Demo Requests</span><span>📋</span></div>
            <div class="sc-val">6</div>
            <div class="sc-note">Curated Support Scenarios</div>
        </div>
        <div class="sum-card purple">
            <div class="sc-label purple"><span>Support Categories</span><span>🧭</span></div>
            <div class="sc-val">6</div>
            <div class="sc-note">Deterministic Policy Queues</div>
        </div>
        <div class="sum-card teal">
            <div class="sc-label teal"><span>Implemented Objectives</span><span>🎯</span></div>
            <div class="sc-val">2</div>
            <div class="sc-note">Obj 1 (NLP) · Obj 2 (Routing)</div>
        </div>
        <div class="sum-card orange">
            <div class="sc-label orange"><span>Email Intake</span><span>📧</span></div>
            <div class="sc-val">Manual</div>
            <div class="sc-note">Sample / Fallback Mode Active</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# INBOX PANEL (shared — used on Dashboard + Inbox screen)
# ─────────────────────────────────────────────────────────────────────────────
def render_inbox_panel(custom_key: str, panel_prefix: str = "dash") -> None:
    """Renders the inbox list in a white-panel. Selection handled via clicking cards or dropdown."""
    scenario_keys = list(SCENARIOS.keys())
    all_keys = scenario_keys + [custom_key]

    current = st.session_state.selected_inbox_key
    if current not in all_keys:
        current = scenario_keys[0]

    st.markdown("""
    <div class="wp-hdr">
        <span class="wp-title">📥 Support Inbox</span>
        <span class="wp-badge blue">All (6)</span>
    </div>
    """, unsafe_allow_html=True)

    def _format_inbox_option(k: str) -> str:
        if k in SCENARIOS:
            sc = SCENARIOS[k]
            t_id = sc.get('ticket_id', '')
            subj = sc.get('subject', sc.get('title', ''))
            cat = sc.get('category', '')
            return f"{t_id}  ·  {subj}  [{cat}]"
        return "📝  Custom Request (Paste Any Message)"

    # Dropdown selector wrapped in modern styling container matching inspiration
    idx = all_keys.index(current) if current in all_keys else 0
    with st.container():
        st.markdown('<div class="inbox-dropdown-wrap">', unsafe_allow_html=True)
        selected = st.selectbox(
            "Ticket selector",
            all_keys,
            index=idx,
            format_func=_format_inbox_option,
            key=f"inbox_select_{panel_prefix}",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    if selected != st.session_state.selected_inbox_key:
        st.session_state.selected_inbox_key = selected
        st.rerun()

    # Visual inbox cards (now fully interactive & clickable with live progress)
    for i, k in enumerate(scenario_keys):
        sc = SCENARIOS[k]
        is_active = (k == st.session_state.selected_inbox_key)
        ac = " active" if is_active else ""
        badge = _cat_badge(sc["category"])

        # Query persistent lifecycle progress from SQLite
        t_id = sc.get('ticket_id', k)
        tk_info = get_ticket(t_id)
        tk_stage = tk_info["stage"]
        tk_prog = tk_info["progress"]
        tk_badge_cls = STAGE_BADGE_CLASSES.get(normalize_stage(tk_stage), "stage-badge-received")

        with st.container(key=f"inbox_card_{panel_prefix}_{i}"):
            st.markdown(f"""
            <div class="inbox-item{ac}">
                <div class="inbox-top">
                    <div style="display:flex;align-items:center;">
                        <div class="inbox-avatar" style="background:{sc.get('avatar_color','#3B82F6')}">
                            {sc.get('avatar_initials','?')}
                        </div>
                        <span class="inbox-name">{sc.get('sender_name','Customer')}</span>
                    </div>
                    <span class="inbox-time">{sc.get('timestamp','')}</span>
                </div>
                <div class="inbox-subject">{sc.get('subject', sc['title'])}</div>
                <div class="inbox-snippet">{sc.get('snippet','')}</div>
                <div class="inbox-footer">
                    {badge}
                    <span class="stage-badge-mini {tk_badge_cls}">● {tk_stage} ({tk_prog}%)</span>
                </div>
                <div class="card-pbar-bg">
                    <div class="card-pbar-fill" style="width: {tk_prog}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Select {sc.get('ticket_id', k)}", key=f"btn_inbox_{panel_prefix}_{i}"):
                st.session_state.selected_inbox_key = k
                st.rerun()

    # Custom intake card with live progress
    is_custom = (st.session_state.selected_inbox_key == custom_key)
    cc = " active" if is_custom else ""
    c_info = get_ticket("#CUSTOM-LIVE")
    c_stage = c_info["stage"]
    c_prog = c_info["progress"]
    c_badge_cls = STAGE_BADGE_CLASSES.get(normalize_stage(c_stage), "stage-badge-received")

    with st.container(key=f"inbox_card_{panel_prefix}_custom"):
        st.markdown(f"""
        <div class="inbox-item{cc}" style="border-style:dashed;">
            <div class="inbox-top">
                <div style="display:flex;align-items:center;">
                    <div class="inbox-avatar" style="background:#64748B">CU</div>
                    <span class="inbox-name">Custom Request</span>
                </div>
                <span class="inbox-time">Live</span>
            </div>
            <div class="inbox-snippet">Paste arbitrary email or dialogue thread…</div>
            <div class="inbox-footer">
                <span class="badge review">Manual Intake</span>
                <span class="stage-badge-mini {c_badge_cls}">● {c_stage} ({c_prog}%)</span>
            </div>
            <div class="card-pbar-bg">
                <div class="card-pbar-fill" style="width: {c_prog}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select Custom Request", key=f"btn_inbox_{panel_prefix}_custom"):
            st.session_state.selected_inbox_key = custom_key
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST INTAKE PANEL (Objective 1 input)
# ─────────────────────────────────────────────────────────────────────────────
def render_request_intake(panel_key_suffix: str) -> tuple:
    """Returns (request_text: str, source_label: str)."""
    custom_key = "📝 Custom Request (Paste Any Message)"
    selected_key = st.session_state.selected_inbox_key

    if selected_key != custom_key:
        sc = SCENARIOS[selected_key]
        badge = _cat_badge(sc["category"])
        t_id = sc.get('ticket_id', selected_key)
        tk_data = get_ticket(t_id)

        st.markdown(f"""
        <div class="wp-hdr">
            <div>
                <span class="wp-title">Request Intake</span>
                <span style="font-size:0.75rem;color:#64748B;margin-left:0.4rem;">{t_id}</span>
            </div>
            {badge}
        </div>
        <div class="cust-strip">
            <div class="inbox-avatar" style="background:{sc.get('avatar_color','#3B82F6')};width:26px;height:26px;font-size:0.7rem;">
                {sc.get('avatar_initials','?')}
            </div>
            <div>
                <span class="cust-name">{sc.get('sender_name','')}</span>
                &nbsp;<span class="cust-email">&lt;{sc.get('sender_email','')}&gt;</span>
            </div>
            <span class="cust-plan">Plan: {sc.get('customer_plan','—')}</span>
        </div>
        """, unsafe_allow_html=True)

        # Independent lifecycle stepper & demo user controls
        render_complaint_stepper(tk_data)
        render_ticket_status_controls(t_id, tk_data["stage"], panel_prefix=panel_key_suffix)

        request_text = st.text_area(
            "Message content:",
            value=sc["content"],
            height=195,
            key=f"req_text_{panel_key_suffix}_{selected_key}",
            label_visibility="collapsed",
        )

        # Attachment indicator
        if sc.get("attachment"):
            st.markdown(f"""
            <div class="attach-strip">
                📎&nbsp;<strong>{sc['attachment']}</strong>
            </div>
            """, unsafe_allow_html=True)

        source_label = f"Ticket: {sc.get('ticket_id','')} — {sc.get('subject','')}"
    else:
        t_id = "#CUSTOM-LIVE"
        tk_data = get_ticket(t_id)

        st.markdown("""
        <div class="wp-hdr">
            <span class="wp-title">Custom Support Request</span>
            <span class="badge review">Manual</span>
        </div>
        """, unsafe_allow_html=True)

        # Independent lifecycle stepper & demo user controls for custom intake
        render_complaint_stepper(tk_data)
        render_ticket_status_controls(t_id, tk_data["stage"], panel_prefix=f"{panel_key_suffix}_custom")
        request_text = st.text_area(
            "Paste your email or thread:",
            value="",
            placeholder="From: customer@example.com\nSubject: Need assistance...\n\nHello team...",
            height=220,
            key=f"req_custom_{panel_key_suffix}",
            label_visibility="collapsed",
        )
        source_label = "Custom Pasted Input"

    return request_text, source_label


# ─────────────────────────────────────────────────────────────────────────────
# AI ANALYSIS RESULTS PANEL (Objective 1 + 2 output)
# ─────────────────────────────────────────────────────────────────────────────
def render_analysis_result(result, show_kb_articles: bool = True):
    """Renders the full AI analysis + routing result into the current column/container."""
    if result is None:
        st.markdown("""
        <div class="await-box">
            <div class="await-icon">⚡</div>
            <div class="await-title">Awaiting Analysis</div>
            <div class="await-sub">Click <strong>"Run Extraction &amp; Routing"</strong> to execute live Gemini extraction.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown('<div class="result-container">', unsafe_allow_html=True)

    # ── Objective 1 ──────────────────────────────────────────────────────────
    st.markdown('<div class="afl">Customer Problem (Obj 1)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pill-issue" style="margin-bottom:0.5rem;">{result.issue}</div>', unsafe_allow_html=True)

    st.markdown('<div class="afl">Customer Intent</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pill-intent" style="margin-bottom:0.5rem;">{result.intent}</div>', unsafe_allow_html=True)

    st.markdown('<div class="afl">Extracted Entities</div>', unsafe_allow_html=True)
    if result.entities:
        tags = "".join(
            f'<span class="etag"><span class="etag-k">{k.replace("_"," ").title()}:</span>{v}</span>'
            for k, v in result.entities.items()
        )
        st.markdown(f'<div class="entity-wrap">{tags}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:0.78rem;color:#94A3B8;margin-bottom:0.5rem;">(No domain entities extracted)</div>', unsafe_allow_html=True)

    st.markdown('<div class="afl">Conversational Context</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ctx-box">{result.context}</div>', unsafe_allow_html=True)

    # ── Objective 2 ──────────────────────────────────────────────────────────
    st.markdown('<hr class="thin-divider">', unsafe_allow_html=True)
    st.markdown('<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.6rem;"><span style="font-size:0.95rem;font-weight:700;color:#0F172A;">Workflow Routing (Obj 2)</span><span class="wp-badge blue">Rule Engine</span></div>', unsafe_allow_html=True)

    # Category + Queue + Priority row
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        st.markdown(f"""
        <div class="pri-box">
            <div class="afl">Category</div>
            <div style="margin-top:0.2rem;">{_cat_badge(result.category.value)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="route-box">
            <div class="route-label">Assigned Team Queue</div>
            <div class="route-val">{result.route}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        pc = _pri_class(result.priority)
        pl = _pri_label(result.priority)
        st.markdown(f"""
        <div class="pri-box">
            <div class="afl">Priority</div>
            <div class="{pc}" style="margin-top:0.2rem;">{pl}</div>
        </div>
        """, unsafe_allow_html=True)

    # Routing reason
    st.markdown(f"""
    <div class="reason-strip" style="margin-top:0.55rem;">
        <strong>Routing Explanation:</strong> {result.routing_reason}
    </div>
    """, unsafe_allow_html=True)

    # Recommended actions
    st.markdown('<div class="afl">Recommended Actions</div>', unsafe_allow_html=True)
    actions = [
        result.suggested_action,
        f"Route ticket to <strong>{result.route}</strong> queue.",
        "Update SLA timestamp and send customer acknowledgement.",
    ]
    rows_html = "".join(
        f'<div class="action-row"><div class="action-num">{i+1}</div><div>{a}</div></div>'
        for i, a in enumerate(actions)
    )
    st.markdown(rows_html, unsafe_allow_html=True)

    # KB articles from scenario (if available)
    if show_kb_articles:
        sel_key = st.session_state.get("selected_inbox_key", "")
        articles = []
        if sel_key in SCENARIOS:
            articles = SCENARIOS[sel_key].get("articles", [])
        if articles:
            st.markdown('<hr class="thin-divider">', unsafe_allow_html=True)
            st.markdown('<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.4rem;"><span class="afl" style="margin-bottom:0;">Related Knowledge Base Articles</span><span style="font-size:0.72rem;color:#0066FF;font-weight:700;">Preview</span></div>', unsafe_allow_html=True)
            kb_rows = "".join(
                f'<div class="kb-row"><span class="kb-icon">📄</span>{a}</div>'
                for a in articles
            )
            st.markdown(kb_rows, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Raw JSON expander
    with st.expander("🔍 Raw JSON Output", expanded=False):
        st.json(result.model_dump())


# ─────────────────────────────────────────────────────────────────────────────
# ANIMATED PIPELINE VISUALIZATION
# ─────────────────────────────────────────────────────────────────────────────
def render_animated_pipeline(current_result, current_sc=None):
    """
    Renders an animated 4-stage horizontal workflow:
    1. Request Intake (Implemented)
    2. Objective 1: AI Issue & Context Extraction (Implemented)
    3. Objective 2: Classification & Workflow Routing (Implemented)
    4. Future Stage: Knowledge Retrieval & Auto-Dispatch (Phase 2 Preview)
    """
    # Stage 1 status (Intake)
    if current_sc:
        s1_pill = '<span class="stage-pill pill-completed">✓ Ingested</span>'
        s1_class = "completed"
        t_id = current_sc.get('ticket_id', '')
        s_name = current_sc.get('sender_name', 'Customer')
        s1_sub = f"<strong>{t_id}</strong> &bull; {s_name}"
        s1_note = f"<span style='font-size:0.71rem;color:#64748B;'>Plan: {current_sc.get('customer_plan','Standard')}</span>"
    elif current_result:
        s1_pill = '<span class="stage-pill pill-completed">✓ Custom Input</span>'
        s1_class = "completed"
        s1_sub = "<strong>Pasted Message</strong>"
        s1_note = "<span style='font-size:0.71rem;color:#64748B;'>User-provided text</span>"
    else:
        s1_pill = '<span class="stage-pill pill-ready">● Standby</span>'
        s1_class = "active-stage"
        s1_sub = "<strong>Normalized Input</strong>"
        s1_note = "<span style='font-size:0.71rem;color:#64748B;'>Select from inbox or paste</span>"

    # Stage 2 status (Obj 1: AI Context Extraction)
    if current_result:
        s2_pill = '<span class="stage-pill pill-completed">✓ Extracted</span>'
        s2_class = "completed"
        issue_text = current_result.issue if len(current_result.issue) <= 30 else current_result.issue[:28] + "…"
        s2_sub = f"<strong>{issue_text}</strong>"
        ent_count = len(current_result.entities) if current_result.entities else 0
        s2_note = f"<span style='font-size:0.71rem;color:#64748B;'>{ent_count} entities &bull; Gemini 3.5</span>"
    else:
        s2_pill = '<span class="stage-pill pill-active">● Active Node</span>'
        s2_class = "active-stage"
        s2_sub = "<strong>Gemini 3.5 Flash Lite</strong>"
        s2_note = "<span style='font-size:0.71rem;color:#64748B;'>Issue, intent &amp; entity NLP</span>"

    # Stage 3 status (Obj 2: Classification & Routing)
    if current_result:
        p_val = current_result.priority.value.upper()
        if p_val == "HIGH":
            p_class = "pill-high"
        elif p_val == "MEDIUM":
            p_class = "pill-medium"
        else:
            p_class = "pill-low"
        s3_pill = f'<span class="stage-pill {p_class}">● {p_val}</span>'
        s3_class = "completed"
        s3_sub = f"<strong>{current_result.category.value}</strong>"
        route_text = current_result.route if len(current_result.route) <= 26 else current_result.route[:24] + "…"
        s3_note = f"<span style='font-size:0.71rem;color:#64748B;'>{route_text}</span>"
    else:
        s3_pill = '<span class="stage-pill pill-ready">● Standby</span>'
        s3_class = ""
        s3_sub = "<strong>6-Route Engine</strong>"
        s3_note = "<span style='font-size:0.71rem;color:#64748B;'>Deterministic policy routing</span>"

    # Stage 4 status (Phase 2 Preview)
    s4_pill = '<span class="stage-pill pill-preview">⏳ Preview Only</span>'
    s4_class = "preview-stage"
    s4_sub = "<strong>Knowledge &amp; Dispatch</strong>"
    s4_note = "<span style='font-size:0.71rem;color:#94A3B8;'>Phase 2 RAG &amp; dispatch</span>"

    # Connector animations and glowing dots
    has_input = bool(current_sc or current_result)
    flow_1_2 = "animated-flow" if has_input else ""
    flow_2_3 = "animated-flow" if current_result else ""
    dot_1_2 = '<div class="flow-node-dot"></div>' if flow_1_2 else ""
    dot_2_3 = '<div class="flow-node-dot"></div>' if flow_2_3 else ""

    pipeline_html = f"""
    <div class="pipeline-grid">
        <!-- Stage 1 -->
        <div class="pipeline-card {s1_class}">
            <div class="stage-top">
                <span class="stage-step-lbl">Stage 1 · Intake</span>
                {s1_pill}
            </div>
            <div class="stage-body">
                <div class="stage-icon">📥</div>
                <div>
                    <div class="stage-title">Request Ingestion</div>
                    <div class="stage-desc">{s1_sub}<br>{s1_note}</div>
                </div>
            </div>
        </div>

        <!-- Connector 1 -> 2 -->
        <div class="pipeline-arrow-slot">
            <div class="connector-line {flow_1_2}">
                {dot_1_2}
            </div>
        </div>

        <!-- Stage 2 -->
        <div class="pipeline-card {s2_class}">
            <div class="stage-top">
                <span class="stage-step-lbl">Stage 2 · Obj 1</span>
                {s2_pill}
            </div>
            <div class="stage-body">
                <div class="stage-icon">🧠</div>
                <div>
                    <div class="stage-title">AI Context Extraction</div>
                    <div class="stage-desc">{s2_sub}<br>{s2_note}</div>
                </div>
            </div>
        </div>

        <!-- Connector 2 -> 3 -->
        <div class="pipeline-arrow-slot">
            <div class="connector-line {flow_2_3}">
                {dot_2_3}
            </div>
        </div>

        <!-- Stage 3 -->
        <div class="pipeline-card {s3_class}">
            <div class="stage-top">
                <span class="stage-step-lbl">Stage 3 · Obj 2</span>
                {s3_pill}
            </div>
            <div class="stage-body">
                <div class="stage-icon">🧭</div>
                <div>
                    <div class="stage-title">Workflow Routing</div>
                    <div class="stage-desc">{s3_sub}<br>{s3_note}</div>
                </div>
            </div>
        </div>

        <!-- Connector 3 -> 4 (Dashed - Future Stage Preview) -->
        <div class="pipeline-arrow-slot">
            <div class="connector-line dashed-flow"></div>
        </div>

        <!-- Stage 4 -->
        <div class="pipeline-card {s4_class}">
            <div class="stage-top">
                <span class="stage-step-lbl" style="color: #B45309;">Stage 4 · Phase 2</span>
                {s4_pill}
            </div>
            <div class="stage-body">
                <div class="stage-icon">⚡</div>
                <div>
                    <div class="stage-title" style="color: #64748B;">Knowledge &amp; Dispatch</div>
                    <div class="stage-desc">{s4_sub}<br>{s4_note}</div>
                </div>
            </div>
        </div>
    </div>
    """
    if hasattr(st, "html"):
        st.html(pipeline_html)
    else:
        st.markdown(pipeline_html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 1 — DASHBOARD OVERVIEW (PRIMARY)
# ─────────────────────────────────────────────────────────────────────────────
def screen_dashboard():
    _init_state()
    custom_key = "📝 Custom Request (Paste Any Message)"

    # Page heading
    st.markdown("""
    <div class="pg-hdr">
        <div>
            <div class="pg-title">Support Operations Dashboard</div>
            <div class="pg-sub">AI Customer Support Knowledge Agent &bull; Objectives 1 &amp; 2 Live Implementation</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Summary cards
    render_summary_cards()

    # Main grid: workspace (L) + inbox panel (R)
    col_workspace, col_inbox = st.columns([2.35, 1.0], gap="medium")

    # ── Right: Inbox ──────────────────────────────────────────────────────────
    with col_inbox:
        st.markdown('<div class="wp">', unsafe_allow_html=True)
        render_inbox_panel(custom_key, panel_prefix="dash")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Left: Main Workspace ──────────────────────────────────────────────────
    with col_workspace:
        # Row 1: Request Intake + AI Analysis side by side
        col_intake, col_ai = st.columns([1.05, 1.2], gap="small")

        with col_intake:
            st.markdown('<div class="wp">', unsafe_allow_html=True)
            request_text, source_label = render_request_intake("dash")
            trigger = st.button("⚡ Run Extraction & Routing", key="btn_dash_run", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Run analysis
        if trigger:
            rt = request_text.strip() if request_text else ""
            if not rt:
                st.error("Please enter or select a customer support message.")
            elif len(rt) < 10:
                st.warning("Message too short to extract meaningful context.")
            else:
                with st.spinner("Extracting with Gemini and routing…"):
                    try:
                        active_t_id = SCENARIOS[st.session_state.selected_inbox_key].get('ticket_id') if st.session_state.selected_inbox_key in SCENARIOS else "#CUSTOM-LIVE"
                        res = process_and_route_ticket(rt, source_label=source_label, ticket_id=active_t_id)
                        st.session_state.analysis_cache[st.session_state.selected_inbox_key] = res
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Analysis failed: {exc}")

        current_result = st.session_state.analysis_cache.get(st.session_state.selected_inbox_key)

        with col_ai:
            st.markdown('<div class="wp">', unsafe_allow_html=True)
            st.markdown("""
            <div class="wp-hdr">
                <span class="wp-title">Objective 1: AI Issue Analysis</span>
                <span class="wp-badge green">Gemini 3.5</span>
            </div>
            """, unsafe_allow_html=True)
            render_analysis_result(current_result, show_kb_articles=False)
            st.markdown('</div>', unsafe_allow_html=True)

        # Row 2: Obj 2 Workflow Routing (full width of workspace)
        st.markdown('<div class="wp">', unsafe_allow_html=True)
        st.markdown("""
        <div class="wp-hdr">
            <span class="wp-title">Objective 2: Classification &amp; Workflow Routing</span>
            <span class="wp-badge blue">Rule Engine</span>
        </div>
        """, unsafe_allow_html=True)

        if current_result is None:
            st.caption("Workflow routing displays once the ticket is analyzed above.")
        else:
            c1, c2, c3 = st.columns([1, 2.2, 1])
            with c1:
                st.markdown(f"""
                <div class="pri-box">
                    <div class="afl">Category</div>
                    <div style="margin-top:0.25rem;">{_cat_badge(current_result.category.value)}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="route-box">
                    <div class="route-label">Assigned Team Queue</div>
                    <div class="route-val">{current_result.route}</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                pc = _pri_class(current_result.priority)
                pl = _pri_label(current_result.priority)
                st.markdown(f"""
                <div class="pri-box">
                    <div class="afl">Priority Level</div>
                    <div class="{pc}" style="margin-top:0.25rem;">{pl}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="reason-strip" style="margin-top:0.55rem;">
                <strong>Routing Explanation (Audit Trail):</strong> {current_result.routing_reason}
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="afl">Recommended Operational Actions</div>', unsafe_allow_html=True)
            actions = [
                current_result.suggested_action,
                f"Route ticket to <strong>{current_result.route}</strong> queue.",
                "Update SLA timestamp and trigger customer acknowledgement notification.",
            ]
            rows_html = "".join(
                f'<div class="action-row"><div class="action-num">{i+1}</div><div>{a}</div></div>'
                for i, a in enumerate(actions)
            )
            st.markdown(rows_html, unsafe_allow_html=True)

            # KB articles
            sel_key = st.session_state.selected_inbox_key
            if sel_key in SCENARIOS:
                articles = SCENARIOS[sel_key].get("articles", [])
                if articles:
                    st.markdown('<hr class="thin-divider">', unsafe_allow_html=True)
                    st.markdown('<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.4rem;"><span class="afl" style="margin-bottom:0;">Related Knowledge Base Articles</span><span style="font-size:0.72rem;color:#0066FF;font-weight:700;">Preview</span></div>', unsafe_allow_html=True)
                    kb_html = "".join(f'<div class="kb-row"><span class="kb-icon">📄</span>{a}</div>' for a in articles)
                    st.markdown(kb_html, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ── Full-Width Lower Section: Pipeline + Demonstration Queue ─────────────
    # Row 3: Animated Pipeline Stepper
    st.markdown('<div class="wp">', unsafe_allow_html=True)
    st.markdown("""
    <div class="wp-hdr">
        <div>
            <span class="wp-title">End-to-End Triage Pipeline</span>
            <span style="font-size:0.75rem;color:#64748B;margin-left:0.5rem;">Live Multi-Stage AI Workflow</span>
        </div>
        <span class="wp-badge blue">Real-Time Flow</span>
    </div>
    """, unsafe_allow_html=True)
    sel_sc = SCENARIOS.get(st.session_state.selected_inbox_key)
    render_animated_pipeline(current_result, sel_sc)
    st.markdown('</div>', unsafe_allow_html=True)

    # Row 4: Demo request queue table
    st.markdown('<div class="wp">', unsafe_allow_html=True)
    st.markdown("""
    <div class="wp-hdr">
        <div>
            <span class="wp-title">Demonstration Support Requests Queue</span>
            <span style="font-size:0.75rem;color:#64748B;margin-left:0.5rem;">6 Curated Production-grade Test Scenarios</span>
        </div>
        <span class="wp-badge green">Verified Cases</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display: grid; grid-template-columns: 1.0fr 2.3fr 1.3fr 0.9fr 1.6fr 0.9fr; gap: 0.75rem; padding: 0.55rem 0.85rem; background: #F1F5F9; border-radius: 8px; margin-bottom: 0.6rem; border: 1px solid #E2E8F0;">
        <div style="font-size: 0.75rem; font-weight: 800; color: #1E293B; letter-spacing: 0.05em; text-transform: uppercase;">Ticket ID</div>
        <div style="font-size: 0.75rem; font-weight: 800; color: #1E293B; letter-spacing: 0.05em; text-transform: uppercase;">Subject &amp; Customer</div>
        <div style="font-size: 0.75rem; font-weight: 800; color: #1E293B; letter-spacing: 0.05em; text-transform: uppercase;">Category</div>
        <div style="font-size: 0.75rem; font-weight: 800; color: #1E293B; letter-spacing: 0.05em; text-transform: uppercase;">Priority</div>
        <div style="font-size: 0.75rem; font-weight: 800; color: #1E293B; letter-spacing: 0.05em; text-transform: uppercase;">Lifecycle Progress</div>
        <div style="font-size: 0.75rem; font-weight: 800; color: #1E293B; letter-spacing: 0.05em; text-transform: uppercase; text-align: right;">Action</div>
    </div>
    """, unsafe_allow_html=True)

    for k, sc in SCENARIOS.items():
        rcols = st.columns([1.0, 2.3, 1.3, 0.9, 1.6, 0.9])
        t_id = sc.get('ticket_id', '')
        tk_info = get_ticket(t_id)
        tk_stage = tk_info["stage"]
        tk_prog = tk_info["progress"]
        tk_badge_cls = STAGE_BADGE_CLASSES.get(normalize_stage(tk_stage), "stage-badge-received")

        with rcols[0]:
            st.markdown(f"<div style='font-size: 0.88rem; font-weight: 700; color: #0F172A; padding-top: 0.4rem;'>{t_id}</div>", unsafe_allow_html=True)
        with rcols[1]:
            st.markdown(
                f"<div style='padding-top: 0.15rem;'>"
                f"<div style='font-size: 0.88rem; font-weight: 600; color: #0F172A;'>{sc.get('subject','')}</div>"
                f"<div style='font-size: 0.78rem; font-weight: 500; color: #475569;'>👤 {sc.get('sender_name','')} &bull; <span style='color: #64748B;'>{sc.get('timestamp','')}</span></div>"
                f"</div>",
                unsafe_allow_html=True
            )
        with rcols[2]:
            st.markdown(f"<div style='padding-top: 0.35rem;'>{_cat_badge(sc['category'])}</div>", unsafe_allow_html=True)
        with rcols[3]:
            cat_c = sc["category"].lower()
            if "billing" in cat_c or "api" in cat_c or "account" in cat_c:
                phtml = "<div style='padding-top: 0.4rem;'><span style='background: #FEE2E2; color: #991B1B; font-weight: 800; font-size: 0.76rem; padding: 0.2rem 0.55rem; border-radius: 4px; border: 1px solid #FECACA;'>HIGH</span></div>"
            elif "export" in cat_c or "unclear" in cat_c:
                phtml = "<div style='padding-top: 0.4rem;'><span style='background: #FEF3C7; color: #92400E; font-weight: 800; font-size: 0.76rem; padding: 0.2rem 0.55rem; border-radius: 4px; border: 1px solid #FDE68A;'>MEDIUM</span></div>"
            else:
                phtml = "<div style='padding-top: 0.4rem;'><span style='background: #DCFCE7; color: #166534; font-weight: 800; font-size: 0.76rem; padding: 0.2rem 0.55rem; border-radius: 4px; border: 1px solid #BBF7D0;'>LOW</span></div>"
            st.markdown(phtml, unsafe_allow_html=True)
        with rcols[4]:
            st.markdown(
                f"<div class='table-pbar-wrap' style='padding-top:0.25rem;'>"
                f"  <div class='table-pbar-lbl'>"
                f"    <span class='stage-badge-mini {tk_badge_cls}'>● {tk_stage}</span>"
                f"    <span style='color:#0F172A;font-size:0.72rem;font-weight:700;'>{tk_prog}%</span>"
                f"  </div>"
                f"  <div class='card-pbar-bg' style='margin-top:0.2rem;height:5px;'>"
                f"    <div class='card-pbar-fill' style='width:{tk_prog}%;'></div>"
                f"  </div>"
                f"</div>",
                unsafe_allow_html=True
            )
        with rcols[5]:
            if st.button("Inspect", key=f"tbl_{sc.get('ticket_id')}", use_container_width=True):
                st.session_state.selected_inbox_key = k
                st.rerun()
        st.markdown("<div style='border-bottom: 1px solid #F1F5F9; margin: 0.25rem 0;'></div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 2 — DEDICATED INBOX TRIAGE (3-column: inbox | conversation | analysis)
# ─────────────────────────────────────────────────────────────────────────────
def screen_inbox():
    _init_state()
    custom_key = "📝 Custom Request (Paste Any Message)"

    st.markdown('<div class="pg-title" style="margin-bottom:0.85rem;">📥 Support Inbox</div>', unsafe_allow_html=True)

    col_list, col_convo, col_analysis = st.columns([1.05, 1.85, 1.6], gap="small")

    with col_list:
        st.markdown('<div class="wp">', unsafe_allow_html=True)
        render_inbox_panel(custom_key, panel_prefix="inbox")
        st.markdown('</div>', unsafe_allow_html=True)

    selected_key = st.session_state.selected_inbox_key
    current_result = st.session_state.analysis_cache.get(selected_key)

    with col_convo:
        st.markdown('<div class="wp">', unsafe_allow_html=True)
        active_t_id = SCENARIOS[selected_key].get('ticket_id') if selected_key in SCENARIOS else "#CUSTOM-LIVE"
        tk_data = get_ticket(active_t_id)

        # Per-complaint lifecycle progress stepper & demo controls
        render_complaint_stepper(tk_data)
        render_ticket_status_controls(active_t_id, tk_data["stage"], panel_prefix="inbox_convo")
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

        if selected_key != custom_key:
            sc = SCENARIOS[selected_key]
            badge = _cat_badge(sc["category"])
            st.markdown(f"""
            <div class="wp-hdr">
                <div>
                    <span class="wp-title">{sc.get('subject','')}</span>
                    <span style="font-size:0.74rem;color:#64748B;margin-left:0.4rem;">{sc.get('ticket_id','')}</span>
                </div>
                {badge}
            </div>
            <div class="cust-strip">
                <div class="inbox-avatar" style="background:{sc.get('avatar_color','#3B82F6')};width:26px;height:26px;font-size:0.7rem;">
                    {sc.get('avatar_initials','?')}
                </div>
                <div>
                    <span class="cust-name">{sc.get('sender_name','')}</span>
                    &nbsp;<span class="cust-email">&lt;{sc.get('sender_email','')}&gt;</span>
                </div>
                <span class="cust-plan">Plan: {sc.get('customer_plan','—')}&nbsp;·&nbsp;Since {sc.get('customer_since','—')}</span>
            </div>
            """, unsafe_allow_html=True)
            request_text = st.text_area(
                "Message:",
                value=sc["content"],
                height=240,
                key=f"inbox_msg_{selected_key}",
                label_visibility="collapsed",
            )
            if sc.get("attachment"):
                st.markdown(f"""
                <div class="attach-strip">📎 <strong>{sc['attachment']}</strong>&nbsp;<span style="color:#94A3B8;">(Demo attachment)</span></div>
                """, unsafe_allow_html=True)
            source_label = f"Ticket: {sc.get('ticket_id','')}"
        else:
            st.markdown("""
            <div class="wp-hdr">
                <span class="wp-title">Custom Support Request</span>
                <span class="badge review">Manual</span>
            </div>
            """, unsafe_allow_html=True)
            request_text = st.text_area(
                "Paste message:",
                value="",
                placeholder="From: …\nSubject: …\n\nMessage body…",
                height=255,
                key="inbox_custom_msg",
                label_visibility="collapsed",
            )
            source_label = "Custom Pasted Input"

        run_btn = st.button("⚡ Run AI Extraction & Workflow Route", key="btn_inbox_run", type="primary", use_container_width=True)
        if run_btn:
            rt = request_text.strip() if request_text else ""
            if not rt:
                st.error("Please enter or select a customer support message.")
            elif len(rt) < 10:
                st.warning("Message too short to extract meaningful context.")
            else:
                with st.spinner("Extracting with Gemini and routing…"):
                    try:
                        res = process_and_route_ticket(rt, source_label=source_label, ticket_id=active_t_id)
                        st.session_state.analysis_cache[selected_key] = res
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Analysis failed: {exc}")

        # Action bar (preview)
        st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)
        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            if st.button("↩ Reply", key="inbox_reply", use_container_width=True):
                st.toast("ℹ️ Preview (Obj 4): Outbound email dispatch — Phase 2.", icon="ℹ️")
        with ac2:
            if st.button("↩ Reply All", key="inbox_replyall", use_container_width=True):
                st.toast("ℹ️ Preview (Obj 4): Outbound dispatch — Phase 2.", icon="ℹ️")
        with ac3:
            if st.button("↪ Forward", key="inbox_fwd", use_container_width=True):
                st.toast("ℹ️ Preview (Obj 4): Forwarding — Phase 2.", icon="ℹ️")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_analysis:
        st.markdown('<div class="wp">', unsafe_allow_html=True)
        st.markdown("""
        <div class="wp-hdr">
            <span class="wp-title">AI Analysis &amp; Routing</span>
            <span class="wp-badge green">Obj 1 &amp; 2</span>
        </div>
        """, unsafe_allow_html=True)

        if current_result is None:
            st.info("👈 Select a ticket and click **Run AI Extraction & Workflow Route** to analyze.")
        else:
            render_analysis_result(current_result, show_kb_articles=True)

        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 3 — WORKFLOW ROUTING (Obj 2 explainer + live run)
# ─────────────────────────────────────────────────────────────────────────────
def screen_workflow_routing():
    _init_state()
    st.markdown('<div class="pg-title" style="margin-bottom:0.85rem;">🧭 Workflow Routing — Objective 2</div>', unsafe_allow_html=True)

    ROUTES = [
        ("Billing/Payments", "Finance & Billing Operations", "High", ["billing", "invoice", "charge", "refund", "subscription"]),
        ("Account/Login", "Identity & Access Management (IAM)", "High", ["login", "password", "locked", "2fa", "mfa", "sso"]),
        ("API/Technical", "Developer Support & Tier-2 Engineering", "High", ["api", "401", "500", "token", "endpoint", "sdk"]),
        ("Product/Export", "Product Operations Desk", "Medium", ["export", "csv", "download", "truncated", "report"]),
        ("Feature Request", "Product Management Backlog", "Low", ["feature", "dark mode", "webhook", "roadmap"]),
        ("Unclear/Human Review", "Tier-1 Triage & Manual Clarification", "Medium", ["(vague or insufficient input)"]),
    ]

    st.markdown('<div class="wp">', unsafe_allow_html=True)
    st.markdown("**Six deterministic routing categories — keyword signal matching with explicit audit trail.**")
    st.markdown("<br>", unsafe_allow_html=True)

    for cat, route, pri, signals in ROUTES:
        pc = "pri-high" if pri == "High" else "pri-medium" if pri == "Medium" else "pri-low"
        st.markdown(f"""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:9px;padding:0.75rem 1rem;margin-bottom:0.6rem;display:flex;align-items:flex-start;gap:1rem;">
            <div style="flex-shrink:0;width:130px;">
                {_cat_badge(cat)}
                <div class="{pc}" style="margin-top:0.3rem;">{pri.upper()}</div>
            </div>
            <div style="flex:1;">
                <div style="font-weight:700;font-size:0.88rem;color:#0F172A;margin-bottom:0.2rem;">{route}</div>
                <div style="font-size:0.78rem;color:#64748B;">Signals: <code>{'</code>, <code>'.join(signals)}</code></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 5 — TICKETS QUEUE
# ─────────────────────────────────────────────────────────────────────────────
def screen_tickets():
    st.markdown('<div class="pg-title" style="margin-bottom:0.85rem;">🎫 Tickets Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="wp">', unsafe_allow_html=True)
    st.caption("All 6 curated test tickets tracked across support categories and operational priority levels.")

    st.markdown("""
    <div style="display: grid; grid-template-columns: 1.0fr 2.4fr 1.3fr 1.8fr 0.9fr; gap: 0.75rem; padding: 0.55rem 0.85rem; background: #F1F5F9; border-radius: 8px; margin-bottom: 0.6rem; border: 1px solid #E2E8F0;">
        <div style="font-size: 0.75rem; font-weight: 800; color: #1E293B; letter-spacing: 0.05em; text-transform: uppercase;">Ticket ID</div>
        <div style="font-size: 0.75rem; font-weight: 800; color: #1E293B; letter-spacing: 0.05em; text-transform: uppercase;">Subject &amp; Customer</div>
        <div style="font-size: 0.75rem; font-weight: 800; color: #1E293B; letter-spacing: 0.05em; text-transform: uppercase;">Category</div>
        <div style="font-size: 0.75rem; font-weight: 800; color: #1E293B; letter-spacing: 0.05em; text-transform: uppercase;">Lifecycle Progress</div>
        <div style="font-size: 0.75rem; font-weight: 800; color: #1E293B; letter-spacing: 0.05em; text-transform: uppercase; text-align: right;">Action</div>
    </div>
    """, unsafe_allow_html=True)

    for k, sc in SCENARIOS.items():
        rcols = st.columns([1.0, 2.4, 1.3, 1.8, 0.9])
        t_id = sc.get('ticket_id', '')
        tk_info = get_ticket(t_id)
        tk_stage = tk_info["stage"]
        tk_prog = tk_info["progress"]
        tk_badge_cls = STAGE_BADGE_CLASSES.get(normalize_stage(tk_stage), "stage-badge-received")

        with rcols[0]:
            st.markdown(f"<div style='font-size:0.88rem; font-weight:700; color:#0F172A; padding-top:0.4rem;'>{t_id}</div><div style='font-size:0.74rem;color:#64748B;'>{sc.get('timestamp','')}</div>", unsafe_allow_html=True)
        with rcols[1]:
            st.markdown(f"<div style='font-size:0.88rem; font-weight:600; color:#0F172A; padding-top:0.15rem;'>{sc.get('subject','')}</div><div style='font-size:0.78rem; font-weight:500; color:#475569;'>👤 {sc.get('sender_name','')}</div>", unsafe_allow_html=True)
        with rcols[2]:
            st.markdown(f"<div style='padding-top:0.35rem;'>{_cat_badge(sc['category'])}</div>", unsafe_allow_html=True)
        with rcols[3]:
            st.markdown(
                f"<div class='table-pbar-wrap' style='padding-top:0.25rem;'>"
                f"  <div class='table-pbar-lbl'>"
                f"    <span class='stage-badge-mini {tk_badge_cls}'>● {tk_stage}</span>"
                f"    <span style='color:#0F172A;font-size:0.72rem;font-weight:700;'>{tk_prog}%</span>"
                f"  </div>"
                f"  <div class='card-pbar-bg' style='margin-top:0.2rem;height:5px;'>"
                f"    <div class='card-pbar-fill' style='width:{tk_prog}%;'></div>"
                f"  </div>"
                f"</div>",
                unsafe_allow_html=True
            )
        with rcols[4]:
            if st.button("Open", key=f"tkt_{sc.get('ticket_id')}", use_container_width=True):
                st.session_state.selected_inbox_key = k
                st.session_state.current_nav = "📥  Support Inbox"
                st.rerun()
        st.markdown("<div style='border-bottom: 1px solid #F1F5F9; margin: 0.25rem 0;'></div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 6 — KNOWLEDGE BASE (Obj 3 Preview)
# ─────────────────────────────────────────────────────────────────────────────
def screen_knowledge_base():
    st.markdown('<div class="pg-title" style="margin-bottom:0.85rem;">📚 Knowledge Base</div>', unsafe_allow_html=True)
    st.markdown('<div class="wp">', unsafe_allow_html=True)
    st.info("ℹ️ **Objective 3 Preview Mode**: This knowledge base will be embedded and queried via RAG vector search in Phase 2 to automatically synthesize verified support responses.")

    articles = [
        ("Handling Duplicate Subscription Charges", "Billing & Payments",
         "Step-by-step resolution for double billing, pre-auth holds, and payment gateway ledger adjustments."),
        ("Resolving 401 Unauthorized API Authentication Failures", "API & Technical",
         "Root cause checklist for expired bearer tokens, invalid scopes, and API gateway migration changes."),
        ("Emergency Two-Factor Authentication (2FA) Recovery", "Account / Login",
         "Identity verification protocol for users who lost authenticator hardware or mobile phones."),
        ("CSV Export Truncation & Pagination Limits", "Product / Export",
         "Troubleshooting large table exports that truncate at 50 rows via pagination worker bugs."),
        ("Product Roadmap Submission Process", "Feature Requests",
         "How feature suggestions and API webhook enhancement tickets are triaged into engineering sprints."),
        ("Customer Clarification Guidelines & Templates", "Unclear / Human Review",
         "Standard templates for requesting reproduction steps, error logs, and diagnostic information."),
    ]

    for title, cat, desc in articles:
        st.markdown(f"""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.6rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.25rem;">
                <span style="font-size:0.92rem;font-weight:700;color:#0066FF;">📄 {title}</span>
                {_cat_badge(cat)}
            </div>
            <div style="font-size:0.82rem;color:#475569;line-height:1.45;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 7 — CUSTOMERS
# ─────────────────────────────────────────────────────────────────────────────
def screen_customers():
    st.markdown('<div class="pg-title" style="margin-bottom:0.85rem;">👥 Customer Directory</div>', unsafe_allow_html=True)
    st.markdown('<div class="wp">', unsafe_allow_html=True)
    st.caption("Demonstration customer profiles linked to active support tickets.")
    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2, gap="medium")
    for idx, (k, sc) in enumerate(SCENARIOS.items()):
        col = col_a if idx % 2 == 0 else col_b
        t_id = sc.get('ticket_id', '')
        tk_info = get_ticket(t_id)
        tk_stage = tk_info["stage"]
        tk_prog = tk_info["progress"]
        tk_badge_cls = STAGE_BADGE_CLASSES.get(normalize_stage(tk_stage), "stage-badge-received")
        with col:
            st.markdown(f"""
            <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:9px;padding:0.85rem;margin-bottom:0.7rem;">
                <div style="display:flex;align-items:center;gap:0.65rem;margin-bottom:0.4rem;">
                    <div class="inbox-avatar" style="background:{sc.get('avatar_color','#3B82F6')};width:36px;height:36px;font-size:0.82rem;flex-shrink:0;">
                        {sc.get('avatar_initials','?')}
                    </div>
                    <div>
                        <div style="font-weight:700;font-size:0.95rem;color:#0F172A;">{sc.get('sender_name','')}</div>
                        <div style="font-size:0.78rem;color:#64748B;">{sc.get('sender_email','')}</div>
                    </div>
                </div>
                <div style="font-size:0.82rem;color:#334155;line-height:1.55;">
                    <div><strong>Plan:</strong> {sc.get('customer_plan','—')}</div>
                    <div><strong>Customer Since:</strong> {sc.get('customer_since','—')}</div>
                    <div><strong>Active Ticket:</strong> {t_id} &bull; {sc.get('subject','')}</div>
                    <div style="margin-top:0.35rem;display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap;">
                        {_cat_badge(sc['category'])}
                        <span class="stage-badge-mini {tk_badge_cls}">● {tk_stage} ({tk_prog}%)</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 8 — AUTOMATIONS (Obj 4 Preview)
# ─────────────────────────────────────────────────────────────────────────────
def screen_automations():
    st.markdown('<div class="pg-title" style="margin-bottom:0.85rem;">⚡ Automations</div>', unsafe_allow_html=True)
    st.markdown('<div class="wp">', unsafe_allow_html=True)
    st.info("ℹ️ **Objective 4 Preview Mode**: External action dispatches (Jira sync, webhook escalation, email auto-reply) are scheduled for Phase 2.")

    rules = [
        ("Rule #1: High-Priority API Incident Alert",
         "Category == API/Technical AND Priority == High",
         "Alert Developer Support On-Call via webhook notification"),
        ("Rule #2: Duplicate Charge Ledger Audit",
         "Category == Billing/Payments AND 'duplicate' in issue",
         "Fetch gateway transactions and attach bank statement to ticket"),
        ("Rule #3: Locked Account 2FA Reset Escalation",
         "Category == Account/Login AND 'locked' in context",
         "Trigger identity verification SMS and unlock account workflow"),
        ("Rule #4: Feature Request Backlog Logger",
         "Category == Feature Request",
         "Append to product roadmap backlog and tag relevant persona"),
        ("Rule #5: Vague Input Human Clarification",
         "Category == Unclear/Human Review",
         "Route to Tier-1 agent and dispatch clarification questionnaire"),
    ]

    for title, trigger, action in rules:
        st.markdown(f"""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:9px;padding:0.85rem 1rem;margin-bottom:0.6rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.3rem;">
                <strong style="font-size:0.92rem;color:#0F172A;">{title}</strong>
                <span style="font-size:0.72rem;background:#FEF3C7;color:#92400E;padding:0.15rem 0.5rem;border-radius:4px;font-weight:700;">Preview</span>
            </div>
            <div style="font-size:0.8rem;color:#475569;"><strong>Trigger:</strong> <code>{trigger}</code></div>
            <div style="font-size:0.8rem;color:#475569;"><strong>Action:</strong> {action}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 9 — ANALYTICS (Illustrative)
# ─────────────────────────────────────────────────────────────────────────────
def screen_analytics():
    st.markdown('<div class="pg-title" style="margin-bottom:0.85rem;">📈 Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="wp">', unsafe_allow_html=True)
    st.caption("Illustrative operational metrics demonstrating triage distribution across categories.")

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Ingested Tickets", "142", delta="+18 today")
    with c2: st.metric("Auto Route Rate", "91.5 %", delta="+2.1 %")
    with c3: st.metric("Human Clarification", "8.5 %", delta="Target < 10 %")
    with c4: st.metric("Avg Triage Latency", "1.8 s", delta="-0.4 s")

    st.markdown("---")
    st.markdown("#### Ticket Distribution by Category (Illustrative)")
    st.bar_chart({
        "Billing/Payments": 36,
        "API/Technical": 28,
        "Account/Login": 18,
        "Product/Export": 10,
        "Feature Request": 5,
        "Unclear/Human Review": 3,
    })
    st.caption("⚠️ Illustrative sample data — not derived from production telemetry.")
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 10 — SETTINGS & API
# ─────────────────────────────────────────────────────────────────────────────
def screen_settings(gmail_info: dict):
    st.markdown('<div class="pg-title" style="margin-bottom:0.85rem;">⚙️ Settings & API</div>', unsafe_allow_html=True)
    st.markdown('<div class="wp">', unsafe_allow_html=True)

    st.markdown("#### LLM Configuration")
    st.markdown(f"""
    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:7px;padding:0.8rem 1rem;margin-bottom:1rem;font-size:0.86rem;line-height:1.65;">
        <div><strong>Active Model:</strong> <code>gemini-3.5-flash-lite</code></div>
        <div><strong>SDK:</strong> google-genai v2.25.0 — <code>client.interactions.create</code></div>
        <div><strong>API Key:</strong> <span style="color:#10B981;font-weight:700;">Configured via .env (GEMINI_API_KEY)</span></div>
        <div><strong>Output Schema:</strong> Pydantic <code>IssueAnalysis</code> → <code>RoutedSupportRequest</code></div>
        <div><strong>Timeout:</strong> 30 s with graceful error display</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Gmail API Intake Service")
    st.markdown(f"""
    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:7px;padding:0.8rem 1rem;margin-bottom:1rem;font-size:0.86rem;line-height:1.65;">
        <div><strong>Status:</strong> <span style="color:#D97706;font-weight:700;">{gmail_info.get('mode','Fallback Mode')}</span></div>
        <div><strong>Reason:</strong> {gmail_info.get('reason','credentials.json not present')}</div>
        <div><strong>OAuth Scope:</strong> <code>https://www.googleapis.com/auth/gmail.readonly</code></div>
        <div><strong>Fallback:</strong> Manual / sample intake fully operational — Objectives 1 &amp; 2 unaffected.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Test Coverage")
    st.markdown("""
    <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:7px;padding:0.75rem 1rem;font-size:0.86rem;line-height:1.65;">
        <div><strong>Test Suite:</strong> <code>tests/test_pipeline.py</code></div>
        <div><strong>Tests:</strong> 16 passing — ConversationManager, EmailProcessor, PreprocessInput,
             WorkflowRouter (6 categories), InputValidation, GmailServiceFallback</div>
        <div><strong>Command:</strong> <code>python -m unittest discover tests</code></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN APPLICATION ROUTER
# ─────────────────────────────────────────────────────────────────────────────
def main():
    gmail_info = get_gmail_status()
    nav = render_sidebar(gmail_info)
    render_topbar()

    if "Dashboard" in nav:
        screen_dashboard()
    elif "Inbox" in nav:
        screen_inbox()
    elif "Workflow Routing" in nav:
        screen_workflow_routing()
    elif "Tickets" in nav:
        screen_tickets()
    elif "Knowledge" in nav:
        screen_knowledge_base()
    elif "Customers" in nav:
        screen_customers()
    elif "Automations" in nav:
        screen_automations()
    elif "Analytics" in nav:
        screen_analytics()
    elif "Settings" in nav:
        screen_settings(gmail_info)


if __name__ == "__main__":
    main()
