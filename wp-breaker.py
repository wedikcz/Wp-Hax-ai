#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    WP-BREAKER PRO v8.0 — FULL STACK                        ║
║         Unified WordPress Penetration Testing Suite (Termux OK)            ║
║                                                                            ║
║  Modules:                                                                  ║
║    [1] WPScan Wrapper — Fingerprinting, path/plugin/user enumeration       ║
║    [2] AetherX Exploit Engine — CVE mapping, AI payload mutation, verify   ║
║    [3] XML-RPC Bruteforcer — Multicall (500 attempts/req), pingback SSRF   ║
║    [4] Contextual AI Wordlist Generator — LLM-driven site scraping         ║
║    [5] Cookie-Spray & Session Fixation                                    ║
║    [6] Headless Browser Human Simulation — Playwright/Selenium             ║
║    [7] Interactive CLI Menu — Threaded, progress bars, live output         ║
║                                                                            ║
║  Author: AetherX Research Team                                             ║
║  License: Ethical Use Only - Authorized Penetration Testing Only           ║
║                                                                            ║
║  [!] USER CONFIRMED: "Tenho permissão e estou autorizado a realizar este   ║
║      pentest" / "I have permission and am authorized to perform this       ║
║      pentest"                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import http.client
import io
import ipaddress
import itertools
import json
import logging
import os
import pickle
import random
import re
import shlex
import shutil
import socket
import ssl
import sqlite3
import string
import struct
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import traceback
import uuid
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum, auto
from functools import lru_cache, wraps
from html.parser import HTMLParser
from http.cookies import SimpleCookie
from io import BytesIO, StringIO
from pathlib import Path
from string import ascii_letters, digits, punctuation
from typing import (Any, Callable, Dict, Generator, List, Optional,
                    Set, Tuple, Union)
from urllib.parse import (parse_qs, quote, unquote, urlencode, urljoin,
                           urlparse, urlunparse)
from xml.parsers.expat import ExpatError

# =============================================================================
#  TERMUX / ENVIRONMENT DETECTION & PATH SANITY
# =============================================================================

IS_TERMUX = bool(os.environ.get("TERMUX_VERSION")) or \
            "com.termux" in os.environ.get("HOME", "").lower() or \
            "termux" in os.environ.get("PREFIX", "").lower()

if IS_TERMUX:
    _home = os.environ.get("HOME", "/data/data/com.termux/files/home")
    LOG_DIR = Path(_home) / ".wpbreaker"
    REPORT_DIR = LOG_DIR / "reports"
    CONFIG_PATH = LOG_DIR / "config.yaml"
    WORDLIST_DIR = LOG_DIR / "wordlists"
    CACHE_DIR = LOG_DIR / "cache"
    TOOLS_DIR = LOG_DIR / "tools"
    _shm = Path("/dev/shm")
    TEMP_DIR = _shm if _shm.exists() else LOG_DIR / "tmp"
else:
    LOG_DIR = Path.home() / ".wpbreaker"
    REPORT_DIR = LOG_DIR / "reports"
    CONFIG_PATH = LOG_DIR / "config.yaml"
    WORDLIST_DIR = LOG_DIR / "wordlists"
    CACHE_DIR = LOG_DIR / "cache"
    TOOLS_DIR = LOG_DIR / "tools"
    TEMP_DIR = LOG_DIR / "tmp"

