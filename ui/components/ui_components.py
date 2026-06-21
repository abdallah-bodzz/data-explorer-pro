# ui_components.py
"""UI Components, CSS styles, and HTML templates for Data Explorer Pro
Premium glass morphism design with elegant, slow transitions
"""

import streamlit as st
import time
from typing import Optional, Dict, Any, List
import hashlib

# ============================================================================
# CSS STYLES - SOPHISTICATED ELEGANCE WITH SLOW TRANSITIONS
# ============================================================================

CSS_STYLES = """<style>
/* ===== CSS VARIABLES - REFINED PALETTE ===== */
:root {
    --primary: #5575ff;
    --primary-hover: #6a88ff;
    --primary-muted: #3d5cd9;
    --accent-success: #4ade80;
    --accent-warning: #fb923c;
    --accent-error: #ef4444;
    --accent-info: #60a5fa;
    
    --bg: #0B0B14;
    --secondary-bg: #16162A;
    --text: #E8EDF4;
    --text-secondary: #9BA3B4;
    --text-tertiary: rgba(232, 237, 244, 0.6);
    
    --glass-bg: rgba(22, 22, 42, 0.65);
    --glass-border: rgba(85, 117, 255, 0.12);
    --glass-highlight: rgba(255, 255, 255, 0.06);
    
    /* Refined transitions */
    --transition-elegant: cubic-bezier(0.42, 0, 0.05, 0.99);
    --transition-smooth: cubic-bezier(0.4, 0, 0.2, 1);
    --transition-flow: cubic-bezier(0.25, 0.46, 0.45, 0.94);
    --transition-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
    --transition-snap: cubic-bezier(0.85, 0, 0.15, 1);
    --transition-butter: cubic-bezier(0.33, 1, 0.68, 1);
    
    /* Duration standards */
    --duration-instant: 150ms;
    --duration-fast: 250ms;
    --duration-base: 350ms;
    --duration-slow: 500ms;
    --duration-leisurely: 700ms;
    
    /* Shadows hierarchy */
    --shadow-soft: 0 8px 40px rgba(0, 0, 0, 0.15);
    --shadow-subtle: 0 4px 24px rgba(0, 0, 0, 0.08);
    --shadow-elevated: 0 12px 56px rgba(0, 0, 0, 0.22);
    --shadow-glow: 0 0 60px rgba(85, 117, 255, 0.05);
    --shadow-glow-hover: 0 0 80px rgba(106, 136, 255, 0.08);
    
    --radius-large: 16px;
    --radius-medium: 12px;
    --radius-small: 8px;
}

/* ===== ELEGANT ANIMATIONS - SMOOTH & SLOW ===== */
@keyframes soft-fade-in {
    from { 
        opacity: 0; 
        transform: translateY(6px) scale(0.995);
        filter: blur(2px);
    }
    to { 
        opacity: 1; 
        transform: translateY(0) scale(1);
        filter: blur(0);
    }
}

@keyframes gentle-shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}

@keyframes subtle-pulse {
    0%, 100% { 
        box-shadow: var(--shadow-soft), 0 0 0 0 rgba(85, 117, 255, 0.04); 
        transform: scale(1);
    }
    50% { 
        box-shadow: var(--shadow-soft), 0 0 0 3px rgba(85, 117, 255, 0.08);
        transform: scale(1.001);
    }
}

@keyframes elegant-float {
    0%, 100% { 
        transform: translateY(0) rotate(0deg); 
    }
    33% { 
        transform: translateY(-1px) rotate(0.2deg); 
    }
    66% { 
        transform: translateY(0.5px) rotate(-0.1deg); 
    }
}

@keyframes light-streak-gentle {
    0% { 
        transform: translateX(-100%) skewX(-12deg); 
        opacity: 0; 
    }
    20%, 80% { 
        opacity: 0.2; 
    }
    100% { 
        transform: translateX(200%) skewX(-12deg); 
        opacity: 0; 
    }
}

@keyframes border-glow {
    0%, 100% { 
        border-color: rgba(85, 117, 255, 0.12); 
        box-shadow: 0 0 0 0 rgba(85, 117, 255, 0); 
    }
    50% { 
        border-color: rgba(85, 117, 255, 0.2); 
        box-shadow: 0 0 0 1px rgba(85, 117, 255, 0.05); 
    }
}

@keyframes content-reveal {
    from { 
        clip-path: inset(0 0 100% 0);
        opacity: 0.8;
    }
    to { 
        clip-path: inset(0 0 0 0);
        opacity: 1;
    }
}

@keyframes tab-text-glow {
    0%, 100% { 
        text-shadow: 0 0 0 rgba(85, 117, 255, 0); 
    }
    50% { 
        text-shadow: 0 0 8px rgba(85, 117, 255, 0.3); 
    }
}

@keyframes tab-switch {
    0% { 
        opacity: 0.8;
        transform: translateY(2px);
    }
    100% { 
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes success-pulse {
    0%, 100% { 
        box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); 
    }
    50% { 
        box-shadow: 0 0 0 3px rgba(74, 222, 128, 0.15); 
    }
}

@keyframes warning-pulse {
    0%, 100% { 
        box-shadow: 0 0 0 0 rgba(251, 146, 60, 0); 
    }
    50% { 
        box-shadow: 0 0 0 3px rgba(251, 146, 60, 0.15); 
    }
}

/* ===== RESET & ACCESSIBILITY ===== */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}

/* ===== LAYOUT & CONTAINERS - ELEGANT ENTRANCE ===== */
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 1.5rem;
    animation: soft-fade-in 1.2s var(--transition-elegant);
}

.element-container {
    animation: soft-fade-in 0.8s var(--transition-elegant) forwards;
    opacity: 0;
    will-change: transform, opacity;
}

.element-container:nth-child(1) { animation-delay: 0.06s; }
.element-container:nth-child(2) { animation-delay: 0.12s; }
.element-container:nth-child(3) { animation-delay: 0.18s; }
.element-container:nth-child(4) { animation-delay: 0.24s; }

/* ===== SIDEBAR - PREMIUM GLASS WITH ROUNDED CORNERS ===== */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, var(--bg) 0%, var(--secondary-bg) 100%) !important;
    backdrop-filter: blur(30px) saturate(200%);
    border-right: 1px solid var(--glass-border);
    border-radius: 0 var(--radius-large) var(--radius-large) 0;
}

[data-testid="stSidebar"] .element-container {
    animation: soft-fade-in 0.9s var(--transition-elegant) forwards;
    animation-delay: 0.1s;
}

[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stExpander label,
[data-testid="stSidebar"] .stCheckbox label,
[data-testid="stSidebar"] .stRadio label {
    color: rgba(232, 237, 244, 0.95) !important;
    transition: color var(--duration-fast) var(--transition-smooth);
}

/* ===== SIDEBAR SPECIFIC COMPONENTS - ELEGANT GLASS ===== */
.sidebar-glass-card {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(25px) saturate(180%);
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-medium) !important;
    box-shadow: var(--shadow-soft);
    position: relative;
    overflow: hidden;
    transition: 
        transform var(--duration-base) var(--transition-smooth),
        box-shadow var(--duration-base) var(--transition-elegant),
        border-color var(--duration-fast) var(--transition-flow),
        background-color var(--duration-fast) var(--transition-flow);
    will-change: transform, box-shadow, border-color;
}

.sidebar-glass-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 50%;
    height: 100%;
    background: linear-gradient(
        90deg,
        transparent,
        var(--glass-highlight),
        transparent
    );
    transform: skewX(-12deg);
    opacity: 0;
}

.sidebar-glass-card:hover {
    border-color: rgba(106, 136, 255, 0.18) !important;
    transform: translateY(-1px);
    box-shadow: var(--shadow-elevated), var(--shadow-glow-hover);
    animation: subtle-pulse 4s var(--transition-smooth) infinite;
}

.sidebar-glass-card:hover::before {
    animation: light-streak-gentle 1.8s var(--transition-elegant);
    opacity: 0.2;
}

/* ===== BUTTONS - ELEGANT DEPTH ===== */
.stButton > button {
    background: rgba(85, 117, 255, 0.08) !important;
    border: 1px solid rgba(85, 117, 255, 0.15) !important;
    color: var(--text) !important;
    border-radius: var(--radius-small);
    transition: 
        background-color var(--duration-fast) var(--transition-flow),
        border-color var(--duration-fast) var(--transition-flow),
        transform var(--duration-base) var(--transition-bounce),
        box-shadow var(--duration-base) var(--transition-elegant) !important;
    position: relative;
    overflow: hidden;
    font-weight: 500;
    letter-spacing: 0.01em;
    padding: 0.5rem 1rem;
}

.stButton > button:hover:not(:disabled) {
    background: rgba(106, 136, 255, 0.12) !important;
    border-color: rgba(106, 136, 255, 0.25) !important;
    transform: translateY(-0.5px);
    box-shadow: var(--shadow-subtle);
}

.stButton > button:active:not(:disabled) {
    transform: translateY(0);
    transition-duration: var(--duration-instant);
}

.stButton > button::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 40%;
    height: 100%;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.08),
        transparent
    );
    transform: skewX(-15deg);
    transition: left var(--duration-leisurely) var(--transition-elegant);
}

.stButton > button:hover::after {
    left: 150%;
}

/* Primary button variant */
.stButton > button[type="primary"] {
    background: linear-gradient(
        135deg,
        rgba(85, 117, 255, 0.15),
        rgba(85, 117, 255, 0.08)
    ) !important;
    border-color: rgba(85, 117, 255, 0.25) !important;
}

/* ===== TABS - PREMIUM GLASS TABS WITH ELEGANT DETAILS ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    padding: 0.5rem;
    background: rgba(22, 22, 42, 0.25);
    backdrop-filter: blur(20px) saturate(180%);
    border-radius: var(--radius-medium);
    border: 1px solid var(--glass-border);
    box-shadow: 
        inset 0 1px 0 rgba(255, 255, 255, 0.05),
        0 4px 20px rgba(0, 0, 0, 0.1);
    margin-bottom: 1.5rem;
}

.stTabs [data-baseweb="tab"] {
    position: relative;
    overflow: hidden;
    transition: 
        background-color var(--duration-fast) var(--transition-flow),
        color var(--duration-fast) var(--transition-smooth),
        transform var(--duration-base) var(--transition-bounce),
        border-color var(--duration-fast) var(--transition-flow);
    border-radius: var(--radius-small);
    margin: 0;
    padding: 0.7rem 1.4rem;
    font-weight: 500;
    color: rgba(232, 237, 244, 0.65) !important;
    border: 1px solid transparent;
    background: transparent;
    letter-spacing: 0.01em;
    font-size: 0.9rem;
    white-space: nowrap;
}

.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
    background: rgba(106, 136, 255, 0.07) !important;
    color: rgba(232, 237, 244, 0.95) !important;
    transform: translateY(-1px);
    border-color: rgba(106, 136, 255, 0.15);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(
        135deg,
        rgba(106, 136, 255, 0.18),
        rgba(85, 117, 255, 0.09)
    ) !important;
    background-size: 200% auto !important;
    animation: gentle-shimmer 6s linear infinite !important;
    border: 1px solid rgba(106, 136, 255, 0.25) !important;
    color: var(--text) !important;
    font-weight: 600;
    box-shadow: 
        0 2px 12px rgba(106, 136, 255, 0.15),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    position: relative;
    transform: translateY(-0.5px);
    letter-spacing: 0.02em;
}

/* Selected tab glowing border effect */
.stTabs [aria-selected="true"]::before {
    content: '';
    position: absolute;
    inset: -1px;
    border-radius: calc(var(--radius-small) + 1px);
    background: linear-gradient(
        135deg,
        rgba(106, 136, 255, 0.4),
        rgba(85, 117, 255, 0.2),
        rgba(106, 136, 255, 0.4)
    );
    z-index: -1;
    animation: border-glow 3s var(--transition-elegant) infinite;
}

/* Selected tab bottom indicator */
.stTabs [aria-selected="true"]::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 20%;
    right: 20%;
    height: 3px;
    background: linear-gradient(90deg, 
        transparent, 
        var(--primary-hover), 
        transparent
    );
    border-radius: 2px;
    animation: soft-fade-in var(--duration-slow) var(--transition-elegant);
    box-shadow: 
        0 0 10px rgba(106, 136, 255, 0.4),
        0 0 20px rgba(106, 136, 255, 0.2);
    filter: blur(0.5px);
}

/* Tab icon enhancement */
.stTabs [data-baseweb="tab"] strong {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    transition: all var(--duration-base) var(--transition-smooth);
}

.stTabs [data-baseweb="tab"] strong::before {
    content: attr(data-icon);
    font-size: 1.1em;
    opacity: 0.7;
    transition: 
        opacity var(--duration-fast) var(--transition-smooth),
        transform var(--duration-base) var(--transition-bounce);
}

.stTabs [data-baseweb="tab"]:hover strong::before {
    opacity: 0.9;
    transform: scale(1.1) rotate(5deg);
    filter: drop-shadow(0 0 4px rgba(106, 136, 255, 0.3));
}

.stTabs [aria-selected="true"] strong::before {
    opacity: 1;
    transform: scale(1.15);
    filter: drop-shadow(0 0 6px rgba(106, 136, 255, 0.4));
    animation: elegant-float 3s var(--transition-smooth) infinite;
}

/* Tab hover border animation */
.stTabs [data-baseweb="tab"]:not([aria-selected="true"]):hover::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: var(--radius-small);
    padding: 1px;
    background: linear-gradient(
        135deg,
        rgba(106, 136, 255, 0.3),
        rgba(85, 117, 255, 0.1),
        rgba(106, 136, 255, 0.3)
    );
    -webkit-mask: 
        linear-gradient(#fff 0 0) content-box, 
        linear-gradient(#fff 0 0);
    mask: 
        linear-gradient(#fff 0 0) content-box, 
        linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    animation: gentle-shimmer 4s linear infinite;
    pointer-events: none;
}

.stTabs [aria-selected="true"] span {
    animation: tab-text-glow 3s var(--transition-elegant) infinite;
    position: relative;
}

/* Add subtle shine effect to selected tab */
.stTabs [aria-selected="true"] .tab-shine {
    position: absolute;
    top: 0;
    left: -100%;
    width: 50%;
    height: 100%;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.1),
        transparent
    );
    transform: skewX(-15deg);
    animation: light-streak-gentle 2.5s var(--transition-elegant) infinite;
}

/* Tab count badges (if any) */
.stTabs [data-baseweb="tab"] .tab-badge {
    background: rgba(106, 136, 255, 0.15);
    color: var(--text);
    font-size: 0.7rem;
    padding: 0.1rem 0.4rem;
    border-radius: 10px;
    margin-left: 0.4rem;
    font-weight: 600;
    border: 1px solid rgba(106, 136, 255, 0.2);
    transition: all var(--duration-fast) var(--transition-smooth);
}

.stTabs [aria-selected="true"] .tab-badge {
    background: rgba(255, 255, 255, 0.15);
    border-color: rgba(255, 255, 255, 0.3);
    transform: scale(1.1);
}

/* Tab transition when switching */
.stTabs [aria-selected="true"] {
    animation: 
        tab-switch var(--duration-base) var(--transition-elegant),
        gentle-shimmer 6s linear infinite;
}

/* ===== EXPANDERS - ELEGANT REVEAL ===== */
[data-testid="stExpander"] {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-medium);
    transition: 
        border-color var(--duration-fast) var(--transition-flow),
        transform var(--duration-base) var(--transition-bounce),
        box-shadow var(--duration-base) var(--transition-elegant);
    overflow: hidden;
}

[data-testid="stExpander"]:hover {
    border-color: rgba(106, 136, 255, 0.2) !important;
    transform: translateY(-1px);
    box-shadow: var(--shadow-elevated);
}

[data-testid="stExpander"] > div:first-child {
    transition: all var(--duration-base) var(--transition-smooth);
}

[data-testid="stExpander"] > div:last-child {
    animation: content-reveal var(--duration-slow) var(--transition-smooth);
}

/* ===== INPUTS & CONTROLS - ELEGANT FOCUS ===== */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stTextArea > div > div > textarea {
    background: rgba(22, 22, 42, 0.5) !important;
    border: 1px solid var(--glass-border) !important;
    color: var(--text) !important;
    border-radius: var(--radius-small);
    transition: 
        border-color var(--duration-fast) var(--transition-flow),
        background-color var(--duration-fast) var(--transition-smooth),
        box-shadow var(--duration-base) var(--transition-elegant),
        transform var(--duration-fast) var(--transition-bounce);
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div:focus-within,
.stTextArea > div > div > textarea:focus {
    border-color: var(--primary-hover) !important;
    box-shadow: 0 0 0 2px rgba(106, 136, 255, 0.1) !important;
    background: rgba(106, 136, 255, 0.04) !important;
    transform: translateY(-0.5px);
}

/* Fix for input text visibility */
.stSelectbox > div > div > div,
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    caret-color: var(--text) !important;
}

.stSelectbox [data-baseweb="select"] {
    color: var(--text) !important;
}

.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: var(--text-tertiary) !important;
    opacity: 0.7 !important;
}

[data-baseweb="popover"] {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(25px) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-small) !important;
    color: var(--text) !important;
}

[data-baseweb="menu"] li {
    color: var(--text) !important;
    background: transparent !important;
    transition: background-color var(--duration-fast) var(--transition-smooth);
}

[data-baseweb="menu"] li:hover {
    background: rgba(106, 136, 255, 0.1) !important;
}

/* ===== TOGGLES - SMOOTH TRANSITIONS ===== */
[data-baseweb="toggle"] {
    transition: all var(--duration-base) var(--transition-smooth) !important;
    border-radius: 12px !important;
}

[data-baseweb="toggle"]:hover:not(:disabled) {
    transform: scale(1.03);
}

[data-baseweb="toggle"][aria-checked="true"] {
    background-color: var(--primary-hover) !important;
    animation: subtle-pulse 3s var(--transition-smooth) infinite;
}

/* Success toggle variant */
[data-baseweb="toggle"][aria-checked="true"].toggle-success {
    background-color: var(--accent-success) !important;
    animation: success-pulse 3s var(--transition-smooth) infinite;
}

/* ===== SCROLLBAR - GLASS STYLE ===== */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.08);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb {
    background: rgba(106, 136, 255, 0.25);
    border-radius: 3px;
    transition: 
        background-color var(--duration-fast) var(--transition-smooth),
        width var(--duration-fast) var(--transition-bounce);
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(106, 136, 255, 0.35);
    width: 8px;
}

/* ===== METRICS - ULTRA-PREMIUM GLASS WITH EXQUISITE DETAILS ===== */
.stMetric {
    background: linear-gradient(
        145deg,
        rgba(85, 117, 255, 0.03),
        rgba(22, 22, 42, 0.75) 30%,
        rgba(22, 22, 42, 0.85)
    ) !important;
    backdrop-filter: blur(24px) saturate(200%);
    border: 1px solid transparent !important;
    border-radius: var(--radius-medium);
    transition: 
        transform var(--duration-base) var(--transition-bounce),
        box-shadow var(--duration-base) var(--transition-elegant),
        border-color var(--duration-fast) var(--transition-flow),
        background var(--duration-base) var(--transition-smooth);
    padding: 1.3rem 1.1rem;
    position: relative;
    overflow: hidden;
    box-shadow: 
        inset 0 1px 0 rgba(255, 255, 255, 0.06),
        0 6px 24px rgba(0, 0, 0, 0.08),
        0 1px 3px rgba(0, 0, 0, 0.04);
    will-change: transform, box-shadow, border-color, background;
}

.stMetric::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(
        135deg,
        rgba(106, 136, 255, 0.05) 0%,
        transparent 40%,
        transparent 60%,
        rgba(106, 136, 255, 0.05) 100%
    );
    opacity: 0;
    transition: opacity var(--duration-leisurely) var(--transition-elegant);
    pointer-events: none;
}

.stMetric::after {
    content: '';
    position: absolute;
    top: 0;
    left: -120%;
    width: 35%;
    height: 100%;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.04),
        rgba(255, 255, 255, 0.08),
        rgba(255, 255, 255, 0.04),
        transparent
    );
    transform: skewX(-12deg);
    transition: left 1.2s var(--transition-elegant);
    opacity: 0;
}

.stMetric:hover {
    background: linear-gradient(
        145deg,
        rgba(106, 136, 255, 0.06),
        rgba(22, 22, 42, 0.8) 30%,
        rgba(22, 22, 42, 0.9)
    ) !important;
    transform: translateY(-3px) scale(1.008);
    box-shadow: 
        inset 0 1px 0 rgba(255, 255, 255, 0.08),
        var(--shadow-elevated),
        0 4px 12px rgba(106, 136, 255, 0.05),
        0 0 0 1px rgba(106, 136, 255, 0.08);
    animation: subtle-pulse 5s var(--transition-flow) infinite;
}

.stMetric:hover::before {
    opacity: 0.6;
}

.stMetric:hover::after {
    left: 150%;
    opacity: 0.4;
    transition-duration: var(--duration-leisurely);
    transition-timing-function: var(--transition-butter);
}

.stMetric .stMetricLabel {
    color: var(--text-secondary) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.03em !important;
    margin-bottom: 0.4rem !important;
    transition: all var(--duration-base) var(--transition-smooth);
    text-transform: uppercase;
}

.stMetric:hover .stMetricLabel {
    color: var(--text) !important;
    letter-spacing: 0.04em !important;
    transform: translateY(-1px);
}

.stMetric .stMetricValue {
    color: var(--text) !important;
    font-size: 1.9rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
    background: linear-gradient(
        135deg, 
        rgba(232, 237, 244, 0.95) 0%,
        rgba(232, 237, 244, 1) 50%,
        rgba(232, 237, 244, 0.9) 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    transition: all var(--duration-base) var(--transition-smooth);
    position: relative;
    display: inline-block;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    line-height: 1.1;
}

.stMetric:hover .stMetricValue {
    transform: scale(1.025) translateY(-1px);
    text-shadow: 
        0 0 20px rgba(106, 136, 255, 0.25),
        0 2px 4px rgba(0, 0, 0, 0.15);
    background: linear-gradient(
        135deg, 
        rgba(232, 237, 244, 1) 0%,
        rgba(255, 255, 255, 1) 50%,
        rgba(232, 237, 244, 0.95) 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.stMetric .stMetricValue::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    width: 0;
    height: 1px;
    background: linear-gradient(90deg, var(--primary-hover), transparent);
    transition: width var(--duration-leisurely) var(--transition-elegant);
    opacity: 0.6;
}

.stMetric:hover .stMetricValue::after {
    width: 100%;
}

.stMetric .stMetricDelta {
    background: linear-gradient(
        135deg,
        rgba(16, 185, 129, 0.12),
        rgba(16, 185, 129, 0.08)
    ) !important;
    color: #10b981 !important;
    border: 1px solid rgba(16, 185, 129, 0.2) !important;
    border-radius: 14px !important;
    padding: 0.25rem 0.6rem !important;
    font-size: 0.73rem !important;
    font-weight: 600 !important;
    margin-top: 0.4rem !important;
    transition: all var(--duration-base) var(--transition-smooth);
    letter-spacing: 0.02em;
    backdrop-filter: blur(4px);
    position: relative;
    overflow: hidden;
}

.stMetric .stMetricDelta::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 30%;
    height: 100%;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.1),
        transparent
    );
    transform: skewX(-15deg);
    transition: left var(--duration-leisurely) var(--transition-elegant);
}

.stMetric:hover .stMetricDelta {
    background: linear-gradient(
        135deg,
        rgba(16, 185, 129, 0.18),
        rgba(16, 185, 129, 0.12)
    ) !important;
    border-color: rgba(16, 185, 129, 0.3) !important;
    transform: translateY(-1.5px);
    box-shadow: 0 2px 8px rgba(16, 185, 129, 0.1);
}

.stMetric:hover .stMetricDelta::before {
    left: 150%;
}

/* Negative delta with premium styling */
.stMetric .stMetricDelta[data-testid="stMetricDeltaNegative"] {
    background: linear-gradient(
        135deg,
        rgba(239, 68, 68, 0.12),
        rgba(239, 68, 68, 0.08)
    ) !important;
    color: var(--accent-error) !important;
    border-color: rgba(239, 68, 68, 0.2) !important;
}

.stMetric:hover .stMetricDelta[data-testid="stMetricDeltaNegative"] {
    background: linear-gradient(
        135deg,
        rgba(239, 68, 68, 0.18),
        rgba(239, 68, 68, 0.12)
    ) !important;
    border-color: rgba(239, 68, 68, 0.3) !important;
    box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);
}

/* Ultra-smooth number animation */
@keyframes gentle-count {
    0% { 
        opacity: 0.7; 
        transform: translateY(3px) scale(0.98);
        filter: blur(0.5px);
    }
    100% { 
        opacity: 1; 
        transform: translateY(0) scale(1);
        filter: blur(0);
    }
}

.stMetric .stMetricValue.updated {
    animation: gentle-count var(--duration-leisurely) var(--transition-elegant);
}

/* Micro-icon enhancement */
.stMetric .metric-icon {
    font-size: 1.1rem;
    opacity: 0.6;
    margin-right: 0.4rem;
    transition: all var(--duration-base) var(--transition-smooth);
    display: inline-block;
    filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.1));
}

.stMetric:hover .metric-icon {
    opacity: 1;
    transform: scale(1.12) rotate(8deg);
    filter: drop-shadow(0 0 6px rgba(106, 136, 255, 0.4));
    animation: elegant-float 4s var(--transition-flow) infinite;
}

/* Ultra-subtle corner accents */
.stMetric .corner-accent {
    position: absolute;
    width: 8px;
    height: 8px;
    opacity: 0.3;
}

.stMetric .corner-accent:nth-child(1) {
    top: 6px;
    left: 6px;
    border-top: 1px solid rgba(106, 136, 255, 0.4);
    border-left: 1px solid rgba(106, 136, 255, 0.4);
}

.stMetric .corner-accent:nth-child(2) {
    top: 6px;
    right: 6px;
    border-top: 1px solid rgba(106, 136, 255, 0.4);
    border-right: 1px solid rgba(106, 136, 255, 0.4);
}

.stMetric .corner-accent:nth-child(3) {
    bottom: 6px;
    left: 6px;
    border-bottom: 1px solid rgba(106, 136, 255, 0.4);
    border-left: 1px solid rgba(106, 136, 255, 0.4);
}

.stMetric .corner-accent:nth-child(4) {
    bottom: 6px;
    right: 6px;
    border-bottom: 1px solid rgba(106, 136, 255, 0.4);
    border-right: 1px solid rgba(106, 136, 255, 0.4);
}

.stMetric:hover .corner-accent {
    opacity: 0.6;
    transition: opacity var(--duration-fast) var(--transition-smooth);
}

/* Micro data shimmer effect */
@keyframes data-shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}

.stMetric .stMetricValue.highlight {
    background: linear-gradient(
        90deg,
        var(--text) 25%,
        rgba(232, 237, 244, 0.9) 50%,
        var(--text) 75%
    );
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: data-shimmer 3s linear infinite;
}

/* Metric group synergy */
.stMetric + .stMetric {
    margin-left: 0.6rem;
}

.stMetric + .stMetric:hover {
    z-index: 10;
    transform: translateY(-3px) scale(1.008) translateX(1px);
}

/* Responsive metric refinement */
@media (max-width: 768px) {
    .stMetric {
        padding: 1rem 0.8rem;
    }
    
    .stMetric .stMetricValue {
        font-size: 1.6rem !important;
    }
    
    .stMetric:hover {
        transform: translateY(-2px) scale(1.005);
    }
}

/* ===== UPLOAD ZONE - ULTRA-PREMIUM GLASS ===== */
[data-testid="stFileUploaderDropzone"] {
    background: linear-gradient(
        145deg,
        rgba(22, 22, 42, 0.5),
        rgba(22, 22, 42, 0.65) 40%,
        rgba(22, 22, 42, 0.5)
    ) !important;
    backdrop-filter: blur(28px) saturate(180%);
    border: 2px dashed transparent !important;
    border-radius: var(--radius-medium) !important;
    position: relative;
    overflow: hidden;
    transition: 
        transform var(--duration-base) var(--transition-bounce),
        box-shadow var(--duration-base) var(--transition-elegant),
        background var(--duration-slow) var(--transition-smooth),
        border-color var(--duration-fast) var(--transition-flow);
    box-shadow: 
        inset 0 1px 0 rgba(255, 255, 255, 0.05),
        0 8px 32px rgba(0, 0, 0, 0.1),
        0 1px 3px rgba(0, 0, 0, 0.05);
}

[data-testid="stFileUploaderDropzone"]::before {
    content: '';
    position: absolute;
    inset: 0;
    background: conic-gradient(
        from 0deg at 50% 50%,
        rgba(106, 136, 255, 0.05) 0deg,
        rgba(106, 136, 255, 0.02) 60deg,
        rgba(106, 136, 255, 0.01) 120deg,
        rgba(106, 136, 255, 0.05) 180deg,
        rgba(106, 136, 255, 0.02) 240deg,
        rgba(106, 136, 255, 0.01) 300deg,
        rgba(106, 136, 255, 0.05) 360deg
    );
    opacity: 0;
    transition: opacity var(--duration-leisurely) var(--transition-elegant);
    pointer-events: none;
}

[data-testid="stFileUploaderDropzone"]::after {
    content: '';
    position: absolute;
    inset: 0;
    border: 2px dashed transparent;
    border-radius: var(--radius-medium) !important;
    background: linear-gradient(
        135deg,
        rgba(106, 136, 255, 0.3),
        rgba(85, 117, 255, 0.15),
        rgba(106, 136, 255, 0.3)
    ) border-box;
    -webkit-mask: 
        linear-gradient(#fff 0 0) padding-box, 
        linear-gradient(#fff 0 0);
    mask: 
        linear-gradient(#fff 0 0) padding-box, 
        linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    transition: all var(--duration-slow) var(--transition-elegant);
    pointer-events: none;
}

[data-testid="stFileUploaderDropzone"] .shimmer-layer {
    position: absolute;
    top: 0;
    left: -100%;
    width: 25%;
    height: 100%;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.03),
        rgba(255, 255, 255, 0.06),
        rgba(255, 255, 255, 0.03),
        transparent
    );
    transform: skewX(-12deg);
    animation: gentle-shimmer 12s ease-in-out infinite;
    opacity: 0;
    pointer-events: none;
}

[data-testid="stFileUploaderDropzone"]:hover {
    background: linear-gradient(
        145deg,
        rgba(106, 136, 255, 0.08),
        rgba(22, 22, 42, 0.7) 40%,
        rgba(106, 136, 255, 0.08)
    ) !important;
    transform: translateY(-2px) scale(1.002);
    box-shadow: 
        inset 0 1px 0 rgba(255, 255, 255, 0.08),
        var(--shadow-elevated),
        0 4px 16px rgba(106, 136, 255, 0.08);
    animation: subtle-pulse 6s var(--transition-flow) infinite;
}

[data-testid="stFileUploaderDropzone"]:hover::before {
    opacity: 0.4;
}

[data-testid="stFileUploaderDropzone"]:hover::after {
    opacity: 0.8;
    background: linear-gradient(
        135deg,
        rgba(106, 136, 255, 0.4),
        rgba(85, 117, 255, 0.2),
        rgba(106, 136, 255, 0.4)
    ) border-box;
}

[data-testid="stFileUploaderDropzone"]:hover .shimmer-layer {
    opacity: 0.3;
    animation-duration: 8s;
}

[data-testid="stFileUploaderDropzone"]:focus-within {
    animation: gentle-shimmer 4s ease-in-out infinite !important;
}

/* Upload zone content */
[data-testid="stFileUploaderDropzone"] .st-emotion-cache-18vzmqx {
    position: relative;
    z-index: 2;
    transition: all var(--duration-base) var(--transition-smooth);
}

[data-testid="stFileUploaderDropzone"]:hover .st-emotion-cache-18vzmqx {
    transform: translateY(-1px) scale(1.02);
}

[data-testid="stFileUploaderDropzone"] .st-emotion-cache-18vzmqx svg {
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
    transition: all var(--duration-base) var(--transition-smooth);
}

[data-testid="stFileUploaderDropzone"]:hover .st-emotion-cache-18vzmqx svg {
    filter: drop-shadow(0 4px 12px rgba(106, 136, 255, 0.3));
    transform: rotate(5deg) scale(1.05);
}

/* Upload zone text */
[data-testid="stFileUploaderDropzone"] p {
    color: var(--text-tertiary) !important;
    transition: all var(--duration-base) var(--transition-smooth);
    position: relative;
    z-index: 2;
}

[data-testid="stFileUploaderDropzone"]:hover p {
    color: var(--text) !important;
    text-shadow: 0 0 10px rgba(106, 136, 255, 0.2);
}

/* Upload zone button */
[data-testid="stFileUploaderDropzone"] button {
    background: linear-gradient(
        135deg,
        rgba(106, 136, 255, 0.12),
        rgba(85, 117, 255, 0.08)
    ) !important;
    border: 1px solid rgba(106, 136, 255, 0.2) !important;
    color: var(--text) !important;
    transition: 
        background-color var(--duration-fast) var(--transition-flow),
        border-color var(--duration-fast) var(--transition-flow),
        transform var(--duration-base) var(--transition-bounce),
        box-shadow var(--duration-base) var(--transition-elegant) !important;
    position: relative;
    z-index: 2;
    overflow: hidden;
}

[data-testid="stFileUploaderDropzone"] button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 40%;
    height: 100%;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.1),
        transparent
    );
    transform: skewX(-15deg);
    transition: left var(--duration-leisurely) var(--transition-elegant);
}

[data-testid="stFileUploaderDropzone"]:hover button {
    background: linear-gradient(
        135deg,
        rgba(106, 136, 255, 0.18),
        rgba(85, 117, 255, 0.12)
    ) !important;
    border-color: rgba(106, 136, 255, 0.3) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

[data-testid="stFileUploaderDropzone"]:hover button::before {
    left: 150%;
}

/* Upload zone active state */
[data-testid="stFileUploaderDropzone"].upload-active {
    animation: gentle-shimmer 2s ease-in-out infinite !important;
    border-color: rgba(106, 136, 255, 0.4) !important;
}

[data-testid="stFileUploaderDropzone"].upload-active .st-emotion-cache-18vzmqx svg {
    animation: elegant-float 3s var(--transition-flow) infinite;
}

/* ===== DIVIDERS - ELEGANT LIGHT TRAILS ===== */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(
        90deg,
        transparent 0%,
        rgba(106, 136, 255, 0.1) 10%,
        rgba(106, 136, 255, 0.25) 50%,
        rgba(106, 136, 255, 0.1) 90%,
        transparent 100%
    );
    margin: 1.8rem 0;
    opacity: 0.3;
    position: relative;
    overflow: visible;
    transition: 
        opacity var(--duration-base) var(--transition-smooth),
        transform var(--duration-base) var(--transition-bounce),
        background var(--duration-slow) var(--transition-elegant);
}

hr::before {
    content: '';
    position: absolute;
    top: -0.5px;
    left: 20%;
    right: 20%;
    height: 2px;
    background: linear-gradient(
        90deg,
        transparent,
        var(--primary-hover),
        transparent
    );
    border-radius: 1px;
    opacity: 0;
    transition: opacity var(--duration-base) var(--transition-smooth);
    filter: blur(0.5px);
}

hr::after {
    content: '';
    position: absolute;
    top: -1px;
    left: 0;
    width: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--primary-hover), transparent);
    border-radius: 1.5px;
    transition: width var(--duration-leisurely) var(--transition-elegant);
    opacity: 0;
}

hr:hover {
    opacity: 0.6;
    transform: scaleY(1.2);
    background: linear-gradient(
        90deg,
        transparent 0%,
        rgba(106, 136, 255, 0.15) 10%,
        rgba(106, 136, 255, 0.35) 50%,
        rgba(106, 136, 255, 0.15) 90%,
        transparent 100%
    );
}

hr:hover::before {
    opacity: 0.4;
    animation: gentle-shimmer 3s linear infinite;
}

hr:hover::after {
    width: 100%;
    opacity: 0.3;
    transition-duration: var(--duration-leisurely);
}

/* Section dividers */
hr.section-divider {
    height: 2px;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(106, 136, 255, 0.15),
        rgba(106, 136, 255, 0.3),
        rgba(106, 136, 255, 0.15),
        transparent
    );
    margin: 2rem 0;
    opacity: 0.4;
}

hr.section-divider::before {
    content: '✦';
    position: absolute;
    top: -10px;
    left: 50%;
    transform: translateX(-50%);
    color: rgba(106, 136, 255, 0.6);
    font-size: 0.8rem;
    background: var(--glass-bg);
    padding: 0 0.5rem;
    border-radius: 10px;
    opacity: 0;
    transition: opacity var(--duration-base) var(--transition-smooth);
}

hr.section-divider:hover::before {
    opacity: 1;
}

/* Subtle dotted dividers */
hr.dotted-divider {
    height: 1px;
    background: linear-gradient(
        90deg,
        transparent,
        transparent 10%,
        rgba(106, 136, 255, 0.2) 10%,
        rgba(106, 136, 255, 0.2) 20%,
        transparent 20%,
        transparent 30%,
        rgba(106, 136, 255, 0.2) 30%,
        rgba(106, 136, 255, 0.2) 40%,
        transparent 40%,
        transparent 50%,
        rgba(106, 136, 255, 0.2) 50%,
        rgba(106, 136, 255, 0.2) 60%,
        transparent 60%,
        transparent 70%,
        rgba(106, 136, 255, 0.2) 70%,
        rgba(106, 136, 255, 0.2) 80%,
        transparent 80%,
        transparent 90%,
        rgba(106, 136, 255, 0.2) 90%,
        transparent 100%
    );
    background-size: 20px 1px;
    opacity: 0.3;
}

/* Animated pulse divider */
@keyframes divider-pulse {
    0%, 100% { opacity: 0.2; }
    50% { opacity: 0.5; }
}

hr.pulse-divider {
    animation: divider-pulse 4s var(--transition-smooth) infinite;
}

/* ===== TABLES & DATAFRAMES - GLASS BACKGROUND ===== */
.dataframe {
    background: rgba(22, 22, 42, 0.3) !important;
    backdrop-filter: blur(10px);
    border-radius: var(--radius-small);
    overflow: hidden;
    border: 1px solid var(--glass-border);
}

.dataframe tbody tr {
    transition: background-color var(--duration-fast) var(--transition-smooth);
}

.dataframe tbody tr:hover {
    background-color: rgba(106, 136, 255, 0.06) !important;
}

/* ===== UTILITY CLASSES ===== */
.glass-elegant {
    background: var(--glass-bg);
    backdrop-filter: blur(25px);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-medium);
    transition: 
        transform var(--duration-base) var(--transition-bounce),
        box-shadow var(--duration-base) var(--transition-elegant),
        border-color var(--duration-fast) var(--transition-flow);
}

.text-gradient {
    background: linear-gradient(135deg, var(--primary-hover), #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.border-glow {
    animation: border-glow 4s var(--transition-smooth) infinite;
}

/* ===== RESPONSIVE ADJUSTMENTS ===== */
@media (max-width: 768px) {
    .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    [data-testid="stSidebar"] { backdrop-filter: blur(15px); }
    :root {
        --radius-large: 12px;
        --radius-medium: 10px;
        --radius-small: 6px;
    }
}

/* Hide default Streamlit elements */
div[data-baseweb="tab-highlight"] { display: none !important; }

/* Error title */
[data-testid="stExceptionMessage"] span {
    color: var(--text) !important;
    font-weight: 600;
    font-size: 1rem;
    margin-bottom: 0.4rem;
    display: block;
}

/* Error message */
[data-testid="stExceptionMessage"] {
    color: rgba(232,237,244,0.85) !important;
    font-family: 'SF Mono', monospace;
    font-size: 0.88rem;
    padding: 0.6rem;
    background: rgba(0,0,0,0.15);
    border-radius: var(--radius-small);
    margin: 0.5rem 0;
    border: 1px solid rgba(255,255,255,0.05);
}

/* Code block */
.st-emotion-cache-5wvq1f {
    background: rgba(0,0,0,0.2) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: var(--radius-small);
    padding: 0.7rem !important;
    margin: 0.5rem 0;
    font-size: 0.82rem;
}

/* Traceback rows */
.st-emotion-cache-1mrdis4 {
    color: rgba(232,237,244,0.8) !important;
    font-family: 'SF Mono', monospace;
    font-size: 0.8rem;
    line-height: 1.5;
    padding: 0.2rem 0;
    border-left: 2px solid transparent;
    padding-left: 0.6rem !important;
    transition: all 0.2s ease;
}

.st-emotion-cache-1mrdis4:hover {
    border-left-color: rgba(239,68,68,0.5);
    background: rgba(239,68,68,0.05);
}

/* Action buttons */
.st-emotion-cache-1w9o8o {
    display: flex;
    gap: 0.6rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255,255,255,0.08);
}

.st-emotion-cache-bxd189,
.st-emotion-cache-1w9o8o a {
    background: rgba(106,136,255,0.1) !important;
    color: var(--text) !important;
    border: 1px solid rgba(106,136,255,0.2) !important;
    border-radius: var(--radius-small) !important;
    padding: 0.4rem 0.8rem !important;
    font-size: 0.82rem !important;
    font-weight: 500;
    text-decoration: none;
    transition: all var(--duration-fast) var(--transition-smooth);
    backdrop-filter: blur(8px);
}

.st-emotion-cache-bxd189:hover,
.st-emotion-cache-1w9o8o a:hover {
    background: rgba(106,136,255,0.15) !important;
    border-color: rgba(106,136,255,0.3) !important;
    transform: translateY(-1px);
}

/* Micro animations */
@keyframes alert-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.9; }
}

[data-testid="stAlertContentError"] .stAlert {
    animation: 
        soft-fade-in var(--duration-slow) var(--transition-elegant),
        alert-pulse 4s ease-in-out infinite;
}

/* Minimal code line highlight */
.st-emotion-cache-1mrdis4:first-of-type {
    color: rgba(239,68,68,0.9) !important;
    font-weight: 500;
}

/* Button icons */
.st-emotion-cache-bxd189::before {
    content: '📋';
    margin-right: 0.4rem;
    font-size: 0.9em;
}

.st-emotion-cache-1w9o8o a[href*="google.com"]::before {
    content: '🔍';
    margin-right: 0.4rem;
    font-size: 0.9em;
}

.st-emotion-cache-1w9o8o a[href*="chatgpt.com"]::before {
    content: '🤖';
    margin-right: 0.4rem;
    font-size: 0.9em;
}

/* Loading spinner enhancement */
.st-emotion-cache-7ym5gk {
    border: 3px solid rgba(106,136,255,0.1) !important;
    border-top: 3px solid rgba(106,136,255,0.6) !important;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Enhanced focus states for accessibility */
*:focus-visible {
    outline: 2px solid rgba(106,136,255,0.5);
    outline-offset: 2px;
    border-radius: var(--radius-small);
}

/* Selection color */
::selection {
    background: rgba(106,136,255,0.3);
    color: white;
}

::-moz-selection {
    background: rgba(106,136,255,0.3);
    color: white;
}

/* Smooth scroll behavior */
html {
    scroll-behavior: smooth;
}

</style>"""

