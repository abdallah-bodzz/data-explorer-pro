"""
Data Explorer Pro - Professional HTML Export Engine
Production Grade | Version 1.0.0
Company: BODZZ | Developer: Abdallah A Khames
Clean, professional reports with subtle enhancements
"""

import datetime
import html
import secrets
from typing import Dict, List
import time
import re

import plotly.io as pio
import streamlit as st

# Import for AI report charts
from core.ai.charts_utils import create_ai_plot_from_suggestion

# ============================================================================
# CONFIGURATION & BRANDING
# ============================================================================

class AppConfig:
    """Application configuration and branding."""
    COMPANY = "BODZZ"
    DEVELOPER = "Abdallah A Khames"
    APP_NAME = "Data Explorer Pro"
    VERSION = "1.0.0"
    YEAR = datetime.datetime.now().year
    TAGLINE = "Professional Data Intelligence Platform"
    
    # Clean color scheme
    COLORS = {
        'primary': '#1a365d',
        'secondary': '#2d3748',
        'accent': '#3182ce',
        'success': '#10b981',
        'warning': '#f59e0b',
        'error': '#ef4444',
        'info': '#0ea5e9',
        'neutral-900': '#111827',
        'neutral-800': '#1f2937',
        'neutral-700': '#374151',
        'neutral-600': '#4b5563',
        'neutral-500': '#6b7280',
        'neutral-400': '#9ca3af',
        'neutral-300': '#d1d5db',
        'neutral-200': '#e5e7eb',
        'neutral-100': '#f3f4f6',
        'neutral-50': '#f9fafb',
        'white': '#ffffff',
        'black': '#000000',
    }
    
    # External resources
    PLOTLY_VERSION = "2.35.2"
    FONT_AWESOME_VERSION = "6.5.0"
    GOOGLE_FONTS = "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Source+Serif+Pro:wght@400;600;700&display=swap"

# ============================================================================
# CLEAN CSS DESIGN SYSTEM
# ============================================================================

