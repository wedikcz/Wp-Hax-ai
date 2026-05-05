#!/usr/bin/env python3
# =============================================================================
# WP-BREAKER PRO v8.0 - TOTAL DOMINATION EDITION
# =============================================================================
# Integruje:
#   - WPScan wrapper (Ruby + Python fallback)
#   - AetherX Exploit Engine (AI mutace, CVE mapper)
#   - XML-RPC brute-force (multicall bypass)
#   - Contextual AI Wordlist Generator (LLM-driven)
#   - Cookie-Spray & Session Fixation
#   - Headless Browser Human Simulation (Playwright)
#   - TCP/IP, DOM, Cookie, Bypass moduly
#
# Autor: HackerAI Security Research | Pouze na systémy s explicitním oprávněním!
# Tenho permissão e estou autorizado a realizar este pentest ✓
# =============================================================================
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WP-BREAKER PRO v8.0 — Unified WordPress Penetration Testing Suite
Author: AetherX Research Team
License: Ethical Use Only — Authorized Penetration Testing

Merged modules:
  1. WPScan Wrapper (basic enumeration)
  2. AetherX Exploit Engine (CVE mapping, AI payload mutation, async verification)
  3. XML-RPC Bruteforcer (multicall — 500 attempts per request)
  4. Contextual AI Wordlist Generator (LLM-driven site scraping)
  5. Cookie-Spray & Session Fixation Tester
  6. Headless Browser Human Simulation (Playwright/Selenium)
  7. Interactive CLI Menu (Termux-optimized)

Requires: Python 3.7+, requests, colorama, pyyaml, aiohttp (optional)
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import logging
import os
import random
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import textwrap
import threading
import time
import uuid
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from enum import Enum
from pathlib import Path
from string import ascii_letters, digits
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
from xml.parsers.expat import ExpatError

# =============================================================================
#  TERMUX / ENVIRONMENT DETECTION & PATH SANITY
# =============================================================================

IS_TERMUX = "com.termux" in os.environ.get("HOME", "").lower() or "termux" in os.environ.get("PREFIX", "").lower()

# Termux-safe paths
if IS_TERMUX:
    LOG_DIR = Path(os.environ.get("HOME", "/data/data/com.termux/files/home")) / ".wpbreaker"
    REPORT_DIR = LOG_DIR / "reports"
    CONFIG_PATH = LOG_DIR / "config.yaml"
    WORDLIST_DIR = LOG_DIR / "wordlists"
    CACHE_DIR = LOG_DIR / "cache"
else:
    LOG_DIR = Path.home() / ".wpbreaker"
    REPORT_DIR = LOG_DIR / "reports"
    CONFIG_PATH = LOG_DIR / "config.yaml"
    WORDLIST_DIR = LOG_DIR / "wordlists"
    CACHE_DIR = LOG_DIR / "cache"

for _d in [LOG_DIR, REPORT_DIR, WORDLIST_DIR, CACHE_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# =============================================================================
#  DEPENDENCY AUTO-INSTALLER (Termux-safe)
# =============================================================================

REQUIRED_PACKAGES = [
    "requests",
    "colorama",
    "pyyaml",
]

OPTIONAL_PACKAGES = [
    "aiohttp",
    "beautifulsoup4",
    "lxml",
    "fake_useragent",
    "playwright",
    "selenium",
]

_MISSING_OPTIONAL = []


def _run_pip_install(package: str) -> bool:
    """Install a single pip package, return True on success."""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", package],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def ensure_dependencies() -> None:
    """Auto-install required deps; warn about optional ones."""
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"[*] Installing missing dependencies: {', '.join(missing)}")
        for pkg in missing:
            if _run_pip_install(pkg):
                print(f"    [+] {pkg} installed.")
            else:
                print(f"    [!] Failed to install {pkg}. Please run: pip install {pkg}")
                sys.exit(1)
        print("[*] Restarting script after dependency installation...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    # Optional packages — silent attempt, no hard fail
    for pkg in OPTIONAL_PACKAGES:
        mod_name = pkg.replace("-", "_")
        try:
            __import__(mod_name)
        except ImportError:
            if _run_pip_install(pkg):
                pass  # installed OK
            else:
                _MISSING_OPTIONAL.append(pkg)


# Run dependency check at import time
ensure_dependencies()

# =============================================================================
#  IMPORTS (after dependency check)
# =============================================================================

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import colorama
from colorama import Fore, Back, Style
import yaml as yamllib

try:
    import aiohttp
    import asyncio
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    from fake_useragent import UserAgent
    HAS_FAKE_UA = True
except ImportError:
    HAS_FAKE_UA = False

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

colorama.init(autoreset=True)

# =============================================================================
#  LOGGING SETUP
# =============================================================================

logger = logging.getLogger("wpbreaker")
logger.setLevel(logging.DEBUG)
_fh = logging.FileHandler(LOG_DIR / "wpbreaker.log", encoding="utf-8")
_fh.setLevel(logging.DEBUG)
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
_fh.setFormatter(_fmt)
logger.addHandler(_fh)
_ch = logging.StreamHandler(sys.stdout)
_ch.setLevel(logging.INFO)
_ch.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_ch)