# ============================================================================
# HTML TEMPLATES - REFINED WITH SMOOTH TRANSITIONS
# ============================================================================

def get_main_header_html(company: str, version: str, developer: str, year: str) -> str:
    """Generate premium main header with elegant animations"""
    return f"""<div style="text-align:center;margin-bottom:1.5rem;padding:2rem 1.5rem;background:linear-gradient(145deg,#0e0e20 0%,#191934 100%);border-radius:var(--radius-large);color:white;box-shadow:var(--shadow-elevated),inset 0 1px 0 rgba(255,255,255,0.08);position:relative;overflow:hidden;border:1px solid rgba(255,255,255,0.1);min-height:140px;display:flex;flex-direction:column;justify-content:center;align-items:center;animation:soft-fade-in 1s var(--transition-elegant);">
<div class="breathing-orb" style="position:absolute;top:-40px;right:-30px;width:150px;height:150px;background:radial-gradient(circle,rgba(99,102,241,0.1) 0%,transparent 70%);border-radius:50%;filter:blur(30px);opacity:0.5;animation:elegant-float 8s var(--transition-flow) infinite;z-index:1;"></div>
<div class="breathing-orb" style="position:absolute;bottom:-40px;left:-30px;width:150px;height:150px;background:radial-gradient(circle,rgba(139,92,246,0.08) 0%,transparent 70%);border-radius:50%;filter:blur(30px);opacity:0.4;animation:elegant-float 10s var(--transition-flow) infinite reverse;animation-delay:2s;z-index:1;"></div>
<div style="position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:30px 30px;pointer-events:none;opacity:0.2;"></div>
<div style="position:relative;z-index:10;width:100%;max-width:800px;">
<div style="display:flex;align-items:center;justify-content:center;gap:1rem;margin-bottom:0.75rem;animation:soft-fade-in 1.2s var(--transition-elegant);">
<div class="breathing-element" style="padding:0.5rem;background:rgba(255,255,255,0.05);border-radius:var(--radius-medium);border:1px solid rgba(255,255,255,0.12);backdrop-filter:blur(8px);box-shadow:0 6px 20px rgba(0,0,0,0.2);position:relative;transition:all var(--duration-base) var(--transition-smooth);cursor:default;animation:elegant-float 6s var(--transition-flow) infinite;" onmouseenter="this.style.animationPlayState='paused';this.style.transform='translateY(-1px) scale(1.02)';this.style.boxShadow='var(--shadow-elevated),0 0 0 1px rgba(102,126,234,0.2)';this.style.background='rgba(255,255,255,0.08)';" onmouseleave="this.style.animationPlayState='running';this.style.transform='translateY(0) scale(1)';this.style.boxShadow='0 6px 20px rgba(0,0,0,0.2)';this.style.background='rgba(255,255,255,0.05)';">
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter:drop-shadow(0 3px 8px rgba(0,0,0,0.3));transition:all var(--duration-base) var(--transition-smooth);" onmouseenter="this.style.filter='drop-shadow(0 5px 12px rgba(102,126,234,0.4))'" onmouseleave="this.style.filter='drop-shadow(0 3px 8px rgba(0,0,0,0.3))'">
<path d="M3 17L9 11L13 15L21 7" stroke="url(#chartGradient)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="3" cy="17" r="1.6" fill="url(#pointGradient)"/>
<circle cx="9" cy="11" r="1.6" fill="url(#pointGradient)"/>
<circle cx="13" cy="15" r="1.6" fill="url(#pointGradient)"/>
<circle cx="21" cy="7" r="1.6" fill="url(#pointGradient)"/>
<path d="M17 3L17 8M19 5L15 5" stroke="url(#aiGradient)" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
<defs>
<linearGradient id="chartGradient" x1="3" y1="17" x2="21" y2="7"><stop offset="0%" stop-color="#6366f1"/><stop offset="50%" stop-color="#8b5cf6"/><stop offset="100%" stop-color="#a78bfa"/></linearGradient>
<linearGradient id="pointGradient" x1="0" y1="0" x2="4" y2="4"><stop offset="0%" stop-color="#6366f1"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient>
<linearGradient id="aiGradient" x1="15" y1="3" x2="19" y2="8"><stop offset="0%" stop-color="#10b981"/><stop offset="50%" stop-color="#0ea5e9"/><stop offset="100%" stop-color="#3b82f6"/></linearGradient>
</defs></svg></div>
<h1 class="breathing-text" style="margin:0;font-size:1.8rem;font-weight:700;letter-spacing:-0.3px;background:linear-gradient(to right,#ffffff,#e0e7ff,#c7d2fe);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;line-height:1.2;text-shadow:0 2px 10px rgba(0,0,0,0.2);position:relative;cursor:default;animation:soft-fade-in 1.4s var(--transition-elegant);" onmouseenter="this.style.animationPlayState='paused';this.style.textShadow='0 0 20px rgba(102,126,234,0.3)';this.nextElementSibling.style.width='80px';" onmouseleave="this.style.animationPlayState='running';this.style.textShadow='0 2px 10px rgba(0,0,0,0.2)';this.nextElementSibling.style.width='0';">
Data Explorer Pro
<span style="position:absolute;bottom:-2px;left:50%;transform:translateX(-50%);width:0;height:2px;background:linear-gradient(90deg,transparent,rgba(139,92,246,0.8),transparent);border-radius:1px;transition:width var(--duration-slow) var(--transition-smooth);"></span></h1></div>
<div class="breathing-divider" style="width:80px;height:1.5px;margin:0 auto 0.75rem;background:linear-gradient(90deg,transparent,rgba(139,92,246,0.6),transparent);border-radius:1px;opacity:0.7;animation:soft-fade-in 1.6s var(--transition-elegant);"></div>
<p style="font-size:0.9rem;margin:0 0 1rem 0;color:rgba(255,255,255,0.85);font-weight:300;letter-spacing:0.1px;line-height:1.4;animation:soft-fade-in 1.8s var(--transition-elegant);">
Professional analytics by <span class="breathing-company" style="font-weight:500;color:rgba(255,255,255,0.95);">by {company}</span></p>
<div class="breathing-badge" style="display:inline-flex;align-items:center;gap:0.6rem;padding:0.4rem 1rem;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:50px;backdrop-filter:blur(6px);box-shadow:0 4px 20px rgba(0,0,0,0.15);animation:soft-fade-in 2s var(--transition-elegant);" onmouseenter="this.style.animationPlayState='paused';this.style.transform='translateY(-1px)';this.style.boxShadow='var(--shadow-elevated),0 0 0 1px rgba(102,126,234,0.15)';this.style.background='rgba(255,255,255,0.09)';" onmouseleave="this.style.animationPlayState='running';this.style.transform='translateY(0)';this.style.boxShadow='0 4px 20px rgba(0,0,0,0.15)';this.style.background='rgba(255,255,255,0.06)';">
<div style="position:relative;width:6px;height:6px;">
<div style="position:absolute;inset:0;border-radius:50%;background:#10b981;animation:subtle-pulse 3s var(--transition-smooth) infinite;box-shadow:0 0 0 0 rgba(16,185,129,0.4);"></div>
<div style="position:absolute;inset:-2px;border-radius:50%;border:1px solid rgba(16,185,129,0.3);animation:border-glow 3s var(--transition-smooth) infinite;opacity:0;"></div></div>
<span style="font-size:0.75rem;color:rgba(255,255,255,0.9);font-weight:500;">v{version}</span>
<div style="width:1px;height:12px;background:linear-gradient(transparent,rgba(255,255,255,0.3),transparent);"></div>
<span style="font-size:0.75rem;color:rgba(255,255,255,0.7);">{developer}</span></div>
<div style="margin-top:0.5rem;display:flex;justify-content:center;gap:0.75rem;opacity:0.6;animation:soft-fade-in 2.2s var(--transition-elegant);">
<style>
@media (prefers-reduced-motion:reduce){{*{{animation:none !important;}}}}
</style>
<script>
document.querySelectorAll('.breathing-element,.breathing-text,.breathing-divider,.breathing-company,.breathing-badge').forEach(el=>{{
el.addEventListener('mouseenter',()=>el.style.animationPlayState='paused');
el.addEventListener('mouseleave',()=>el.style.animationPlayState='running');
}});
const title=document.querySelector('.breathing-text');if(title){{title.addEventListener('mouseenter',()=>title.nextElementSibling.style.width='80px');title.addEventListener('mouseleave',()=>title.nextElementSibling.style.width='0');}}
</script></div>"""