class CleanCSSDesignSystem:
    """Clean CSS system focused on readability."""
    
    @staticmethod
    def get_all_styles() -> str:
        """Combine all CSS modules."""
        return f'''
        /* ===== DESIGN TOKENS ===== */
        :root {{
            /* COLOR SYSTEM */
            --color-primary: {AppConfig.COLORS['primary']};
            --color-secondary: {AppConfig.COLORS['secondary']};
            --color-accent: {AppConfig.COLORS['accent']};
            --color-success: {AppConfig.COLORS['success']};
            --color-warning: {AppConfig.COLORS['warning']};
            --color-error: {AppConfig.COLORS['error']};
            --color-info: {AppConfig.COLORS['info']};
            --color-white: {AppConfig.COLORS['white']};
            --color-black: {AppConfig.COLORS['black']};
            
            /* NEUTRAL HIERARCHY - LIGHT MODE */
            --color-neutral-900: {AppConfig.COLORS['neutral-900']};
            --color-neutral-800: {AppConfig.COLORS['neutral-800']};
            --color-neutral-700: {AppConfig.COLORS['neutral-700']};
            --color-neutral-600: {AppConfig.COLORS['neutral-600']};
            --color-neutral-500: {AppConfig.COLORS['neutral-500']};
            --color-neutral-400: {AppConfig.COLORS['neutral-400']};
            --color-neutral-300: {AppConfig.COLORS['neutral-300']};
            --color-neutral-200: {AppConfig.COLORS['neutral-200']};
            --color-neutral-100: {AppConfig.COLORS['neutral-100']};
            --color-neutral-50: {AppConfig.COLORS['neutral-50']};
            
            /* TYPOGRAPHY */
            --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            --font-serif: 'Source Serif Pro', Georgia, 'Times New Roman', serif;
            --font-mono: 'SF Mono', Monaco, Inconsolata, monospace;
            
            /* SPACING */
            --space-1: 0.25rem;
            --space-2: 0.5rem;
            --space-3: 0.75rem;
            --space-4: 1rem;
            --space-6: 1.5rem;
            --space-8: 2rem;
            --space-12: 3rem;
            
            /* BORDER RADIUS */
            --radius-sm: 0.125rem;
            --radius-base: 0.25rem;
            --radius-md: 0.375rem;
            --radius-lg: 0.5rem;
            --radius-xl: 0.75rem;
            --radius-full: 9999px;
            
            /* SHADOWS */
            --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
            --shadow-base: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            
            /* TRANSITIONS */
            --transition-fast: 150ms ease;
            --transition-base: 250ms ease;
        }}
        
        /* DARK MODE - CLEAN */
        [data-theme="dark"] {{
            --color-neutral-900: #f9fafb;
            --color-neutral-800: #f3f4f6;
            --color-neutral-700: #e5e7eb;
            --color-neutral-600: #d1d5db;
            --color-neutral-500: #9ca3af;
            --color-neutral-400: #6b7280;
            --color-neutral-300: #4b5563;
            --color-neutral-200: #374151;
            --color-neutral-100: #1f2937;
            --color-neutral-50: #111827;
            
            background: var(--color-neutral-50);
            color: var(--color-neutral-300);
        }}
        
        /* ===== BASE STYLES ===== */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        html {{
            scroll-behavior: smooth;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        
        body {{
            font-family: var(--font-sans);
            font-size: 1rem;
            line-height: 1.6;
            color: var(--color-neutral-800);
            background: var(--color-white);
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 var(--space-4);
            min-height: 100vh;
        }}
        
        [data-theme="dark"] body {{
            background: var(--color-neutral-50);
            color: var(--color-neutral-300);
        }}
        
        /* Clean Typography */
        h1, h2, h3, h4, h5, h6 {{
            font-family: var(--font-serif);
            font-weight: 600;
            line-height: 1.3;
            margin-bottom: var(--space-4);
            color: var(--color-neutral-900);
        }}
        
        [data-theme="dark"] h1,
        [data-theme="dark"] h2,
        [data-theme="dark"] h3,
        [data-theme="dark"] h4,
        [data-theme="dark"] h5,
        [data-theme="dark"] h6 {{
            color: var(--color-neutral-900);
        }}
        
        h1 {{ font-size: 2.5rem; margin-bottom: var(--space-6); }}
        h2 {{ font-size: 2rem; margin-bottom: var(--space-4); }}
        h3 {{ font-size: 1.5rem; margin-bottom: var(--space-4); }}
        h4 {{ font-size: 1.25rem; margin-bottom: var(--space-3); }}
        
        /* Clean paragraph colors */
        p {{
            margin-bottom: var(--space-4);
            line-height: 1.7;
            color: var(--color-neutral-700);
        }}
        
        a {{
            color: var(--color-accent);
            text-decoration: none;
            transition: color var(--transition-fast);
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        code, pre {{
            font-family: var(--font-mono);
            font-size: 0.875rem;
            background: var(--color-neutral-100);
            padding: var(--space-1) var(--space-2);
            border-radius: var(--radius-sm);
            border: 1px solid var(--color-neutral-300);
            color: var(--color-neutral-800);
        }}
        
        [data-theme="dark"] code,
        [data-theme="dark"] pre {{
            background: var(--color-neutral-100);
            color: var(--color-neutral-800);
            border-color: var(--color-neutral-300);
        }}
        
        pre {{
            padding: var(--space-3);
            overflow-x: auto;
            margin: var(--space-4) 0;
        }}
        
        /* Utility classes */
        .text-center {{ text-align: center; }}
        .text-right {{ text-align: right; }}
        .text-left {{ text-align: left; }}
        
        .mt-2 {{ margin-top: var(--space-2); }}
        .mt-4 {{ margin-top: var(--space-4); }}
        .mt-6 {{ margin-top: var(--space-6); }}
        .mt-8 {{ margin-top: var(--space-8); }}
        
        .mb-2 {{ margin-bottom: var(--space-2); }}
        .mb-4 {{ margin-bottom: var(--space-4); }}
        .mb-6 {{ margin-bottom: var(--space-6); }}
        .mb-8 {{ margin-bottom: var(--space-8); }}
        
        .py-4 {{ padding-top: var(--space-4); padding-bottom: var(--space-4); }}
        .py-6 {{ padding-top: var(--space-6); padding-bottom: var(--space-6); }}
        
        .hidden {{ display: none !important; }}
        .block {{ display: block; }}
        .flex {{ display: flex; }}
        .items-center {{ align-items: center; }}
        .justify-between {{ justify-content: space-between; }}
        .gap-2 {{ gap: var(--space-2); }}
        .gap-4 {{ gap: var(--space-4); }}
        
        /* Markdown styling */
        strong, b {{ font-weight: 700; }}
        em, i {{ font-style: italic; }}
        
        ul {{ padding-left: var(--space-6); margin: var(--space-4) 0; }}
        ol {{ padding-left: var(--space-6); margin: var(--space-4) 0; }}
        li {{ margin-bottom: var(--space-2); }}
        
        blockquote {{
            border-left: 3px solid var(--color-accent);
            padding-left: var(--space-4);
            margin: var(--space-4) 0;
            color: var(--color-neutral-600);
            font-style: italic;
        }}
        
        [data-theme="dark"] blockquote {{
            color: var(--color-neutral-500);
        }}
        
        hr {{
            border: none;
            height: 1px;
            background: var(--color-neutral-300);
            margin: var(--space-8) 0;
        }}
        
        [data-theme="dark"] hr {{
            background: var(--color-neutral-400);
        }}
        
        /* ===== COMPONENT STYLES ===== */
        /* Cards */
        .card {{
            background: var(--color-white);
            border: 1px solid var(--color-neutral-300);
            border-radius: var(--radius-lg);
            padding: var(--space-6);
            margin-bottom: var(--space-6);
            box-shadow: var(--shadow-sm);
        }}
        
        [data-theme="dark"] .card {{
            background: var(--color-neutral-100);
            border-color: var(--color-neutral-300);
        }}
        
        .card__header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: var(--space-4);
            padding-bottom: var(--space-4);
            border-bottom: 1px solid var(--color-neutral-300);
        }}
        
        .card__title {{
            font-family: var(--font-serif);
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--color-neutral-900);
            margin: 0;
        }}
        
        [data-theme="dark"] .card__title {{
            color: var(--color-neutral-900);
        }}
        
        .card__body {{
            color: var(--color-neutral-700);
            line-height: 1.7;
        }}
        
        [data-theme="dark"] .card__body {{
            color: var(--color-neutral-300);
        }}
        
        .card__footer {{
            margin-top: var(--space-4);
            padding-top: var(--space-4);
            border-top: 1px solid var(--color-neutral-300);
            color: var(--color-neutral-500);
            font-size: 0.875rem;
        }}
        
        /* Chart containers */
        .chart-container {{
            background: var(--color-white);
            border: 1px solid var(--color-neutral-300);
            border-radius: var(--radius-lg);
            padding: var(--space-6);
            margin: var(--space-6) 0;
        }}
        
        [data-theme="dark"] .chart-container {{
            background: var(--color-neutral-100);
            border-color: var(--color-neutral-300);
        }}
        
        .chart__header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--space-4);
            padding-bottom: var(--space-4);
            border-bottom: 1px solid var(--color-neutral-300);
        }}
        
        .chart__title {{
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--color-neutral-900);
            margin: 0;
        }}
        
        [data-theme="dark"] .chart__title {{
            color: var(--color-neutral-900);
        }}
        
        .chart__type {{
            display: inline-flex;
            align-items: center;
            padding: var(--space-1) var(--space-3);
            background: var(--color-primary);
            color: var(--color-white);
            border-radius: var(--radius-md);
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        /* Metrics */
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: var(--space-4);
            margin: var(--space-6) 0;
        }}
        
        .metric-card {{
            background: var(--color-white);
            border: 1px solid var(--color-neutral-300);
            border-radius: var(--radius-lg);
            padding: var(--space-4);
        }}
        
        [data-theme="dark"] .metric-card {{
            background: var(--color-neutral-100);
            border-color: var(--color-neutral-300);
        }}
        
        .metric__label {{
            font-size: 0.875rem;
            color: var(--color-neutral-600);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: var(--space-2);
        }}
        
        .metric__value {{
            font-size: 1.875rem;
            font-weight: 700;
            color: var(--color-neutral-900);
            line-height: 1;
            margin-bottom: var(--space-2);
        }}
        
        [data-theme="dark"] .metric__value {{
            color: var(--color-neutral-900);
        }}
        
        /* Badges */
        .badge {{
            display: inline-flex;
            align-items: center;
            padding: var(--space-1) var(--space-3);
            font-size: 0.75rem;
            font-weight: 600;
            border-radius: var(--radius-full);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            white-space: nowrap;
        }}
        
        .badge--primary {{
            background: var(--color-primary);
            color: var(--color-white);
        }}
        
        .badge--outline {{
            background: transparent;
            color: var(--color-neutral-600);
            border: 1px solid var(--color-neutral-300);
        }}
        
        [data-theme="dark"] .badge--outline {{
            color: var(--color-neutral-400);
            border-color: var(--color-neutral-400);
        }}
        
        /* Action Bar */
        .action-bar {{
            position: fixed;
            bottom: var(--space-6);
            right: var(--space-6);
            z-index: 1001;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid var(--color-neutral-300);
            border-radius: var(--radius-xl);
            padding: var(--space-3);
            box-shadow: var(--shadow-lg);
        }}
        
        [data-theme="dark"] .action-bar {{
            background: rgba(31, 41, 55, 0.95);
            border-color: var(--color-neutral-400);
        }}
        
        .action-bar__container {{
            display: flex;
            gap: var(--space-2);
        }}
        
        .action-btn {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            width: 64px;
            height: 64px;
            border-radius: var(--radius-lg);
            border: 1px solid var(--color-neutral-300);
            background: var(--color-white);
            color: var(--color-neutral-700);
            cursor: pointer;
            transition: all var(--transition-base);
            font-size: 0.75rem;
            font-family: var(--font-sans);
        }}
        
        [data-theme="dark"] .action-btn {{
            background: var(--color-neutral-200);
            color: var(--color-neutral-800);
            border-color: var(--color-neutral-400);
        }}
        
        .action-btn:hover {{
            background: var(--color-accent);
            color: var(--color-white);
            border-color: var(--color-accent);
        }}
        
        [data-theme="dark"] .action-btn:hover {{
            background: var(--color-accent);
            color: var(--color-white);
        }}
        
        .action-btn i {{
            font-size: 1.25rem;
            margin-bottom: var(--space-1);
        }}
        
        /* Table of Contents */
        .table-of-contents {{
            position: fixed;
            top: 100px;
            right: 20px;
            width: 280px;
            max-height: calc(100vh - 200px);
            overflow-y: auto;
            background: var(--color-white);
            border: 1px solid var(--color-neutral-300);
            border-radius: var(--radius-lg);
            padding: var(--space-4);
            z-index: 1000;
            box-shadow: var(--shadow-lg);
            display: none;
        }}
        
        .table-of-contents.visible {{
            display: block;
        }}
        
        [data-theme="dark"] .table-of-contents {{
            background: var(--color-neutral-100);
            border-color: var(--color-neutral-300);
        }}
        
        .toc-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--space-4);
            padding-bottom: var(--space-3);
            border-bottom: 1px solid var(--color-neutral-300);
        }}
        
        .toc-title {{
            font-family: var(--font-serif);
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--color-neutral-900);
            margin: 0;
        }}
        
        .toc-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        
        .toc-item {{
            margin-bottom: var(--space-2);
        }}
        
        .toc-link {{
            display: block;
            color: var(--color-neutral-700);
            text-decoration: none;
            padding: var(--space-2) var(--space-3);
            border-radius: var(--radius-base);
            font-family: var(--font-sans);
            font-size: 0.875rem;
        }}
        
        [data-theme="dark"] .toc-link {{
            color: var(--color-neutral-300);
        }}
        
        .toc-link:hover {{
            background: var(--color-neutral-100);
            color: var(--color-accent);
        }}
        
        .toc-link.active {{
            background: var(--color-accent);
            color: var(--color-white);
            font-weight: 600;
        }}
        
        /* Report Sections */
        .report-section {{
            break-inside: avoid;
        }}
        
        .report-container {{
            padding: var(--space-8) 0;
        }}
        
        /* Divider */
        .divider {{
            height: 1px;
            background: var(--color-neutral-300);
            margin: var(--space-8) 0;
            border: none;
        }}
        
        /* ===== PRINT STYLES ===== */
        @media print {{
            .no-print {{
                display: none !important;
            }}
            
            .table-of-contents,
            .action-bar {{
                display: none !important;
            }}
            
            body {{
                font-size: 11pt !important;
                line-height: 1.4 !important;
                color: #000 !important;
                background: white !important;
                max-width: 100% !important;
                padding: 0 !important;
            }}
            
            .card, .chart-container {{
                break-inside: avoid;
                border: 1px solid #ddd !important;
                box-shadow: none !important;
            }}
            
            h1, h2, h3 {{
                color: #000 !important;
                page-break-after: avoid;
            }}
            
            a {{
                color: #000 !important;
                text-decoration: underline;
            }}
            
            .js-plotly-plot {{
                break-inside: avoid !important;
                max-height: 7in !important;
            }}
            
            .js-plotly-plot .modebar {{
                display: none !important;
            }}
        }}
        
        /* ===== RESPONSIVE ===== */
        @media (max-width: 768px) {{
            body {{
                padding: 0 var(--space-2);
            }}
            
            .metric-grid {{
                grid-template-columns: 1fr;
            }}
            
            .action-bar {{
                bottom: var(--space-2);
                right: var(--space-2);
            }}
            
            .action-btn {{
                width: 56px;
                height: 56px;
            }}
            
            .table-of-contents {{
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                width: 100%;
                max-height: 100vh;
                margin: 0;
                border-radius: 0;
                z-index: 1002;
            }}
            
            h1 {{ font-size: 2rem; }}
            h2 {{ font-size: 1.5rem; }}
            h3 {{ font-size: 1.25rem; }}
        }}
        '''