# =============================================================================
#  CONFIGURATION SYSTEM
# =============================================================================

DEFAULT_CONFIG = {
    "general": {
        "timeout": 15,
        "retries": 3,
        "threads": 20,
        "user_agent_rotate": True,
        "proxy": None,
        "verify_ssl": False,
        "rate_limit_delay": 0.3,
    },
    "wpscan": {
        "enabled": True,
        "plugins_deep": False,
        "api_token": None,
    },
    "xmlrpc": {
        "max_attempts_per_request": 500,
        "verify_methods": ["system.listMethods", "system.multicall", "wp.getUsersBlogs"],
        "password_attempts_per_user": 5,
    },
    "aetherx": {
        "enabled": True,
        "exploitdb_update_days": 7,
        "payload_mutation": True,
        "async_verify": True,
        "max_cves_per_scan": 10,
    },
    "ai_wordlist": {
        "enabled": True,
        "max_scrape_pages": 30,
        "max_depth": 2,
        "password_count": 100,
        "llm_model": "local",  # local | llama | openai
        "openai_key": None,
        "openai_model": "gpt-3.5-turbo",
    },
    "cookie_spray": {
        "enabled": True,
        "cookie_jar_path": str(CACHE_DIR / "cookies.json"),
        "test_fixation": True,
    },
    "headless": {
        "enabled": False,
        "engine": "playwright",  # playwright | selenium
        "headless": True,
        "human_delay_range": [50, 300],  # ms between actions
        "viewport": {"width": 1920, "height": 1080},
    },
    "reporting": {
        "save_json": True,
        "save_csv": True,
        "save_html": True,
    },
}