def get_sidebar_header_html(company: str) -> str:
    """Premium sidebar header with elegant glass effect"""
    return f"""<div class="sidebar-glass-card" style='text-align:center;margin-bottom:1.5rem;padding:1.2rem;position:relative;animation:soft-fade-in 0.8s var(--transition-elegant);'>
    <div style='position:absolute;top:-20px;right:-20px;width:80px;height:80px;background:radial-gradient(circle,rgba(106,136,255,0.1) 0%,transparent 70%);border-radius:50%;filter:blur(15px);z-index:0;opacity:0.6;'></div>
    <div style='position:absolute;bottom:-20px;left:-20px;width:80px;height:80px;background:radial-gradient(circle,rgba(106,136,255,0.08) 0%,transparent 70%);border-radius:50%;filter:blur(15px);z-index:0;opacity:0.4;'></div>
    <div style='position:relative;z-index:10;'>
    <div style='display:flex;align-items:center;justify-content:center;gap:0.85rem;margin-bottom:0.6rem;'>
    <div style='padding:0.6rem;background:rgba(255,255,255,0.08);border-radius:var(--radius-medium);border:1px solid rgba(255,255,255,0.15);display:flex;align-items:center;justify-content:center;backdrop-filter:blur(8px);transition:all var(--duration-base) var(--transition-smooth);' onmouseenter="this.style.transform='rotate(5deg) scale(1.05)';this.style.background='rgba(255,255,255,0.12)';" onmouseleave="this.style.transform='rotate(0) scale(1)';this.style.background='rgba(255,255,255,0.08)';">
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 3L8 8L3 13M13 17H21M13 7H21" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
    <h2 style='margin:0;color:white;font-size:1.35rem;font-weight:600;letter-spacing:-0.3px;transition:all var(--duration-base) var(--transition-smooth);' onmouseenter="this.style.textShadow='0 0 10px rgba(106,136,255,0.3)';" onmouseleave="this.style.textShadow='none';">Explorer</h2></div>
    <p style='margin:0;font-size:0.88rem;font-weight:400;color:rgba(255,255,255,0.7);'>by {company}</p></div></div>"""