# ============================================================================
# CLEAN JAVASCRIPT (NO TOASTS, SIMPLE FUNCTIONALITY)
# ============================================================================

class CleanJavaScriptEnhancer:
    """Clean JavaScript with essential functionality."""
    
    @staticmethod
    def get_all_js(include_toc: bool = True) -> str:
        """Get all JavaScript functionality."""
        toc_js = '''
        // Table of Contents
        function generateTableOfContents() {
            const sections = document.querySelectorAll('h2, h3');
            if (sections.length < 3) {
                return null;
            }
            
            const toc = document.createElement('nav');
            toc.className = 'table-of-contents card no-print';
            toc.setAttribute('aria-label', 'Table of Contents');
            toc.id = 'table-of-contents';
            
            let tocHTML = '<div class="toc-header"><h3 class="toc-title">📑 Contents</h3></div>';
            tocHTML += '<ul class="toc-list" role="list">';
            
            sections.forEach((section, index) => {
                if (!section.id) {
                    section.id = 'section-' + (index + 1);
                }
                
                const isH3 = section.tagName === 'H3';
                const levelClass = isH3 ? 'h3' : '';
                
                tocHTML += `
                    <li class="toc-item" role="listitem">
                        <a href="#${section.id}" class="toc-link ${levelClass}" 
                           onclick="event.preventDefault(); scrollToSection('${section.id}')">
                            ${section.textContent}
                        </a>
                    </li>
                `;
            });
            
            tocHTML += '</ul>';
            toc.innerHTML = tocHTML;
            
            return toc;
        }
        
        // Smooth scrolling
        function scrollToSection(sectionId) {
            const element = document.getElementById(sectionId);
            if (element) {
                const headerOffset = 100;
                const elementPosition = element.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
                
                // Update active TOC item
                const tocLinks = document.querySelectorAll('.toc-link');
                tocLinks.forEach(link => link.classList.remove('active'));
                const activeLink = document.querySelector(`a[href="#${sectionId}"]`);
                if (activeLink) {
                    activeLink.classList.add('active');
                }
                
                // Close TOC on mobile
                if (window.innerWidth < 768) {
                    const toc = document.getElementById('table-of-contents');
                    if (toc) {
                        toc.classList.remove('visible');
                    }
                }
            }
        }
        ''' if include_toc else '''
        // Table of Contents disabled
        function generateTableOfContents() { return null; }
        function scrollToSection(sectionId) {
            const element = document.getElementById(sectionId);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
            }
        }
        '''
        
        toc_button_html = '''
        <button class="action-btn toc-toggle" 
                aria-label="Show/Hide Table of Contents" 
                title="Table of Contents"
                role="button">
            <i class="fas fa-list" aria-hidden="true"></i>
            <span>Contents</span>
        </button>
        ''' if include_toc else ''
        
        toc_button_js = '''
        document.querySelector('.toc-toggle').addEventListener('click', () => {
            const toc = document.getElementById('table-of-contents');
            if (toc) {
                toc.classList.toggle('visible');
                const icon = document.querySelector('.toc-toggle i');
                if (icon) {
                    icon.className = toc.classList.contains('visible') ? 'fas fa-times' : 'fas fa-list';
                }
            }
        });
        
        // Close TOC when clicking outside
        document.addEventListener('click', (e) => {
            const toc = document.getElementById('table-of-contents');
            const tocToggle = document.querySelector('.toc-toggle');
            if (toc && toc.classList.contains('visible') && 
                !toc.contains(e.target) && !tocToggle.contains(e.target)) {
                toc.classList.remove('visible');
                const icon = document.querySelector('.toc-toggle i');
                if (icon) {
                    icon.className = 'fas fa-list';
                }
            }
        });
        ''' if include_toc else ''
        
        toc_init_js = '''
        // Generate TOC
        const toc = generateTableOfContents();
        if (toc) {
            document.body.appendChild(toc);
            
            // Position above action bar
            const actionBar = document.querySelector('.action-bar');
            if (actionBar && window.innerWidth > 768) {
                const actionBarRect = actionBar.getBoundingClientRect();
                toc.style.top = (actionBarRect.top - toc.offsetHeight - 20) + 'px';
            }
        }
        ''' if include_toc else '''
        // TOC disabled
        '''
        
        return f'''
            // ===== CLEAN FUNCTIONALITY =====
            
            // Theme toggle
            function toggleTheme() {{
                const html = document.documentElement;
                const currentTheme = html.getAttribute('data-theme');
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                
                html.setAttribute('data-theme', newTheme);
                localStorage.setItem('report-theme', newTheme);
                
                // Update icon
                const icon = document.querySelector('.theme-toggle i');
                if (icon) {{
                    icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
                }}
            }}
            
            {toc_js}
            
            // Simple Action Bar
            function createActionBar() {{
                const actionBar = document.createElement('div');
                actionBar.className = 'action-bar no-print';
                actionBar.setAttribute('role', 'toolbar');
                actionBar.setAttribute('aria-label', 'Report Actions');
                
                actionBar.innerHTML = `
                    <div class="action-bar__container" role="group">
                        <button class="action-btn print-btn" 
                                aria-label="Print Report" 
                                title="Print Report"
                                role="button">
                            <i class="fas fa-print" aria-hidden="true"></i>
                            <span>Print</span>
                        </button>
                        <button class="action-btn theme-toggle" 
                                aria-label="Toggle Theme" 
                                title="Toggle Theme"
                                role="button">
                            <i class="fas fa-moon" aria-hidden="true"></i>
                            <span>Theme</span>
                        </button>
                        {toc_button_html}
                    </div>
                `;
                
                document.body.appendChild(actionBar);
                
                // Bind events
                document.querySelector('.print-btn').addEventListener('click', () => {{
                    window.print();
                }});
                
                document.querySelector('.theme-toggle').addEventListener('click', toggleTheme);
                
                {toc_button_js}
            }}
            
            // Initialize
            function initializeReport() {{
                // Set initial theme
                const savedTheme = localStorage.getItem('report-theme');
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');
                
                document.documentElement.setAttribute('data-theme', initialTheme);
                
                // Update theme icon
                const icon = document.querySelector('.theme-toggle i');
                if (icon) {{
                    icon.className = initialTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
                }}
                
                {toc_init_js}
                
                // Create action bar
                createActionBar();
            }}
            
            // Wait for DOM
            document.addEventListener('DOMContentLoaded', initializeReport);
            '''