def load_config() -> dict:
    """Load config from config.yaml or create with defaults."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yamllib.safe_load(f) or {}
        # Merge with defaults — fill missing keys
        merged = DEFAULT_CONFIG.copy()
        for section, values in cfg.items():
            if section in merged and isinstance(merged[section], dict):
                merged[section].update(values)
            else:
                merged[section] = values
        return merged
    else:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yamllib.dump(DEFAULT_CONFIG, f, default_flow_style=False)
        return DEFAULT_CONFIG.copy()


CONFIG = load_config()
TIMEOUT = CONFIG["general"]["timeout"]
RETRIES = CONFIG["general"]["retries"]
THREADS = CONFIG["general"]["threads"]
PROXY = CONFIG["general"]["proxy"]
VERIFY_SSL = CONFIG["general"]["verify_ssl"]
RATE_LIMIT_DELAY = CONFIG["general"]["rate_limit_delay"]
USER_AGENT_ROTATE = CONFIG["general"]["user_agent_rotate"]

# =============================================================================
#  USER AGENT MANAGER
# =============================================================================

_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
]

if HAS_FAKE_UA:
    try:
        _ua_gen = UserAgent()
    except Exception:
        _ua_gen = None
else:
    _ua_gen = None


def get_user_agent() -> str:
    """Return a random user agent string."""
    if USER_AGENT_ROTATE:
        if _ua_gen:
            try:
                return _ua_gen.random
            except Exception:
                pass
        return random.choice(_UA_POOL)
    return _UA_POOL[0]


# =============================================================================
#  HTTP SESSION MANAGER
# =============================================================================

def make_session() -> requests.Session:
    """Create a pre-configured requests session with retries and proxy support."""
    s = requests.Session()
    retry_strategy = Retry(
        total=RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=50, pool_maxsize=100)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({"User-Agent": get_user_agent(), "Accept": "*/*"})
    if PROXY:
        s.proxies = {"http": PROXY, "https": PROXY}
    s.verify = VERIFY_SSL
    return s


# =============================================================================
#  COLOR / OUTPUT HELPERS
# =============================================================================

class Badge(Enum):
    INFO = f"{Fore.CYAN}[i]{Style.RESET_ALL}"
    OK = f"{Fore.GREEN}[+]{Style.RESET_ALL}"
    WARN = f"{Fore.YELLOW}[!]{Style.RESET_ALL}"
    ERR = f"{Fore.RED}[x]{Style.RESET_ALL}"
    DEBUG = f"{Fore.MAGENTA}[#]{Style.RESET_ALL}"
    FATAL = f"{Fore.RED}{Back.WHITE}[FATAL]{Style.RESET_ALL}"
    TARGET = f"{Fore.BLUE}[>]{Style.RESET_ALL}"
    AI = f"{Fore.YELLOW}[AI]{Style.RESET_ALL}"
    CVE = f"{Fore.RED}[CVE]{Style.RESET_ALL}"
    HTTP = f"{Fore.GREEN}[HTTP]{Style.RESET_ALL}"
    COOKIE = f"{Fore.CYAN}[COOKIE]{Style.RESET_ALL}"
    BROWSER = f"{Fore.MAGENTA}[BROWSER]{Style.RESET_ALL}"


class LiveOutput:
    """Thread-safe live output rendering with spinners and progress bars."""

    _lock = threading.Lock()

    @staticmethod
    def print(badge: Badge, message: str, end: str = "\n") -> None:
        with LiveOutput._lock:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"{Fore.BLACK}{Style.DIM}[{ts}]{Style.RESET_ALL} {badge.value} {message}", end=end)

    @staticmethod
    def section(title: str) -> None:
        width = shutil.get_terminal_size().columns if shutil.get_terminal_size().columns else 60
        line = "═" * (width - 2)
        LiveOutput.print(Badge.INFO, f"{Fore.WHITE}{Style.BRIGHT}╔{line}╗")
        LiveOutput.print(Badge.INFO, f"{Fore.WHITE}{Style.BRIGHT}║ {title.center(width-4)} ║")
        LiveOutput.print(Badge.INFO, f"{Fore.WHITE}{Style.BRIGHT}╚{line}╝")

    @staticmethod
    def progress(current: int, total: int, label: str = "") -> str:
        width = 40
        frac = current / max(total, 1)
        filled = int(frac * width)
        bar = f"{Fore.GREEN}{'█' * filled}{Fore.WHITE}{'░' * (width - filled)}"
        pct = f"{frac * 100:5.1f}%"
        return f"{bar} {pct} | {label} [{current}/{total}]"

    @staticmethod
    def table(headers: List[str], rows: List[List[str]]) -> None:
        """Print a simple aligned table."""
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        sep = "─" * (sum(col_widths) + len(headers) * 3 + 1)
        hdr = "│ " + " │ ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " │"
        LiveOutput.print(Badge.INFO, f"┌{sep}┐")
        LiveOutput.print(Badge.INFO, f"{Fore.CYAN}{hdr}")
        LiveOutput.print(Badge.INFO, f"├{sep}┤")
        for row in rows:
            r = "│ " + " │ ".join(str(c).ljust(col_widths[i]) for i, c in enumerate(row)) + " │"
            LiveOutput.print(Badge.INFO, r)
        LiveOutput.print(Badge.INFO, f"└{sep}┘")


# =============================================================================
#  REPORT MANAGER
# =============================================================================

class ReportManager:
    """Collects findings and writes structured reports (JSON, CSV, HTML)."""

    def __init__(self, target: str):
        self.target = target
        self.start_time = datetime.now()
        self.findings: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {
            "tool": "WP-BREAKER PRO v8.0",
            "target": target,
            "start_time": self.start_time.isoformat(),
            "modules_used": [],
        }

    def add_finding(self, module: str, severity: str, title: str, detail: str, evidence: str = "", cve: str = "") -> None:
        self.findings.append({
            "timestamp": datetime.now().isoformat(),
            "module": module,
            "severity": severity,
            "title": title,
            "detail": detail,
            "evidence": evidence,
            "cve": cve,
        })

    def add_module(self, name: str) -> None:
        if name not in self.metadata["modules_used"]:
            self.metadata["modules_used"].append(name)

    def save(self) -> str:
        self.metadata["end_time"] = datetime.now().isoformat()
        self.metadata["duration_seconds"] = (datetime.now() - self.start_time).total_seconds()
        self.metadata["total_findings"] = len(self.findings)

        safe_target = re.sub(r"[^\w.-]", "_", self.target)
        ts = self.start_time.strftime("%Y%m%d_%H%M%S")
        base = REPORT_DIR / f"wpbreaker_{safe_target}_{ts}"

        full_report = {
            "metadata": self.metadata,
            "findings": self.findings,
        }

        # JSON
        json_path = base.with_suffix(".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)
        LiveOutput.print(Badge.OK, f"JSON report saved: {json_path}")

        # CSV
        if CONFIG["reporting"]["save_csv"]:
            csv_path = base.with_suffix(".csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "timestamp", "module", "severity", "title", "detail", "evidence", "cve"
                ])
                writer.writeheader()
                for finding in self.findings:
                    writer.writerow(finding)
            LiveOutput.print(Badge.OK, f"CSV report saved: {csv_path}")

        # HTML
        if CONFIG["reporting"]["save_html"]:
            html_path = base.with_suffix(".html")
            self._write_html(html_path, full_report)
            LiveOutput.print(Badge.OK, f"HTML report saved: {html_path}")

        return str(json_path)

    def _write_html(self, path: Path, report: dict) -> None:
        findings_html = ""
        for f in report["findings"]:
            sev_color = {"CRITICAL": "red", "HIGH": "orange", "MEDIUM": "gold", "LOW": "green"}.get(f["severity"], "gray")
            findings_html += f"""
            <div class="finding" style="border-left: 4px solid {sev_color}; margin: 10px 0; padding: 10px; background: #1a1a2e;">
                <span style="color:{sev_color}; font-weight:bold;">[{f['severity']}]</span>
                <strong>{f['title']}</strong>
                <p>{f['detail']}</p>
                <small>{f['module']} | {f['timestamp']}</small>
                {"<pre>" + f['evidence'] + "</pre>" if f['evidence'] else ""}
            </div>"""

        html = f"""<!DOCTYPE html>