def get_sidebar_footer_html(version: str, developer: str, company: str, year: str) -> str:
    """Elegant glass footer with smooth transitions"""
    return f"""<div class="sidebar-glass-card" style='color:var(--text-tertiary);font-size:0.78rem;margin-top:2rem;padding:1.2rem;text-align:center;animation:soft-fade-in 1s var(--transition-elegant);'>
    <div style='display:flex;align-items:center;justify-content:center;gap:0.6rem;margin-bottom:0.6rem;'>
    <div style='width:6px;height:6px;border-radius:50%;position:relative;background:var(--primary-hover);animation:subtle-pulse 4s var(--transition-smooth) infinite;'></div>
    <small style='font-weight:500;color:var(--text);'>v{version}</small></div>
    <small style='display:block;margin-bottom:0.3rem;color:var(--text-secondary);'>{developer}</small>
    <small style='font-size:0.72rem;opacity:0.7;color:var(--text-tertiary);'>© {year} {company}</small></div>"""

def get_dataset_info_card(filename: str, rows: int, cols: int) -> str:
    """Elegant dataset card with smooth animations"""
    card_id = hashlib.md5(filename.encode()).hexdigest()[:6]
    return f"""<div id="dataset-card-{card_id}" class="sidebar-glass-card" style='padding:1.2rem;margin-bottom:1rem;animation:soft-fade-in 0.9s var(--transition-elegant);'>
    <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.85rem;'>
    <span style='font-weight:600;font-size:0.92rem;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{filename}</span>
    <div style='font-size:0.72rem;background:rgba(74,222,128,0.12);color:var(--accent-success);padding:0.25rem 0.7rem;border-radius:var(--radius-small);font-weight:600;border:1px solid rgba(74,222,128,0.2);transition:all var(--duration-fast) var(--transition-smooth);animation:success-pulse 3s var(--transition-smooth) infinite;'>ACTIVE</div></div>
    <div style='display:grid;grid-template-columns:1fr 1fr;gap:0.6rem;'>
    <div style='font-size:0.82rem;color:var(--text-secondary);padding:0.5rem;border-radius:var(--radius-small);background:rgba(0,0,0,0.1);transition:all var(--duration-base) var(--transition-smooth);' onmouseenter="this.style.background='rgba(106,136,255,0.1)';this.style.transform='translateY(-1px)';" onmouseleave="this.style.background='rgba(0,0,0,0.1)';this.style.transform='translateY(0)';">
    <div style='font-weight:700;color:var(--primary-hover);font-size:1.1rem;transition:all var(--duration-base) var(--transition-smooth);' onmouseenter="this.style.textShadow='0 0 10px rgba(106,136,255,0.3)';" onmouseleave="this.style.textShadow='none';">{rows:,}</div>
    <div style='font-size:0.72rem;opacity:0.8;'>Rows</div></div>
    <div style='font-size:0.82rem;color:var(--text-secondary);padding:0.5rem;border-radius:var(--radius-small);background:rgba(0,0,0,0.1);transition:all var(--duration-base) var(--transition-smooth);' onmouseenter="this.style.background='rgba(106,136,255,0.1)';this.style.transform='translateY(-1px)';" onmouseleave="this.style.background='rgba(0,0,0,0.1)';this.style.transform='translateY(0)';">
    <div style='font-weight:700;color:var(--primary-hover);font-size:1.1rem;transition:all var(--duration-base) var(--transition-smooth);' onmouseenter="this.style.textShadow='0 0 10px rgba(106,136,255,0.3)';" onmouseleave="this.style.textShadow='none';">{cols}</div>
    <div style='font-size:0.72rem;opacity:0.8;'>Columns</div></div></div>
    <script>
    document.getElementById('dataset-card-{card_id}').addEventListener('mouseenter', function() {{
        this.style.animation = 'subtle-pulse 3s ease-in-out infinite';
    }});
    document.getElementById('dataset-card-{card_id}').addEventListener('mouseleave', function() {{
        this.style.animation = '';
    }});
    </script></div>"""