for _d in [LOG_DIR, REPORT_DIR, WORDLIST_DIR, CACHE_DIR, TOOLS_DIR, TEMP_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# =============================================================================
#  DEPENDENCY AUTO-INSTALLER (Termux-safe + Self-Healing)
# =============================================================================

REQUIRED_PACKAGES = [
    "requests",
    "colorama",
    "pyyaml",
    "urllib3",
]

OPTIONAL_PACKAGES = [
    "aiohttp",
    "beautifulsoup4",
    "lxml",
    "fake_useragent",
    "playwright",
    "selenium",
    "cryptography",
    "pillow",
    "humanize",
    "tqdm",
    "rich",
    "prompt_toolkit",
    "paramiko",
    "scp",
    "pynacl",
]

_MISSING_OPTIONAL: List[str] = []
_INSTALL_LOCK = threading.Lock()


def _pip_install(package: str, timeout: int = 30) -> bool:
    """Install a pip package with timeout. Returns True on success."""
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--quiet", package]
        if IS_TERMUX:
            cmd.insert(-1, "--no-cache-dir")
        subprocess.check_call(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
        return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
        return False


def ensure_dependencies() -> None:
    """Auto-install required packages; attempt optional ones silently."""
    global _MISSING_OPTIONAL

    missing_required = []
    for pkg in REQUIRED_PACKAGES:
        mod_name = pkg.replace("-", "_").replace(".", "_")
        try:
            __import__(mod_name)
        except ImportError:
            missing_required.append(pkg)

    if missing_required:
        print(f"{Fore.YELLOW}[!] Installing required dependencies: {', '.join(missing_required)}{Style.RESET_ALL}")
        for pkg in missing_required:
            if _pip_install(pkg):
                print(f"    {Fore.GREEN}[+]{Style.RESET_ALL} {pkg} installed.")
            else:
                print(f"    {Fore.RED}[x]{Style.RESET_ALL} Failed to install {pkg}. Run: pip install {pkg}")
                sys.exit(1)
        print(f"{Fore.GREEN}[+]{Style.RESET_ALL} Restarting to load dependencies...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    for pkg in OPTIONAL_PACKAGES:
        mod_name = pkg.replace("-", "_").replace(".", "_")
        try:
            __import__(mod_name)
        except ImportError:
            if _pip_install(pkg):
                pass
            else:
                _MISSING_OPTIONAL.append(pkg)


ensure_dependencies()

# =============================================================================
#  IMPORTS (after dependency check)
# =============================================================================

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import (ConnectionError, HTTPError, ReadTimeout,
                                  RequestException, SSLError, Timeout)
from urllib3.util.retry import Retry
import colorama
from colorama import Fore, Back, Style
import yaml as yamllib

try:
    import aiohttp
    from aiohttp import ClientSession, TCPConnector, ClientTimeout
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    from lxml import etree as lxml_etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False

try:
    from fake_useragent import UserAgent as FakeUA
    HAS_FAKE_UA = True
except ImportError:
    HAS_FAKE_UA = False

try:
    from playwright.sync_api import (Playwright, sync_playwright,
                                      TimeoutError as PlaywrightTimeout,
                                      Error as PlaywrightError)
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
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.common.exceptions import (TimeoutException, WebDriverException,
                                             NoSuchElementException)
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

try:
    from rich.console import Console as RichConsole
    from rich.table import Table as RichTable
    from rich.progress import (Progress, BarColumn, TextColumn,
                                TimeElapsedColumn, SpinnerColumn)
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

colorama.init(autoreset=True)

# =============================================================================
#  LOGGING SETUP
# =============================================================================

logger = logging.getLogger("wpbreaker")
logger.setLevel(logging.DEBUG)

_fh = logging.FileHandler(LOG_DIR / "wpbreaker.log", encoding="utf-8", mode="a")
_fh.setLevel(logging.DEBUG)
_fmt_file = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(threadName)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_fh.setFormatter(_fmt_file)
logger.addHandler(_fh)

_ch = logging.StreamHandler(sys.stdout)
_ch.setLevel(logging.INFO)
_ch.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_ch)


# =============================================================================
#  CONFIGURATION SYSTEM
# =============================================================================

DEFAULT_CONFIG: Dict[str, Any] = {
    "general": {
        "timeout": 15,
        "retries": 3,
        "threads": 20,
        "user_agent_rotate": True,
        "proxy": None,
        "proxy_auth": None,
        "verify_ssl": False,
        "rate_limit_delay": 0.3,
        "max_redirects": 5,
        "cookie_persistence": True,
        "tor_enabled": False,
        "tor_port": 9050,
        "dns_resolver": "system",
        "random_delay_range": [0.1, 0.8],
    },
    "wpscan": {
        "enabled": True,
        "plugins_deep": False,
        "api_token": None,
        "passive_mode": False,
        "skip_cve_check": False,
    },
    "xmlrpc": {
        "enabled": True,
        "max_attempts_per_request": 500,
        "verify_methods": ["system.listMethods", "system.multicall",
                           "wp.getUsersBlogs", "pingback.ping",
                           "mt.setPostCategories", "wp.getOptions"],
        "password_attempts_per_user": 5,
        "check_pingback_ssrf": True,
        "check_system_multicall": True,
    },
    "aetherx": {
        "enabled": True,
        "exploitdb_path": str(TOOLS_DIR / "exploitdb"),
        "exploitdb_update_days": 7,
        "payload_mutation": True,
        "async_verify": True,
        "max_cves_per_scan": 15,
        "ai_payload_generation": True,
        "verify_with_curl": False,
    },
    "ai_wordlist": {
        "enabled": True,
        "max_scrape_pages": 30,
        "max_depth": 2,
        "password_count": 100,
        "min_password_length": 8,
        "max_password_length": 32,
        "include_symbols": True,
        "include_dates": True,
        "include_years": True,
        "include_leet": True,
        "llm_model": "local",
        "llm_temperature": 0.8,
        "llm_max_tokens": 1024,
        "openai_key": None,
        "openai_model": "gpt-3.5-turbo",
        "openai_base_url": "https://api.openai.com/v1",
        "local_llm_url": "http://127.0.0.1:11434/api/generate",
        "local_llm_model": "llama3.2",
    },
    "cookie_spray": {
        "enabled": True,
        "cookie_jar_path": str(CACHE_DIR / "cookies.json"),
        "test_fixation": True,
        "test_replay": True,
        "test_privilege_escalation": True,
        "spray_wordlist": [],
    },
    "headless": {
        "enabled": False,
        "engine": "playwright",
        "headless": True,
        "human_delay_range_ms": [50, 300],
        "mouse_move_steps": 15,
        "keystroke_variance": 0.2,
        "viewport_width": 1920,
        "viewport_height": 1080,
        "device_scale_factor": 1.0,
        "locale": "en-US",
        "timezone": "America/New_York",
        "geolocation": None,
        "record_video": False,
        "screenshot_on_findings": True,
        "cloudflare_wait_timeout": 30,
        "browser_executable_path": None,
    },
    "reporting": {
        "save_json": True,
        "save_csv": True,
        "save_html": True,
        "save_markdown": True,
        "compress_reports": False,
        "include_raw_evidence": True,
        "max_evidence_length": 5000,
        "report_title": "WP-BREAKER PRO Security Assessment",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user_cfg = yamllib.safe_load(f) or {}
            return _deep_merge(DEFAULT_CONFIG, user_cfg)
        except (yamllib.YAMLError, OSError) as e:
            logger.warning(f"Config load failed ({e}), using defaults")
            return DEFAULT_CONFIG.copy()
    else:
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yamllib.dump(DEFAULT_CONFIG, f, default_flow_style=False, indent=2)
            logger.info(f"Default config written to {CONFIG_PATH}")
        except OSError as e:
            logger.warning(f"Cannot write config: {e}")
        return DEFAULT_CONFIG.copy()


CONFIG = load_config()
CFG_G = CONFIG["general"]
CFG_W = CONFIG["wpscan"]
CFG_X = CONFIG["xmlrpc"]
CFG_A = CONFIG["aetherx"]
CFG_AI = CONFIG["ai_wordlist"]
CFG_C = CONFIG["cookie_spray"]
CFG_H = CONFIG["headless"]
CFG_R = CONFIG["reporting"]

TIMEOUT = CFG_G["timeout"]
RETRIES = CFG_G["retries"]
THREADS = CFG_G["threads"]
PROXY = CFG_G["proxy"]
VERIFY_SSL = CFG_G["verify_ssl"]
RATE_LIMIT_DELAY = CFG_G["rate_limit_delay"]
UA_ROTATE = CFG_G["user_agent_rotate"]


# =============================================================================
#  USER AGENT MANAGER
# =============================================================================

_UA_POOL: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
]

if HAS_FAKE_UA:
    try:
        _ua_gen = FakeUA()
        _ua_gen.random
    except Exception:
        _ua_gen = None
else:
    _ua_gen = None


def get_user_agent() -> str:
    if UA_ROTATE:
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
    s = requests.Session()
    retry_strat = Retry(
        total=RETRIES,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504, 520, 521, 522, 524],
        allowed_methods=frozenset(["GET", "POST", "HEAD"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(
        max_retries=retry_strat,
        pool_connections=50,
        pool_maxsize=200,
        pool_block=False,
    )
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({
        "User-Agent": get_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    })
    if PROXY:
        s.proxies = {"http": PROXY, "https": PROXY}
    s.verify = VERIFY_SSL
    s.max_redirects = CFG_G["max_redirects"]
    return s


# =============================================================================
#  COLOR / OUTPUT / UI SYSTEM
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
    SQL = f"{Fore.RED}[SQL]{Style.RESET_ALL}"
    XSS = f"{Fore.YELLOW}[XSS]{Style.RESET_ALL}"
    AUTH = f"{Fore.BLUE}[AUTH]{Style.RESET_ALL}"
    SHELL = f"{Fore.GREEN}[SHELL]{Style.RESET_ALL}"
    PROXY = f"{Fore.CYAN}[PROXY]{Style.RESET_ALL}"
    SCAN = f"{Fore.WHITE}[SCAN]{Style.RESET_ALL}"
    START = f"{Fore.GREEN}[START]{Style.RESET_ALL}"
    DONE = f"{Fore.GREEN}[DONE]{Style.RESET_ALL}"
    WAIT = f"{Fore.YELLOW}[WAIT]{Style.RESET_ALL}"


class LiveOutput:
    """Thread-safe console output system."""

    _lock = threading.RLock()
    _console = RichConsole() if HAS_RICH else None

    @staticmethod
    def print(badge: Badge, message: str, end: str = "\n", flush: bool = True) -> None:
        with LiveOutput._lock:
            ts = datetime.now().strftime("%H:%M:%S")
            line = f"{Fore.BLACK}{Style.DIM}[{ts}]{Style.RESET_ALL} {badge.value} {message}"
            print(line, end=end, flush=flush)

    @staticmethod
    def raw(message: str) -> None:
        with LiveOutput._lock:
            print(message, flush=True)

    @staticmethod
    def section(title: str, subtitle: str = "") -> None:
        width = min(shutil.get_terminal_size().columns, 100)
        line = "=" * (width - 2)
        LiveOutput.print(Badge.INFO, f"{Fore.WHITE}{Style.BRIGHT}{line}")
        LiveOutput.print(Badge.INFO, f"{Fore.WHITE}{Style.BRIGHT}{title.center(width-2)}")
        if subtitle:
            LiveOutput.print(Badge.INFO, f"{Fore.WHITE}{Style.DIM}{subtitle.center(width-2)}")
        LiveOutput.print(Badge.INFO, f"{Fore.WHITE}{Style.BRIGHT}{line}")

    @staticmethod
    def progress_bar(current: int, total: int, label: str = "",
                     width: int = 40, color: str = Fore.GREEN) -> str:
        if total <= 0:
            total = 1
        frac = current / total
        filled = int(frac * width)
        bar = f"{color}{'#' * filled}{Fore.WHITE}{'.' * (width - filled)}"
        pct = f"{frac * 100:5.1f}%"
        return f"{bar} {pct} {label} [{current}/{total}]"

    @staticmethod
    def table(headers: List[str], rows: List[List[str]], title: str = "") -> None:
        if not headers or not rows:
            return
        if HAS_RICH and LiveOutput._console:
            rt = RichTable(title=title, box=None, header_style="bold cyan")
            for h in headers:
                rt.add_column(h, overflow="fold")
            for row in rows:
                rt.add_row(*[str(c) for c in row])
            LiveOutput._console.print(rt)
            return
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        sep = "-" * (sum(col_widths) + len(headers) * 3 + 1)
        hdr_line = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
        LiveOutput.print(Badge.INFO, f"+{sep}+")
        if title:
            LiveOutput.print(Badge.INFO, f"| {title.center(len(sep)-2)} |")
            LiveOutput.print(Badge.INFO, f"+{sep}+")
        LiveOutput.print(Badge.INFO, f"{Fore.CYAN}{hdr_line}")
        LiveOutput.print(Badge.INFO, f"+{sep}+")
        for row in rows:
            r = "| " + " | ".join(str(c).ljust(col_widths[i]) for i, c in enumerate(row)) + " |"
            LiveOutput.print(Badge.INFO, r)
        LiveOutput.print(Badge.INFO, f"+{sep}+")

    @staticmethod
    def finding(severity: str, title: str, detail: str = "") -> None:
        sev_colors = {
            "CRITICAL": Fore.RED + Back.WHITE,
            "HIGH": Fore.RED,
            "MEDIUM": Fore.YELLOW,
            "LOW": Fore.CYAN,
            "INFO": Fore.GREEN,
        }
        color = sev_colors.get(severity.upper(), Fore.WHITE)
        badge = f"{color}[{severity.upper()}]{Style.RESET_ALL}"
        LiveOutput.print(Badge.INFO, f"{badge} {Fore.WHITE}{Style.BRIGHT}{title}{Style.RESET_ALL}")
        if detail:
            LiveOutput.print(Badge.INFO, f"       {Fore.BLACK}{Style.DIM}{detail}{Style.RESET_ALL}")


# =============================================================================
#  REPORT MANAGER
# =============================================================================

class ReportManager:
    """Collects findings, generates reports in multiple formats."""

    SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}

    def __init__(self, target: str):
        self.target = target
        self.start_time = datetime.now()
        self.findings: List[Dict[str, Any]] = []
        self.modules_used: List[str] = []
        self.metadata: Dict[str, Any] = {
            "tool": "WP-BREAKER PRO v8.0",
            "target": target,
            "start_time": self.start_time.isoformat(),
            "config": {k: v for k, v in CONFIG.items()},
        }

    def add_finding(self, module: str, severity: str, title: str,
                    detail: str, evidence: str = "", cve: str = "",
                    cvss: Optional[float] = None, recommendation: str = "") -> None:
        self.findings.append({
            "timestamp": datetime.now().isoformat(),
            "module": module,
            "severity": severity.upper(),
            "title": title,
            "detail": detail,
            "evidence": evidence[:CFG_R["max_evidence_length"]] if evidence else "",
            "cve": cve,
            "cvss": cvss,
            "recommendation": recommendation,
            "id": hashlib.md5(f"{module}{title}{datetime.now().isoformat()}".encode()).hexdigest()[:12],
        })

    def add_module(self, name: str) -> None:
        if name not in self.modules_used:
            self.modules_used.append(name)

    def get_summary(self) -> Dict[str, int]:
        summary = Counter()
        for f in self.findings:
            summary[f["severity"]] += 1
        return dict(summary)

    def save(self) -> str:
        self.metadata["end_time"] = datetime.now().isoformat()
        self.metadata["duration_seconds"] = round((datetime.now() - self.start_time).total_seconds(), 2)
        self.metadata["total_findings"] = len(self.findings)
        self.metadata["modules_used"] = self.modules_used
        self.metadata["summary"] = self.get_summary()

        safe_target = re.sub(r"[^\w.-]", "_", self.target)
        ts = self.start_time.strftime("%Y%m%d_%H%M%S")
        base = REPORT_DIR / f"wpbreaker_{safe_target}_{ts}"
        full_report = {
            "metadata": self.metadata,
            "findings": sorted(self.findings,
                               key=lambda x: self.SEVERITY_ORDER.get(x["severity"], 99)),
        }
        paths_saved = []

        if CFG_R["save_json"]:
            json_path = base.with_suffix(".json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(full_report, f, indent=2, ensure_ascii=False, default=str)
            paths_saved.append(str(json_path))
            LiveOutput.print(Badge.OK, f"JSON: {json_path}")

        if CFG_R["save_csv"]:
            csv_path = base.with_suffix(".csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "timestamp", "module", "severity", "title", "detail",
                    "evidence", "cve", "cvss", "recommendation", "id"
                ])
                writer.writeheader()
                for finding in self.findings:
                    writer.writerow({k: finding.get(k, "") for k in writer.fieldnames})
            paths_saved.append(str(csv_path))
            LiveOutput.print(Badge.OK, f"CSV: {csv_path}")

        if CFG_R["save_html"]:
            html_path = base.with_suffix(".html")
            self._write_html(html_path, full_report)
            paths_saved.append(str(html_path))
            LiveOutput.print(Badge.OK, f"HTML: {html_path}")

        if CFG_R["save_markdown"]:
            md_path = base.with_suffix(".md")
            self._write_markdown(md_path, full_report)
            paths_saved.append(str(md_path))
            LiveOutput.print(Badge.OK, f"Markdown: {md_path}")

        if CFG_R["compress_reports"] and paths_saved:
            zip_path = base.with_suffix(".zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for p in paths_saved:
                    zf.write(p, arcname=Path(p).name)
            LiveOutput.print(Badge.OK, f"Archive: {zip_path}")

        return str(base.with_suffix(".json"))

    def _write_html(self, path: Path, report: dict) -> None:
        sev_colors = {
            "CRITICAL": "#ff0000", "HIGH": "#ff6600",
            "MEDIUM": "#ffcc00", "LOW": "#00cc66", "INFO": "#3399ff"
        }
        findings_html = ""
        for f in report["findings"]:
            color = sev_colors.get(f["severity"], "#888")
            cve_tag = f" | <a href='https://nvd.nist.gov/vuln/detail/{f['cve']}' target='_blank'>{f['cve']}</a>" if f.get("cve") else ""
            cvss_tag = f" | CVSS: {f['cvss']}" if f.get("cvss") else ""
            evidence_block = f"<pre>{f['evidence']}</pre>" if f.get("evidence") else ""
            rec_block = f"<p><strong>Recommendation:</strong> {f['recommendation']}</p>" if f.get("recommendation") else ""
            findings_html += f"""
            <div class="finding" style="border-left: 5px solid {color};">
                <span class="sev-{f['severity'].lower()}">[{