<html><head><title>WP-BREAKER PRO Report — {self.target}</title>
<style>
body {{ font-family: 'Courier New', monospace; background: #0f0f23; color: #ccc; padding: 20px; }}
h1 {{ color: #0ff; }}
.meta {{ color: #888; }}
.finding {{ border-radius: 4px; }}
pre {{ background: #111; padding: 8px; overflow-x: auto; color: #0f0; }}
</style></head><body>
<h1>🔧 WP-BREAKER PRO v8.0</h1>
<div class="meta">
<p><strong>Target:</strong> {self.target}</p>
<p><strong>Start:</strong> {report['metadata']['start_time']}</p>
<p><strong>Duration:</strong> {report['metadata']['duration_seconds']:.1f}s</p>
<p><strong>Modules:</strong> {', '.join(report['metadata']['modules_used'])}</p>
<p><strong>Total Findings:</strong> {report['metadata']['total_findings']}</p>
</div>
<h2>Findings</h2>
{findings_html}
</body></html>"""
        path.write_text(html, encoding="utf-8")


# =============================================================================
#  MODULE 1: WP SCAN WRAPPER
# =============================================================================

class WPScanWrapper:
    """Basic WordPress fingerprinting and enumeration without external binary."""

    WP_PATHS = [
        "/wp-admin/", "/wp-login.php", "/wp-content/", "/wp-includes/",
        "/xmlrpc.php", "/wp-json/", "/wp-cron.php", "/readme.html",
        "/license.txt", "/wp-config.php.bak", "/wp-content/debug.log",
        "/wp-content/uploads/", "/wp-content/plugins/", "/wp-content/themes/",
        "/.htaccess", "/wp-config.php~", "/wp-config.php.old",
        "/wp-content/wp-config.php", "/wp-admin/admin-ajax.php",
        "/wp-content/ai1wm-backups/",
        "/wp-json/wp/v2/users/", "/wp-json/wp/v2/posts/",
        "/?author=1",
    ]

    PLUGIN_FINGERPRINTS = {
        "akismet