# ============================================================================
# UI COMPONENT CLASS - ELEGANT & SMOOTH
# ============================================================================

class UIComponents:
    """Centralized UI component manager for elegant interfaces"""
    
    @staticmethod
    def render_glass_card(title: str, content: str, icon: str = "✨", variant: str = "default"):
        """Render an elegant glass card"""
        variant_styles = {
            "default": ("rgba(106, 136, 255, 0.08)", "rgba(106, 136, 255, 0.15)", "var(--primary-hover)"),
            "success": ("rgba(74, 222, 128, 0.08)", "rgba(74, 222, 128, 0.15)", "var(--accent-success)"),
            "warning": ("rgba(251, 146, 60, 0.08)", "rgba(251, 146, 60, 0.15)", "var(--accent-warning)"),
            "info": ("rgba(96, 165, 250, 0.08)", "rgba(96, 165, 250, 0.15)", "var(--accent-info)"),
            "error": ("rgba(239, 68, 68, 0.08)", "rgba(239, 68, 68, 0.15)", "var(--accent-error)"),
        }
        
        bg, border, color = variant_styles.get(variant, variant_styles["default"])
        
        return f"""<div class="sidebar-glass-card" style='padding:1.2rem;margin-bottom:1rem;background:{bg} !important;border-color:{border} !important;'>
        <div style='display:flex;align-items:flex-start;gap:0.85rem;'>
        <div style='font-size:1.2rem;margin-top:0.15rem;color:{color};transition:all var(--duration-base) var(--transition-smooth);' onmouseenter="this.style.transform='scale(1.2) rotate(5deg)';" onmouseleave="this.style.transform='scale(1) rotate(0)';">{icon}</div>
        <div><div style='font-weight:600;margin-bottom:0.3rem;font-size:0.95rem;color:var(--text);'>{title}</div>
        <div style='color:var(--text-secondary);font-size:0.9rem;line-height:1.5;'>{content}</div></div></div></div>"""
    
    @staticmethod
    def render_success_glass(message: str, icon: str = "✅"):
        """Render a success message with elegant glass"""
        return UIComponents.render_glass_card("Success", message, icon, "success")
    
    @staticmethod
    def render_warning_glass(message: str, icon: str = "⚠️"):
        """Render a warning with elegant glass"""
        return UIComponents.render_glass_card("Warning", message, icon, "warning")
    
    @staticmethod
    def render_info_glass(message: str, icon: str = "ℹ️"):
        """Render an info message with elegant glass"""
        return UIComponents.render_glass_card("Info", message, icon, "info")
    
    @staticmethod
    def render_error_glass(message: str, icon: str = "❌"):
        """Render an error message with elegant glass"""
        return UIComponents.render_glass_card("Error", message, icon, "error")
    
    @staticmethod
    def create_button_key(text: str) -> str:
        """Create a unique key for buttons"""
        return hashlib.md5(text.encode()).hexdigest()[:8]

