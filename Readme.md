<div align="center">
  <img src="https://img.shields.io/badge/Version-5.0-red?style=for-the-badge" alt="Version 5.0">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Platform-Termux-green?style=for-the-badge&logo=linux" alt="Termux">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License">
  <br>
  <img src="https://img.shields.io/badge/Status-Active-success?style=flat-square">
  <img src="https://img.shields.io/badge/WordPress%20Pentest-AI%20Driven-brightgreen?style=flat-square">
  <img src="https://img.shields.io/badge/Ethical%20Hacking-Authorized-blue?style=flat-square">
</div>

<br>

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=200&section=header&text=WP-BREAKER%20PRO&fontSize=60&fontColor=white&animation=fadeIn&fontAlignY=35" alt="WP-BREAKER PRO Banner"/>
</p>

<h1 align="center">🔥 WP-BREAKER PRO v5.0 — HACKER-AI-DRIVEN</h1>

<p align="center">
  <b>Multi-funkční WordPress Penetrační Testing Tool s Umělou Inteligencí</b><br>
  <i>TCP/IP Fingerprinting • AI Context Scraper • DOM Shadow Analyzer • Cookie Engine<br>
  Bypass Researcher • AI Password Generator • Smart Brute Force • AI Report</i>
</p>

<p align="center">
  <b>⚠️ POUŽÍVEJTE POUZE NA SYSTÉMY, KE KTERÝM MÁTE VÝSLOVNÉ OPRÁVNĚNÍ ⚠️</b>
</p>

---

## 📋 OBSAH

- [🎯 Přehled](#-přehled)
- [✨ Funkce](#-funkce)
- [📱 Instalace v Termuxu (Android)](#-instalace-v-termuxu-android)
- [💻 Instalace na Kali Linux / Ubuntu](#-instalace-na-kali-linux--ubuntu)
- [🎮 Použití - Hlavní Menu](#-použití---hlavní-menu)
- [🕹️ Jednotlivé Moduly](#️-jednotlivé-moduly)
- [🤖 AI Engine - Jak to funguje](#-ai-engine---jak-to-funguje)
- [📊 Příklad Výstupu](#-příklad-výstupu)
- [🛡️ Doporučené Obrany Proti Těmto Technikám](#️-doporučené-obrany-proti-těmto-technikám)
- [🏗️ Projektová Struktura](#️-projektová-struktura)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)
- [📞 Kontakt & Podpora](#-kontakt--podpora)

---

## 🎯 PŘEHLED

**WP-BREAKER PRO** je profesionální nástroj pro penetrační testování WordPress webů, poháněný **AI inteligencí**. Nástroj kombinuje 8 výkonných modulů do jednoho koherentního workflow:

1. **Skenuje** cíl a zjistí jeho infrastrukturu
2. **Analyzuje** obsah webu a vytvoří kontextový profil
3. **Generuje** inteligentní hesla na základě kontextu
4. **Útočí** více metodami s adaptivní korekcí
5. **Reportuje** všechny nálezy v přehledném formátu

Vše běží v **reálném čase** s barevným live outputem přímo v terminálu.

---

## ✨ FUNKCE

| Modul | Popis | Výstup |
|-------|-------|--------|
| **🌐 TCP/IP Fingerprint** | Detekce serveru, WAF, OS, security headers, TTL analýza | Server, WAF, HSTS, CSP |
| **📋 AI Context Scraper** | Extrahuje emaily, jména, firmu, klíčová slova, pluginy, témata, uživatele z REST API | Kontextový profil |
| **🔎 DOM Shadow Analyzer** | Hledá skryté formuláře, NONCE tokeny, credentials v komentářích, JS proměnné, Base64, API endpointy | Skryté prvky |
| **🍪 Cookie Engine** | Analyzuje cookies, testuje Secure/HttpOnly flagy, zkouší admin session injection | Cookie vulnerabilites |
| **🚪 Bypass Researcher** | XML-RPC, REST API, debug log, wp-config zálohy, phpMyAdmin, alternativní login cesty, user enumeration | Bypass cesty |
| **🔑 AI Password Generator** | Generuje hesla z kontextu: leetspeak, keyboard patterns, jméno+rok, company+číslo, top 200 passwords | Wordlist (soubor) |
| **🧠 Smart Brute Force** | XML-RPC + wp-login.php s adaptivním delayem, CAPTCHA detekcí, rate-limit handlingem, multi-threading | Cracknuté heslo |
| **📄 AI Report** | Kompletní shrnutí všech nálezů, kritické/výstražné/informativní, bezpečnostní skóre | Profesionální report |

### AI Self-Correction Loop 🤖

Nástroj obsahuje **inteligentní korekční smyčku**, která:
- Detekuje WAF a automaticky zpomaluje útok
- Rozpozná rate-limiting (HTTP 429/503)
- Přepíná mezi XML-RPC a wp-login.php metodami
- Adaptivně mění timeout a počet vláken
- Ukládá progress a umožňuje pokračovat po přerušení

---

## 📱 INSTALACE V TERMUXU (ANDROID)

### Krok 1: Aktualizace Termuxu
```bash
pkg update && pkg upgrade -y