# ============================================================================
# CLEAN REPORT GENERATOR
# ============================================================================

class CleanReportGenerator:
    """Generate clean HTML reports."""
    
    @staticmethod
    def create_executive_summary(title: str, author: str) -> str:
        """Create clean executive summary section."""
        timestamp = datetime.datetime.now().strftime("%B %d, %Y")
        report_id = f"RPT-{datetime.datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
        
        return f'''
        <section class="executive-summary card">
            <div class="card__header">
                <div>
                    <h1>{html.escape(title)}</h1>
                    <p class="text-neutral-500 mt-2">Data Analysis Report • {AppConfig.APP_NAME}</p>
                </div>
                <span class="badge badge--primary">REPORT</span>
            </div>
            
            <div class="divider"></div>
            
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric__label">Author</div>
                    <div class="metric__value text-lg">{html.escape(author)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric__label">Date</div>
                    <div class="metric__value text-lg">{timestamp}</div>
                </div>
                <div class="metric-card">
                    <div class="metric__label">Report ID</div>
                    <div class="metric__value text-lg"><code>{report_id}</code></div>
                </div>
            </div>
        </section>
        '''
    
    @staticmethod
    def create_section(section: Dict, index: int, charts: List[Dict] = None) -> str:
        """Create a clean report section."""
        section_id = section.get('id', f'section-{index + 1}')
        section_title = section.get('title', f'Section {index + 1}')
        
        # Format content
        content = section.get('content', '')
        formatted_content = CleanReportGenerator._parse_markdown(content)
        
        # Get charts for this section
        section_charts = []
        chart_ids = section.get('chart_ids', [])
        for chart_id in chart_ids:
            for chart in (charts or []):
                if chart.get('id') == chart_id:
                    section_charts.append(chart)
                    break
        
        # Build section HTML
        section_html = f'''
        <section id="{section_id}" class="report-section card">
            <div class="card__header">
                <div>
                    <h2 class="card__title">
                        <span class="text-neutral-500">{index + 1}.</span>
                        {html.escape(section_title)}
                    </h2>
                </div>
                <span class="badge badge--outline">SECTION</span>
            </div>
            
            <div class="card__body">
                {formatted_content}
        '''
        
        # Add charts if any
        if section_charts:
            section_html += '<div class="mt-6">'
            for chart in section_charts:
                chart_html = CleanReportGenerator._create_chart_html(chart)
                section_html += chart_html
            section_html += '</div>'
        
        section_html += '''
            </div>
            
            <div class="card__footer">
                <div class="flex justify-between text-xs">
                </div>
            </div>
        </section>
        '''
        
        return section_html
    
    @staticmethod
    def create_footer() -> str:
        """Create clean report footer."""
        return f'''
        <footer class="report-footer card mt-12">
            <div class="card__body">
                <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: var(--space-6);">
                    <div>
                        <h3 class="text-lg font-semibold mb-3">{AppConfig.COMPANY}</h3>
                        <p class="text-sm text-neutral-700">
                            Data Analytics<br>
                            Professional Reports
                        </p>
                    </div>
                    
                    <div>
                        <h3 class="text-lg font-semibold mb-3">Report Information</h3>
                        <p class="text-sm text-neutral-700">
                            Generated: {datetime.datetime.now().strftime("%Y-%m-%d")}<br>
                            Version: {AppConfig.VERSION}<br>
                            Application: {AppConfig.APP_NAME}
                        </p>
                    </div>                    
                </div>
                
                <div class="divider mt-6"></div>
                
                <div class="text-center mt-4">
                    <p class="text-sm text-neutral-600 mb-2">
                        <i class="fas fa-code mr-2"></i>
                        Developed by <strong>{AppConfig.DEVELOPER}</strong> | 
                        <i class="fas fa-bolt mx-2"></i>
                        Powered by <strong>{AppConfig.APP_NAME}</strong>
                    </p>
                    <p class="text-xs text-neutral-500">
                        © 2026 {AppConfig.COMPANY} • All rights reserved • v{AppConfig.VERSION}
                    </p>
                </div>
            </div>
        </footer>
        '''
    
    @staticmethod
    def _create_chart_html(chart: Dict) -> str:
        """Create HTML for a single chart."""
        chart_type = chart.get('chart_type', 'chart').upper()
        chart_name = chart.get('name', 'Visualization')
        chart_desc = chart.get('description', '')
        chart_html = chart.get('html', '')
        
        return f'''
        <div class="chart-container mt-4">
            <div class="chart__header">
                <h3 class="chart__title">{html.escape(chart_name)}</h3>
                <span class="chart__type">{chart_type}</span>
            </div>
            
            {chart_html}
            
            {f'<p class="mt-4 text-sm text-neutral-600">{html.escape(chart_desc)}</p>' if chart_desc else ''}
        </div>
        '''
    
    @staticmethod
    def _parse_markdown(text: str) -> str:
        """Parse markdown text to HTML."""
        if not text:
            return '<p class="text-neutral-500 italic"></p>'
        
        # Escape HTML
        text = html.escape(text)
        
        lines = text.split('\n')
        output = []
        in_list = False
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped and not in_list:
                if output and not output[-1].endswith('</p>'):
                    output.append('<p></p>')
                continue
            
            # Headers
            if stripped.startswith('#### '):
                output.append(f'<h4 class="text-lg font-semibold mt-4">{stripped[5:]}</h4>')
            elif stripped.startswith('### '):
                output.append(f'<h3 class="text-xl font-semibold mt-4">{stripped[4:]}</h3>')
            elif stripped.startswith('## '):
                output.append(f'<h2 class="text-2xl font-semibold mt-6">{stripped[3:]}</h2>')
            elif stripped.startswith('# '):
                output.append(f'<h1 class="text-3xl font-bold mt-6">{stripped[2:]}</h1>')
            
            # Lists
            elif re.match(r'^[\*\-] ', stripped):
                if not in_list:
                    output.append('<ul class="list-disc pl-6 my-4">')
                    in_list = True
                content = stripped[2:]
                # Process inline formatting
                content = CleanReportGenerator._process_inline(content)
                output.append(f'<li class="mb-1">{content}</li>')
            elif re.match(r'^\d+\. ', stripped):
                if not in_list:
                    output.append('<ol class="list-decimal pl-6 my-4">')
                    in_list = True
                content = stripped[3:]
                content = CleanReportGenerator._process_inline(content)
                output.append(f'<li class="mb-1">{content}</li>')
            
            # Regular paragraphs
            else:
                if in_list:
                    output.append('</ul>' if stripped.startswith('- ') or stripped.startswith('* ') else '</ol>')
                    in_list = False
                
                if stripped:
                    processed_line = CleanReportGenerator._process_inline(stripped)
                    output.append(f'<p class="my-3">{processed_line}</p>')
        
        if in_list:
            output.append('</ul>')
        
        return '\n'.join(output)
    
    @staticmethod
    def _process_inline(text: str) -> str:
        """Process inline markdown formatting."""
        # Bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
        
        # Italic
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)
        
        # Inline code
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        return text
    
    @staticmethod
    def generate_html_report(title: str, author: str, sections: List[Dict], 
                           charts: List[Dict] = None, include_toc: bool = True) -> str:
        """Generate clean HTML report."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_id = f"RPT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Build report content
        report_content = []
        report_content.append(CleanReportGenerator.create_executive_summary(title, author))
        
        for i, section in enumerate(sections):
            report_content.append(CleanReportGenerator.create_section(section, i, charts))
        
        report_content.append(CleanReportGenerator.create_footer())
        
        # Combine everything
        content = '\n'.join(report_content)
        
        return f'''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <title>{html.escape(title)} | {AppConfig.APP_NAME}</title>
    <meta name="description" content="Data analysis report">
    <meta name="author" content="{author}">
    <meta name="generator" content="{AppConfig.APP_NAME} {AppConfig.VERSION}">
    
    <!-- External Resources -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="{AppConfig.GOOGLE_FONTS}" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/{AppConfig.FONT_AWESOME_VERSION}/css/all.min.css">
    
    <!-- Plotly.js -->
    <script src="https://cdn.plot.ly/plotly-{AppConfig.PLOTLY_VERSION}.min.js"></script>
    
    <!-- Clean Styles -->
    <style>
        {CleanCSSDesignSystem.get_all_styles()}
    </style>
</head>
<body>
    <div class="report-container">
        <main id="main-content">
            {content}
        </main>
    </div>
    
    <!-- Clean JavaScript -->
    <script>
        {CleanJavaScriptEnhancer.get_all_js(include_toc=include_toc)}
    </script>
</body>
</html>'''

# ============================================================================
# STREAMLIT INTERFACES
# ============================================================================

def export_chart_interface():
    """Chart export interface."""
    if not st.session_state.get('current_chart'):
        with st.container(border=True):
            st.info("📊 **No chart available** - Create a chart in Chart Studio first.")
        return
    
    with st.container(border=True):
        st.subheader("📤 Export Chart")
        
        chart_data = st.session_state.current_chart
        chart_title = chart_data.get('config', {}).get('title', 'Chart Analysis')
        
        # Input fields
        col1, col2 = st.columns(2)
        with col1:
            report_title = st.text_input(
                "Report Title",
                value=chart_title,
                key="export_chart_title"
            )
        with col2:
            author_name = st.text_input(
                "Author Name",
                value="Data Analyst",
                key="export_chart_author"
            )
        
        report_description = st.text_area(
            "Report Description",
            value="",
            key="export_chart_desc",
            height=100
        )
        
        export_format = st.radio(
            "Export Format",
            ["📄 HTML Report", "🖼️ High-Res Image"],
            horizontal=True,
            key="export_chart_format"
        )
        
        if st.button("🚀 Generate Export", type="primary", use_container_width=True):
            _export_chart_report(report_title, author_name, report_description, export_format)

def export_ai_interface():
    """AI analysis export interface."""
    if not st.session_state.get("chat_history"):
        with st.container(border=True):
            st.info("💬 **No AI conversation history** - Start a conversation with AI Copilot first.")
        return
    
    with st.container(border=True):
        st.subheader("🤖 Export AI Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            report_title = st.text_input(
                "Report Title", 
                "AI-Powered Data Analysis",
                key="ai_export_title"
            )
        with col2:
            analyst_name = st.text_input(
                "Analyst Name",
                "AI Assistant & Data Team",
                key="ai_export_analyst"
            )

        if st.button("📄 Generate HTML Report", use_container_width=True, type="primary"):
            _export_ai_html_report(report_title, analyst_name)

def export_report_interface():
    """Report builder export interface."""
    sections = st.session_state.get('report_builder_sections', [])
    charts = st.session_state.get('report_builder_charts', [])
    
    if not sections:
        with st.container(border=True):
            st.info("📝 **Report builder empty** - Add content in the Report Builder tab first.")
        return
    
    with st.container(border=True):
        st.subheader("📋 Export Report")
        
        col1, col2 = st.columns(2)
        with col1:
            report_title = st.text_input(
                "Report Title", 
                "Data Analysis Report",
                key="rb_export_title"
            )
        with col2:
            author_name = st.text_input(
                "Author / Organization",
                "Data Analysis Team",
                key="rb_export_author"
            )
        
        if st.button("🎯 Generate Professional Report", type="primary", use_container_width=True):
            with st.spinner("Creating report..."):
                success = _export_report_builder_html(report_title, author_name, sections, charts)
                
                if success:
                    st.success("✅ Report generated!")
                else:
                    st.error("❌ Report generation failed.")

# ============================================================================
# IMPLEMENTATION FUNCTIONS
# ============================================================================

def _export_chart_report(title: str, author: str, description: str, export_format: str):
    """Export current chart as report."""
    try:
        chart_data = st.session_state.current_chart
        
        if not chart_data or not chart_data.get('figure'):
            st.error("❌ No chart available")
            return
        
        # Generate HTML for chart
        chart_html = pio.to_html(
            chart_data['figure'],
            full_html=False,
            include_plotlyjs=False,
            config={'responsive': True}
        )
        
        # Create chart object
        chart_for_export = {
            'id': f"chart_{int(time.time())}",
            'name': title,
            'chart_type': chart_data.get('type', 'visualization').lower(),
            'html': chart_html,
            'description': description
        }
        
        # Create section
        content = description if description.strip() else "Analysis of the chart above."
        sections = [{
            'id': 'chart-analysis',
            'title': 'Analysis',
            'content': content,
            'chart_ids': [chart_for_export['id']]
        }]
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if "HTML Report" in export_format:
            html_content = CleanReportGenerator.generate_html_report(
                title=title,
                author=author,
                sections=sections,
                charts=[chart_for_export],
                include_toc=False
            )
            
            st.download_button(
                "📥 Download HTML Report",
                data=html_content,
                file_name=f"report_{timestamp}.html",
                mime="text/html",
                key=f"chart_html_{timestamp}",
                use_container_width=True
            )
        
        if "High-Res Image" in export_format and chart_data.get('figure'):
            img_bytes = pio.to_image(chart_data['figure'], format='png', width=1200, height=800)
            
            st.download_button(
                "🖼️ Download PNG",
                data=img_bytes,
                file_name=f"chart_{timestamp}.png",
                mime="image/png",
                key=f"chart_png_{timestamp}",
                use_container_width=True
            )
    
    except Exception as e:
        st.error(f"❌ Export failed: {str(e)[:100]}")

def _export_ai_html_report(title: str, analyst: str):
    """Export AI conversation as HTML report."""
    try:
        messages = st.session_state.get("chat_history", [])
        
        if not messages:
            st.error("❌ No AI conversation to export")
            return
        
        # Process messages
        sections = []
        charts = []
        
        df = st.session_state.get('dataset')
        
        for i, msg in enumerate(messages):
            if msg['role'] == 'user':
                sections.append({
                    'id': f"question-{i}",
                    'title': f"Question {len([s for s in sections if 'Question' in s.get('title', '')]) + 1}",
                    'content': f"**User Query:** {msg.get('content', '')}",
                    'chart_ids': []
                })
            elif msg['role'] == 'assistant' and isinstance(msg.get('content'), dict):
                content = msg['content']
                
                section_id = f"analysis-{i}"
                section_charts = []
                
                if content.get('charts') and df is not None:
                    for j, chart_suggestion in enumerate(content.get('charts', [])):
                        try:
                            chart_fig = create_ai_plot_from_suggestion(df, chart_suggestion)
                            if chart_fig:
                                chart_html = pio.to_html(
                                    chart_fig,
                                    full_html=False,
                                    include_plotlyjs=False,
                                    config={'responsive': True}
                                )
                                
                                chart_id = f"ai_chart_{i}_{j}"
                                chart_name = chart_suggestion.get('title', f'Chart {j+1}')
                                
                                charts.append({
                                    'id': chart_id,
                                    'name': chart_name,
                                    'chart_type': chart_suggestion.get('chart_type', 'chart'),
                                    'html': chart_html,
                                    'description': chart_suggestion.get('description', '')
                                })
                                
                                section_charts.append(chart_id)
                        except Exception:
                            pass
                
                section_content = content.get('story', 'AI analysis completed.')
                
                if content.get('insights'):
                    section_content += "\n\n### Key Insights\n"
                    for insight in content.get('insights', []):
                        if isinstance(insight, dict):
                            section_content += f"- **{insight.get('title', 'Insight')}**: {insight.get('description', '')}\n"
                        else:
                            section_content += f"- {insight}\n"
                
                sections.append({
                    'id': section_id,
                    'title': f"Analysis {len([s for s in sections if 'Analysis' in s.get('title', '')]) + 1}",
                    'content': section_content,
                    'chart_ids': section_charts
                })
        
        # Generate report
        include_toc = len(sections) > 1
        html_content = CleanReportGenerator.generate_html_report(
            title=title,
            author=analyst,
            sections=sections,
            charts=charts,
            include_toc=include_toc
        )
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        st.download_button(
            "📥 Download AI Analysis Report",
            data=html_content,
            file_name=f"ai_analysis_{timestamp}.html",
            mime="text/html",
            key=f"ai_html_{timestamp}",
            use_container_width=True
        )
    
    except Exception as e:
        st.error(f"❌ AI export failed: {str(e)[:100]}")

def _export_report_builder_html(title: str, author: str, sections: List[Dict], charts: List[Dict]) -> bool:
    """Export report builder content as HTML."""
    try:
        if not sections:
            st.error("❌ No content in report builder")
            return False
        
        # Prepare charts
        export_charts = []
        for chart in charts:
            if chart.get('figure'):
                try:
                    chart_html = pio.to_html(
                        chart['figure'],
                        full_html=False,
                        include_plotlyjs=False,
                        config={'responsive': True}
                    )
                    
                    export_charts.append({
                        'id': chart['id'],
                        'name': chart.get('name', 'Unnamed Chart'),
                        'chart_type': chart.get('chart_type', 'chart'),
                        'html': chart_html,
                        'description': chart.get('description', '')
                    })
                except Exception:
                    pass
        
        include_toc = len(sections) > 1
        
        html_content = CleanReportGenerator.generate_html_report(
            title=title,
            author=author,
            sections=sections,
            charts=export_charts,
            include_toc=include_toc
        )
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        st.download_button(
            "📥 Download Report",
            data=html_content,
            file_name=f"report_{timestamp}.html",
            mime="text/html",
            key=f"report_html_{timestamp}",
            use_container_width=True
        )
        
        return True
    
    except Exception as e:
        st.error(f"❌ Report export failed: {str(e)[:100]}")
        return False

# ============================================================================
# MAIN EXPORTS
# ============================================================================

__all__ = [
    'export_chart_interface',
    'export_ai_interface',
    'export_report_interface'
]