# ============================================================================
# SIDEBAR COMPONENTS - ELEGANT & SMOOTH
# ============================================================================

def render_sidebar_header(company: str):
    """Render elegant sidebar header"""
    st.markdown(get_sidebar_header_html(company), unsafe_allow_html=True)
    st.markdown("""<div style='height:1px;background:linear-gradient(90deg,transparent,rgba(106,136,255,0.3),transparent);margin:1.2rem 0;border-radius:1px;'></div>""", unsafe_allow_html=True)

def render_sidebar_footer(version: str, developer: str, company: str, year: str):
    """Render elegant glass sidebar footer"""
    st.markdown(get_sidebar_footer_html(version, developer, company, year), unsafe_allow_html=True)

def render_ai_settings():
    """Render AI settings panel with elegant styling"""
    with st.expander("🤖 **AI Configuration**", expanded=False):
        if st.session_state.get('ai_model', 'EchoEngine') == 'EchoEngine':
            st.markdown(UIComponents.render_info_glass(
                "Heuristic Mode", 
                "Using rule-based analysis for insights"
            ), unsafe_allow_html=True)
        else:
            model_name = st.session_state.ai_model.replace('-', ' ').title()
            st.markdown(UIComponents.render_success_glass(f"Live AI: {model_name}"), unsafe_allow_html=True)
        
        st.markdown("<div style='color:var(--text);margin-bottom:0.5rem;font-weight:500;'>Model Selection</div>", unsafe_allow_html=True)
        model_options = ["EchoEngine", "gemini-2.5-flash-lite", "claude-3-haiku-20240307"]
        current_model = st.session_state.get('ai_model', 'EchoEngine')
        
        st.session_state.ai_model = st.selectbox(
            "Select AI Model",
            model_options,
            index=model_options.index(current_model) if current_model in model_options else 0,
            help="EchoEngine mode uses heuristic analysis. Live AI requires API key.",
            label_visibility="collapsed"
        )
        
        if st.session_state.ai_model != "EchoEngine":
            st.markdown("<div style='color:var(--text);margin-bottom:0.5rem;font-weight:500;'>API Key</div>", unsafe_allow_html=True)
            st.session_state.api_key = st.text_input(
                "Enter your API key",
                type="password",
                value=st.session_state.get('api_key', ''),
                help="Required for live AI models",
                placeholder="sk-... or your API key",
                label_visibility="collapsed"
            )
        
        st.markdown("""<div style='height:1px;background:rgba(106,136,255,0.2);margin:1.2rem 0;border-radius:1px;'></div>""", unsafe_allow_html=True)
        
        st.session_state.ai_EchoEngine_mode = st.toggle(
            "Force EchoEngine Mode",
            value=st.session_state.get('ai_EchoEngine_mode', True),
            help="Use heuristic analysis even with API key available"
        )

def render_dataset_info():
    """Render dataset information card with elegant effects"""
    st.markdown("### 📊 Dataset")
    
    if st.session_state.dataset is not None:
        df = st.session_state.dataset
        meta = st.session_state.dataset_metadata or {}
        filename = meta.get('filename', 'Current Dataset')
        rows = len(df)
        cols = len(df.columns)
        
        st.markdown(get_dataset_info_card(filename, rows, cols), unsafe_allow_html=True)
        
        col1, col2 = st.columns(2, gap="small")
        with col1:
            if st.button("🗑️ Clear", use_container_width=True, type="secondary"):
                st.session_state.show_clear_confirmation = True
        
        with col2:
            if st.button("🔄 Reset", use_container_width=True, type="secondary"):
                from ui.app import SessionStateManager
                SessionStateManager.reset_analysis()
                st.markdown(UIComponents.render_success_glass("Analysis reset successfully"), unsafe_allow_html=True)
                time.sleep(0.5)
                st.rerun()

def render_empty_dataset_state():
    """Render empty dataset state with elegant glass effect"""
    st.markdown("### 📤 Get Started")
    
    st.markdown("""<div class="sidebar-glass-card" style='padding:1.8rem;text-align:center;animation:elegant-float 8s var(--transition-flow) infinite;'>
    <div style='font-size:3.5rem;margin-bottom:1.2rem;opacity:0.6;animation:elegant-float 6s var(--transition-flow) infinite reverse;'>📊</div>
    <h4 style='margin:0 0 0.6rem 0;font-size:1.2rem;color:var(--text);'>No Dataset Loaded</h4>
    <p style='color:var(--text-secondary);margin:0;font-size:0.92rem;line-height:1.5;'>
    Upload a dataset or try sample data to begin your analysis journey</p></div>""", unsafe_allow_html=True)

def render_confirmation_dialog():
    """Render elegant glass confirmation dialog"""
    if st.session_state.get('show_clear_confirmation', False):
        st.markdown(UIComponents.render_error_glass(
            "Confirm Dataset Clear",
            "This will remove all data and analysis. This action cannot be undone."
        ), unsafe_allow_html=True)
        
        col1, col2 = st.columns(2, gap="small")
        with col1:
            if st.button("✅ Confirm", use_container_width=True, type="primary"):
                from app import SessionStateManager
                SessionStateManager.clear_all()
                st.session_state.show_clear_confirmation = False
                st.markdown(UIComponents.render_success_glass("Dataset cleared successfully"), unsafe_allow_html=True)
                time.sleep(0.6)
                st.rerun()
        with col2:
            if st.button("❌ Cancel", use_container_width=True, type="secondary"):
                st.session_state.show_clear_confirmation = False
                st.rerun()

def premium_header(title, subtitle, icon=None):
    """
    Creates a premium animated header with glass effect.
    """
    icon_html = f'<span class="icon-span">{icon}</span>' if icon else ''
    
    header_html = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap');

        .nav-wrapper {{
            text-align: center;
            padding: 2rem 0;
            animation: soft-fade-in 1.2s var(--transition-elegant) backwards;
        }}

        .premium-h1 {{
            font-family: 'Inter', sans-serif !important;
            font-size: clamp(2rem, 4vw, 3.2rem) !important;
            font-weight: 700 !important;
            letter-spacing: -0.06em !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1 !important;
            
            background: linear-gradient(
                110deg, 
                #888 15%, 
                #fff 45%, 
                #fff 55%, 
                #888 85%
            );
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            
            animation: gentle-shimmer 10s linear infinite;
            user-select: none;
        }}

        .premium-p {{
            font-family: 'Inter', sans-serif !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            color: var(--text-tertiary) !important;
            margin-top: 1.2rem !important;
            letter-spacing: 0.2em !important;
            text-transform: uppercase;
            display: inline-block;
            position: relative;
            padding-bottom: 8px;
            animation: soft-fade-in 1.4s var(--transition-elegant);
        }}

        .premium-p::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 1px;
            background: linear-gradient(90deg, 
                transparent 0%, 
                rgba(255, 255, 255, 0.3) 15%, 
                rgba(255, 255, 255, 0.6) 50%, 
                rgba(255, 255, 255, 0.3) 85%, 
                transparent 100%
            );
            transform: scaleX(0.3);
            transform-origin: center;
            transition: transform var(--duration-slow) var(--transition-smooth);
            opacity: 0.7;
        }}

        .nav-wrapper:hover .premium-p::after {{
            transform: scaleX(1);
        }}

        .icon-span {{
            display: inline-block;
            font-size: 1.5em;
            vertical-align: middle;
            margin-right: 0.4em;
            opacity: 0.9;
            transform: translateY(-0.05em);
            animation: none !important;
            background: none !important;
            -webkit-text-fill-color: initial !important;
            filter: none !important;
            user-select: none;
        }}
    </style>

    <div class="nav-wrapper">
        <h1 class="premium-h1">
            {icon_html}{title}
        </h1>
        <p class="premium-p">
            {subtitle}
        </p>
    </div>
    """
    
    return header_html