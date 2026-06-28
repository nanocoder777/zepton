"""Zepton Interactive Console — msfconsole-style shell for Termux."""
import cmd
import sys
import os
import shlex
import re
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl
from datetime import datetime
from core.colors import *
from core.utils import *

BANNER = r"""
    ███████╗███████╗██████╗ ████████╗ ██████╗ ███╗   ██╗
    ╚══███╔╝██╔════╝██╔══██╗╚══██╔══╝██╔═══██╗████╗  ██║
      ███╔╝ █████╗  ██████╔╝   ██║   ██║   ██║██╔██╗ ██║
     ███╔╝  ██╔══╝  ██╔═══╝    ██║   ██║   ██║██║╚██╗██║
    ███████╗███████╗██║        ██║   ╚██████╔╝██║ ╚████║
    ╚══════╝╚══════╝╚═╝        ╚═╝    ╚═════╝ ╚═╝  ╚═══╝
              Termux Swiss Army Knife v2.0
"""

class ZeptonConsole(cmd.Cmd):
    intro = f"{Colors.CYAN}{BANNER}{Colors.RESET}"
    prompt = f"{Colors.BOLD}{Colors.GREEN}zepton{Colors.RESET} > "
    
    def __init__(self):
        super().__init__()
        self.current_module = None
        self.options = {}
        self.modules = {
            "recon":   "Reconnaissance & OSINT",
            "web":     "Web Application Testing",
            "network": "Network Scanning & Traffic",
            "crypto":  "Cryptography & Encoding",
            "distro":  "Linux Distro Management",
            "report":  "Session Reporting",
        }
        self._update_prompt()
    
    def _update_prompt(self):
        if self.current_module:
            self.prompt = f"{Colors.BOLD}{Colors.GREEN}zepton{Colors.RESET}({Colors.YELLOW}{self.current_module}{Colors.RESET}) > "
        else:
            self.prompt = f"{Colors.BOLD}{Colors.GREEN}zepton{Colors.RESET} > "
    
    def emptyline(self):
        pass
    
    def do_clear(self, arg):
        os.system("clear")
    
    def do_banner(self, arg):
        print(self.intro)
    
    def do_exit(self, arg):
        print(info("Exiting Zepton. Stay curious."))
        return True
    
    def do_quit(self, arg):
        return self.do_exit(arg)
    
    def do_use(self, arg):
        if not arg:
            print(error("No module specified. Use 'show modules' to list available modules."))
            return
        mod = arg.strip().lower()
        if mod in self.modules:
            self.current_module = mod
            self.options = {}
            self._update_prompt()
            print(success(f"Loaded module: {mod}"))
            print(info(f"  {self.modules[mod]}"))
            print(info("Type 'help' for module commands."))
        else:
            print(error(f"Unknown module: {mod}. Use 'show modules' to list available modules."))
    
    def do_back(self, arg):
        if self.current_module:
            print(info(f"Leaving {self.current_module} module."))
            self.current_module = None
            self.options = {}
            self._update_prompt()
        else:
            print(warning("Already at the main menu."))
    
    def do_show(self, arg):
        what = arg.strip().lower()
        if what == "modules" or what == "":
            print(f"\n{Colors.BOLD}Available Modules:{Colors.RESET}")
            rows = []
            for mod, desc in self.modules.items():
                status = Colors.GREEN + "active" + Colors.RESET if mod == self.current_module else Colors.DIM + "idle" + Colors.RESET
                rows.append([mod, desc, status])
            print_table(["Module", "Description", "Status"], rows)
        elif what == "options":
            if not self.current_module:
                print(warning("No module loaded. Use 'use <module>' first."))
                return
            print(f"\n{Colors.BOLD}Module Options ({self.current_module}):{Colors.RESET}")
            if not self.options:
                print(DIM + "  No options set. Commands use direct arguments." + RESET)
            else:
                rows = [[k, str(v)] for k, v in self.options.items()]
                print_table(["Option", "Value"], rows)
        elif what == "commands":
            self.do_help("")
        else:
            print(error(f"Unknown show target: {what}"))
    
    def do_set(self, arg):
        parts = shlex.split(arg)
        if len(parts) < 2:
            print(error("Usage: set <option> <value>"))
            return
        key = parts[0].upper()
        val = parts[1]
        self.options[key] = val
        print(success(f"{key} => {val}"))
    
    def do_unset(self, arg):
        key = arg.strip().upper()
        if key in self.options:
            del self.options[key]
            print(success(f"Cleared {key}"))
        else:
            print(warning(f"{key} was not set."))
    
    def do_shell(self, arg):
        if arg:
            os.system(arg)
        else:
            print(info("Dropping to system shell. Type 'exit' to return to Zepton."))
            os.system(os.environ.get("SHELL", "bash"))
    
    def do_help(self, arg):
        if arg:
            super().do_help(arg)
            return
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}Zepton Core Commands:{Colors.RESET}")
        core = [
            ("help", "Show this help menu"),
            ("show modules", "List available modules"),
            ("show options", "Show current module options"),
            ("use <module>", "Load a module"),
            ("back", "Return to main menu"),
            ("set <opt> <val>", "Set an option value"),
            ("unset <opt>", "Remove an option"),
            ("shell [cmd]", "Execute a shell command"),
            ("clear", "Clear the screen"),
            ("banner", "Show the banner"),
            ("exit / quit", "Leave Zepton"),
        ]
        for c, d in core:
            print(f"  {Colors.GREEN}{c:<20}{Colors.RESET} {d}")
        
        if self.current_module:
            print(f"\n{Colors.BOLD}{Colors.CYAN}{self.current_module.upper()} Module Commands:{Colors.RESET}")
            if self.current_module == "recon":
                cmds = [
                    ("subdomain <domain>", "Brute-force subdomains"),
                    ("osint <domain>", "Aggregate WHOIS + DNS + tech stack"),
                    ("breach <email>", "Check email against breach DB (HIBP)"),
                    ("metadata <url>", "Extract EXIF from downloadable files"),
                ]
            elif self.current_module == "web":
                cmds = [
                    ("scan <target>", "nmap port scan"),
                    ("probe <url>", "HTTP probe (status, headers, time)"),
                    ("headers <url>", "Security header audit"),
                    ("ssl <domain>", "SSL/TLS certificate info"),
                    ("whois <domain>", "WHOIS lookup"),
                    ("dns <domain>", "DNS resolution records"),
                    ("tech <url>", "Fingerprint web technologies"),
                    ("vuln <url>", "Check for exposed files (.git, .env, etc)"),
                    ("fuzz <url>", "Directory/file brute force"),
                    ("sqli <url>", "Basic SQLi parameter probe"),
                    ("xss <url>", "Basic reflected XSS probe"),
                ]
            elif self.current_module == "network":
                cmds = [
                    ("ping <subnet>", "Ping sweep for live hosts"),
                    ("ports <target>", "Connect scan open ports"),
                    ("capture [iface]", "Start tcpdump packet capture"),
                ]
            elif self.current_module == "crypto":
                cmds = [
                    ("hash <text>", "Generate MD5, SHA1, SHA256, bcrypt"),
                    ("crack <hash>", "Attempt hash crack with john"),
                    ("encode <text>", "Base64, URL, hex encode"),
                    ("decode <text>", "Base64, URL, hex decode"),
                ]
            elif self.current_module == "distro":
                cmds = [
                    ("list", "List installed proot distros"),
                    ("install <name>", "Install a distro"),
                    ("login <name>", "Login to a distro"),
                    ("remove <name>", "Remove a distro"),
                    ("backup <name>", "Backup distro to tarball"),
                    ("restore <file>", "Restore distro from tarball"),
                ]
            elif self.current_module == "report":
                cmds = [
                    ("generate", "Create Markdown report from session"),
                    ("save <file>", "Save raw session log to file"),
                    ("clear", "Clear current session log"),
                    ("status", "Show session event count"),
                ]
            else:
                cmds = []
            for c, d in cmds:
                print(f"  {Colors.YELLOW}{c:<22}{Colors.RESET} {d}")
        print()
    
    # ============================================================
    # RECON MODULE
    # ============================================================
    def do_subdomain(self, arg):
        if self.current_module != "recon":
            print(error("'subdomain' is a recon module command. Use 'use recon' first.")); return
        if not arg:
            print(error("Usage: subdomain <domain> [wordlist-path]")); return
        parts = arg.split()
        domain = parts[0]
        wordlist = parts[1] if len(parts) > 1 else get_wordlist("subdomains")
        if not wordlist or not os.path.exists(wordlist):
            print(error("Wordlist not found. Creating default..."))
            wordlist = get_wordlist("subdomains")
        
        print(info(f"Brute-forcing subdomains for {domain}..."))
        found = []
        try:
            with open(wordlist) as f:
                subs = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        except:
            print(error("Could not read wordlist.")); return
        
        for sub in subs[:200]:
            target = f"{sub}.{domain}"
            try:
                import socket
                socket.gethostbyname(target)
                found.append(target)
                print(f"  {Colors.GREEN}[FOUND]{Colors.RESET} {target}")
            except socket.gaierror:
                pass
        
        result = f"Found {len(found)} subdomains: {', '.join(found)}"
        log_event("recon", f"subdomain {domain}", result)
        print(success(f"Done. Found {len(found)} subdomains."))
    
    def do_osint(self, arg):
        if self.current_module != "recon":
            print(error("'osint' is a recon module command. Use 'use recon' first.")); return
        if not arg:
            print(error("Usage: osint <domain>")); return
        domain = arg.strip()
        print(info(f"Running OSINT aggregation on {domain}..."))
        
        whois_out = ""
        if check_cmd("whois"):
            whois_out = run_shell(f"whois {domain}")
        
        dns_out = ""
        if check_cmd("dig"):
            dns_out = run_shell(f"dig +short A {domain}")
        elif check_cmd("nslookup"):
            dns_out = run_shell(f"nslookup {domain}")
        
        tech_out = ""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(f"https://{domain}", headers={"User-Agent":"Mozilla/5.0"}, method="HEAD")
            resp = urllib.request.urlopen(req, timeout=10, context=ctx)
            headers = dict(resp.headers)
            server = headers.get("Server", "Unknown")
            tech_out = f"Server: {server}"
        except Exception as e:
            tech_out = f"Probe failed: {e}"
        
        print(f"\n{Colors.BOLD}WHOIS (filtered):{Colors.RESET}")
        for line in whois_out.splitlines()[:15]:
            if any(k in line.lower() for k in ["domain name", "registrar", "creation", "expiration", "name server", "status", "org", "country"]):
                print(f"  {line}")
        print(f"\n{Colors.BOLD}DNS A Records:{Colors.RESET}")
        print(f"  {dns_out.strip() or 'None'}")
        print(f"\n{Colors.BOLD}Tech:{Colors.RESET}")
        print(f"  {tech_out}")
        
        log_event("recon", f"osint {domain}", f"DNS: {dns_out.strip()}, Tech: {tech_out}")
    
    def do_breach(self, arg):
        if self.current_module != "recon":
            print(error("'breach' is a recon module command. Use 'use recon' first.")); return
        if not arg:
            print(error("Usage: breach <email>")); return
        email = arg.strip()
        print(info(f"Checking {email} against HaveIBeenPwned..."))
        try:
            req = urllib.request.Request(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{urllib.parse.quote(email)}",
                headers={"User-Agent": "Zepton-Termux-Tool", "hibp-api-key": ""}
            )
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read().decode())
            breaches = [b.get("Name", "Unknown") for b in data]
            print(error(f"Pwned! Found in {len(breaches)} breach(es): {', '.join(breaches)}"))
            log_event("recon", f"breach {email}", f"Pwned: {breaches}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(success("Good news — no breaches found for this email."))
                log_event("recon", f"breach {email}", "No breaches found")
            elif e.code == 429:
                print(warning("Rate limited by HIBP. Try again later."))
            else:
                print(error(f"HIBP error: {e.code}"))
        except Exception as e:
            print(error(f"Check failed: {e}"))
    
    def do_metadata(self, arg):
        if self.current_module != "recon":
            print(error("'metadata' is a recon module command. Use 'use recon' first.")); return
        if not arg:
            print(error("Usage: metadata <url-to-file>")); return
        url = arg.strip()
        print(info(f"Downloading and analyzing metadata from {url}..."))
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=15).read()
            if data[:2] == b"\xff\xd8":
                print(success("JPEG detected. Basic EXIF tags:"))
                idx = data.find(b"Exif\x00\x00")
                if idx != -1:
                    snippet = data[idx:idx+200]
                    text = snippet.decode("ascii", errors="ignore")
                    for line in text.split("\x00"):
                        if len(line) > 3 and any(c.isprintable() for c in line):
                            print(f"  {line.strip()}")
                else:
                    print(warning("No EXIF data found."))
            else:
                print(info(f"File type: {data[:4].hex()} — full EXIF parsing requires exiftool"))
            log_event("recon", f"metadata {url}", f"Analyzed {len(data)} bytes")
        except Exception as e:
            print(error(f"Failed: {e}"))
    
    # ============================================================
    # WEB MODULE
    # ============================================================
    def do_scan(self, arg):
        if self.current_module != "web":
            print(error("'scan' is a web module command. Use 'use web' first.")); return
        if not arg:
            print(error("Usage: scan <target> [top-100|top-1000|all]")); return
        parts = arg.split()
        target = parts[0]
        mode = parts[1] if len(parts) > 1 else "top-100"
        if not ensure_pkg("nmap", "nmap"):
            print(error("nmap could not be installed.")); return
        flags = "-F"
        if mode == "top-1000": flags = "--top-ports 1000"
        elif mode == "all": flags = "-p-"
        print(info(f"Scanning {target} ({mode})..."))
        out = run_shell(f"nmap {flags} -sV --open {target}")
        print(out)
        log_event("web", f"scan {target}", out[:500])
        print(success("Scan complete."))
    
    def do_probe(self, arg):
        if self.current_module != "web":
            print(error("'probe' is a web module command. Use 'use web' first.")); return
        if not arg:
            print(error("Usage: probe <url>")); return
        url = arg.strip()
        if not url.startswith("http"): url = "http://" + url
        print(info(f"Probing {url}..."))
        out = run_shell(f'curl -sI -w "\\nHTTP_CODE:%{{http_code}}\\nTIME_TOTAL:%{{time_total}}" -L -m 15 "{url}" 2>&1')
        code = "???"; time_total = "???"; headers = []
        for line in out.splitlines():
            if line.startswith("HTTP_CODE:"): code = line.split(":",1)[1].strip()
            elif line.startswith("TIME_TOTAL:"): time_total = line.split(":",1)[1].strip() + "s"
            elif ":" in line and not line.startswith("HTTP_CODE"): headers.append(line)
        print(f"\n{Colors.BOLD}Status:{Colors.RESET}  {Colors.GREEN if code.startswith('2') else Colors.YELLOW if code.startswith('3') else Colors.RED}{code}{Colors.RESET}")
        print(f"{Colors.BOLD}Time:{Colors.RESET}    {time_total}")
        print(f"{Colors.BOLD}Headers:{Colors.RESET}")
        for h in headers[:15]: print(f"  {Colors.DIM}{h}{Colors.RESET}")
        log_event("web", f"probe {url}", f"Status {code}, Time {time_total}")
        print()
    
    def do_headers(self, arg):
        if self.current_module != "web":
            print(error("'headers' is a web module command. Use 'use web' first.")); return
        if not arg:
            print(error("Usage: headers <url>")); return
        url = arg.strip()
        if not url.startswith("http"): url = "http://" + url
        print(info(f"Auditing security headers for {url}..."))
        out = run_shell(f'curl -sI -L -m 15 "{url}" 2>&1')
        headers = {}
        for line in out.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        
        checks = {
            "strict-transport-security": ("HSTS", "Missing — site vulnerable to SSL strip"),
            "content-security-policy": ("CSP", "Missing — XSS risk higher"),
            "x-frame-options": ("X-Frame-Options", "Missing — clickjacking possible"),
            "x-content-type-options": ("X-Content-Type-Options", "Missing — MIME sniffing risk"),
            "referrer-policy": ("Referrer-Policy", "Missing — referrer leakage"),
            "permissions-policy": ("Permissions-Policy", "Missing — feature abuse risk"),
        }
        rows = []
        for h, (name, missing) in checks.items():
            if h in headers:
                rows.append([name, Colors.GREEN + "Present" + Colors.RESET, headers[h][:40]])
            else:
                rows.append([name, Colors.RED + "Missing" + Colors.RESET, missing])
        print_table(["Header", "Status", "Value/Note"], rows)
        log_event("web", f"headers {url}", f"Missing: {[k for k,v in checks.items() if k not in headers]}")
    
    def do_ssl(self, arg):
        if self.current_module != "web":
            print(error("'ssl' is a web module command. Use 'use web' first.")); return
        if not arg:
            print(error("Usage: ssl <domain>[:port]")); return
        target = arg.strip()
        if ":" not in target: target += ":443"
        print(info(f"Checking SSL for {target}..."))
        out = run_shell(f'echo | openssl s_client -connect {target} -servername {target.split(":")[0]} 2>/dev/null | openssl x509 -noout -dates -subject -issuer 2>/dev/null')
        if not out.strip():
            print(error("Could not retrieve certificate.")); return
        print(f"{Colors.BOLD}Certificate Info:{Colors.RESET}")
        for line in out.strip().splitlines(): print(f"  {Colors.CYAN}{line}{Colors.RESET}")
        cipher_out = run_shell(f'echo | openssl s_client -connect {target} 2>/dev/null | grep "Cipher" | head -3')
        if cipher_out.strip():
            print(f"\n{Colors.BOLD}Cipher:{Colors.RESET}")
            for line in cipher_out.strip().splitlines(): print(f"  {Colors.DIM}{line}{Colors.RESET}")
        log_event("web", f"ssl {target}", out.strip())
        print()
    
    def do_whois(self, arg):
        if self.current_module != "web":
            print(error("'whois' is a web module command. Use 'use web' first.")); return
        if not arg:
            print(error("Usage: whois <domain>")); return
        if not ensure_pkg("whois", "whois"):
            print(error("whois could not be installed.")); return
        print(info(f"WHOIS lookup for {arg}..."))
        out = run_shell(f"whois {arg.strip()}")
        useful = [l for l in out.splitlines() if any(k in l.lower() for k in ["domain name", "registrar", "creation", "expiration", "name server", "status", "org", "country"])]
        for line in useful[:30]: print(f"  {line}")
        log_event("web", f"whois {arg}", f"{len(useful)} lines")
        print()
    
    def do_dns(self, arg):
        if self.current_module != "web":
            print(error("'dns' is a web module command. Use 'use web' first.")); return
        if not arg:
            print(error("Usage: dns <domain> [A|MX|NS|TXT|ALL]")); return
        parts = arg.split()
        domain = parts[0]
        rtype = parts[1].upper() if len(parts) > 1 else "A"
        print(info(f"DNS {rtype} records for {domain}..."))
        if check_cmd("dig"):
            if rtype == "ALL": out = run_shell(f"dig +noall +answer ANY {domain}")
            else: out = run_shell(f"dig +noall +answer {rtype} {domain}")
        else:
            out = run_shell(f"nslookup -type={rtype} {domain}")
        print(out if out.strip() else warning("No records found."))
        log_event("web", f"dns {domain}", out[:300])
    
    def do_tech(self, arg):
        if self.current_module != "web":
            print(error("'tech' is a web module command. Use 'use web' first.")); return
        if not arg:
            print(error("Usage: tech <url>")); return
        url = arg.strip()
        if not url.startswith("http"): url = "http://" + url
        print(info(f"Fingerprinting {url}..."))
        out = run_shell(f'curl -sL -m 15 "{url}" 2>&1 | head -c 50000')
        headers = run_shell(f'curl -sI -L -m 15 "{url}" 2>&1')
        techs = []
        checks = {
            "WordPress": ["wp-content", "wp-includes", "wordpress"],
            "Drupal": ["drupal", "sites/default"],
            "Joomla": ["joomla"],
            "Nginx": ["nginx"],
            "Apache": ["apache"],
            "Cloudflare": ["cloudflare"],
            "PHP": ["php"],
            "Express.js": ["express"],
            "React": ["react", "__next"],
            "Next.js": ["__next"],
            "Shopify": ["shopify"],
            "Wix": ["wix"],
            "Django": ["csrfmiddlewaretoken", "django"],
            "Laravel": ["laravel"],
        }
        combined = (out + headers).lower()
        for tech, signs in checks.items():
            if any(s in combined for s in signs): techs.append(tech)
        server = "Unknown"
        for line in headers.splitlines():
            if line.lower().startswith("server:"): server = line.split(":",1)[1].strip()
        print(f"\n{Colors.BOLD}Server:{Colors.RESET}    {Colors.CYAN}{server}{Colors.RESET}")
        print(f"{Colors.BOLD}Tech:{Colors.RESET}      {Colors.GREEN}{', '.join(techs) if techs else 'None detected'}{Colors.RESET}")
        log_event("web", f"tech {url}", f"Server: {server}, Tech: {techs}")
        print()
    
    def do_vuln(self, arg):
        if self.current_module != "web":
            print(error("'vuln' is a web module command. Use 'use web' first.")); return
        if not arg:
            print(error("Usage: vuln <url>")); return
        base = arg.strip().rstrip("/")
        if not base.startswith("http"): base = "http://" + base
        print(info(f"Checking {base} for exposed files..."))
        
        checks = {
            ".git/HEAD": "Git repo exposed",
            ".env": "Environment file exposed",
            "robots.txt": "Robots file present",
            "sitemap.xml": "Sitemap present",
            ".htaccess": "Apache config exposed",
            "phpinfo.php": "PHP info exposed",
            "server-status": "Apache status page",
            "admin/": "Admin panel",
            "backup/": "Backup directory",
            "config.php": "Config file",
            "wp-config.php": "WordPress config",
            "api/": "API endpoint",
            "swagger.json": "Swagger API docs",
            "api-docs/": "API docs",
        }
        found = []
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        for path, desc in checks.items():
            url = f"{base}/{path}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"}, method="HEAD")
                resp = urllib.request.urlopen(req, timeout=8, context=ctx)
                if resp.status < 400:
                    found.append([path, desc, Colors.RED + str(resp.status) + Colors.RESET])
                    print(f"  {Colors.RED}[EXPOSED]{Colors.RESET} {path} — {desc}")
            except urllib.error.HTTPError as e:
                if e.code in (301, 302, 401, 403):
                    found.append([path, desc, Colors.YELLOW + str(e.code) + Colors.RESET])
                    print(f"  {Colors.YELLOW}[PARTIAL]{Colors.RESET} {path} — {desc} (HTTP {e.code})")
            except:
                pass
        if not found:
            print(success("No common exposed files detected."))
        else:
            print_table(["Path", "Description", "Status"], found)
        log_event("web", f"vuln {base}", f"Found {len(found)} exposed files")
    
    def do_fuzz(self, arg):
        if self.current_module != "web":
            print(error("'fuzz' is a web module command. Use 'use web' first.")); return
        if not arg:
            print(error("Usage: fuzz <url> [wordlist-path]")); return
        parts = arg.split()
        base = parts[0].rstrip("/")
        if not base.startswith("http"): base = "http://" + base
        wordlist = parts[1] if len(parts) > 1 else get_wordlist("dirs")
        if not wordlist or not os.path.exists(wordlist):
            wordlist = get_wordlist("dirs")
        
        print(info(f"Fuzzing directories on {base}..."))
        try:
            with open(wordlist) as f:
                words = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        except:
            print(error("Could not read wordlist.")); return
        
        found = []
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        for word in words[:100]:
            url = f"{base}/{word}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"}, method="HEAD")
                resp = urllib.request.urlopen(req, timeout=5, context=ctx)
                if resp.status < 400:
                    found.append([url, str(resp.status)])
                    print(f"  {Colors.GREEN}[{resp.status}]{Colors.RESET} {url}")
            except urllib.error.HTTPError as e:
                if e.code in (301, 302, 401, 403, 405, 500):
                    found.append([url, str(e.code)])
                    print(f"  {Colors.YELLOW}[{e.code}]{Colors.RESET} {url}")
            except:
                pass
        if found:
            print_table(["URL", "Status"], found)
        else:
            print(warning("No directories found with this wordlist."))
        log_event("web", f"fuzz {base}", f"Found {len(found)} paths")
    
    def do_sqli(self, arg):
        if self.current_module != "web":
            print(error("'sqli' is a web module command. Use 'use web' first.")); return
        if not arg:
            print(error("Usage: sqli <url> [param]")); return
        parts = arg.split()
        url = parts[0]
        param = parts[1] if len(parts) > 1 else "id"
        if not url.startswith("http"): url = "http://" + url
        if "?" not in url: url += f"?{param}=1"
        
        payloads = ["'", "\"", "' OR '1'='1", "1 AND 1=1", "1 AND 1=2", "1' UNION SELECT NULL--"]
        print(info(f"Testing SQLi on {url} (param: {param})..."))
        errors = ["sql syntax", "mysql_fetch", "ORA-", "sqlite", "pg_query", "unclosed quotation", "ODBC", "driver"]
        found = False
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        for payload in payloads:
            test_url = url + payload if "=" in url else f"{url}&{param}={urllib.parse.quote(payload)}"
            try:
                req = urllib.request.Request(test_url, headers={"User-Agent":"Mozilla/5.0"})
                resp = urllib.request.urlopen(req, timeout=10, context=ctx)
                body = resp.read().decode("utf-8", errors="ignore").lower()
                for err in errors:
                    if err in body:
                        print(f"  {Colors.RED}[SQLi DETECTED]{Colors.RESET} Payload: {payload}")
                        print(f"  {Colors.DIM}Error indicator: {err}{Colors.RESET}")
                        found = True
                        break
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="ignore").lower()
                for err in errors:
                    if err in body:
                        print(f"  {Colors.RED}[SQLi DETECTED]{Colors.RESET} Payload: {payload}")
                        print(f"  {Colors.DIM}Error indicator: {err}{Colors.RESET}")
                        found = True
                        break
            except:
                pass
        if not found:
            print(warning("No obvious SQLi indicators found. Target may still be vulnerable to blind/time-based SQLi."))
        log_event("web", f"sqli {url}", "Detected" if found else "Not detected")
    
    def do_xss(self, arg):
        if self.current_module != "web":
            print(error("'xss' is a web module command. Use 'use web' first.")); return
        if not arg:
            print(error("Usage: xss <url> [param]")); return
        parts = arg.split()
        url = parts[0]
        param = parts[1] if len(parts) > 1 else "q"
        if not url.startswith("http"): url = "http://" + url
        if "?" not in url: url += f"?{param}=test"
        
        payloads = ["<script>alert(1)</script>", "\"><img src=x onerror=alert(1)>", "javascript:alert(1)", "<svg onload=alert(1)>"]
        print(info(f"Testing reflected XSS on {url} (param: {param})..."))
        found = False
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        for payload in payloads:
            test_url = url + urllib.parse.quote(payload) if "=" in url else f"{url}&{param}={urllib.parse.quote(payload)}"
            try:
                req = urllib.request.Request(test_url, headers={"User-Agent":"Mozilla/5.0"})
                resp = urllib.request.urlopen(req, timeout=10, context=ctx)
                body = resp.read().decode("utf-8", errors="ignore")
                if payload in body or urllib.parse.quote(payload) in body:
                    print(f"  {Colors.RED}[XSS DETECTED]{Colors.RESET} Payload reflected: {payload[:40]}...")
                    found = True
            except:
                pass
        if not found:
            print(warning("No reflected XSS detected with basic payloads."))
        log_event("web", f"xss {url}", "Detected" if found else "Not detected")
    
    # ============================================================
    # NETWORK MODULE
    # ============================================================
    def do_ping(self, arg):
        if self.current_module != "network":
            print(error("'ping' is a network module command. Use 'use network' first.")); return
        if not arg:
            print(error("Usage: ping <subnet> (e.g., 192.168.1.0/24 or 192.168.1.1-254)")); return
        target = arg.strip()
        print(info(f"Ping sweeping {target}..."))
        if "/" in target:
            if not ensure_pkg("nmap", "nmap"):
                print(error("nmap required for CIDR sweep.")); return
            out = run_shell(f"nmap -sn {target}")
            print(out)
        elif "-" in target:
            base = target.rsplit(".", 1)[0]
            start, end = target.rsplit(".", 1)[1].split("-")
            import subprocess
            for i in range(int(start), int(end)+1):
                ip = f"{base}.{i}"
                result = subprocess.run(["ping", "-c", "1", "-W", "1", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if result.returncode == 0:
                    print(f"  {Colors.GREEN}[UP]{Colors.RESET}   {ip}")
                else:
                    print(f"  {Colors.DIM}[DOWN]{Colors.RESET} {ip}", end="\r")
            print()
        else:
            out = run_shell(f"ping -c 3 {target}")
            print(out)
        log_event("network", f"ping {target}", "Completed")
    
    def do_ports(self, arg):
        if self.current_module != "network":
            print(error("'ports' is a network module command. Use 'use network' first.")); return
        if not arg:
            print(error("Usage: ports <target> [start-end]")); return
        parts = arg.split()
        target = parts[0]
        port_range = parts[1] if len(parts) > 1 else "1-1000"
        print(info(f"Connect-scanning {target} ports {port_range}..."))
        import socket
        start, end = map(int, port_range.split("-"))
        open_ports = []
        for port in range(start, end+1):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                result = s.connect_ex((target, port))
                if result == 0:
                    try:
                        banner = s.recv(1024).decode("utf-8", errors="ignore").strip()
                    except:
                        banner = ""
                    open_ports.append([str(port), banner[:30] or "Unknown"])
                    print(f"  {Colors.GREEN}[OPEN]{Colors.RESET} {port} — {banner[:30]}")
                s.close()
            except:
                pass
        if open_ports:
            print_table(["Port", "Banner/Service"], open_ports)
        else:
            print(warning("No open ports found in range."))
        log_event("network", f"ports {target}", f"Found {len(open_ports)} open ports")
    
    def do_capture(self, arg):
        if self.current_module != "network":
            print(error("'capture' is a network module command. Use 'use network' first.")); return
        iface = arg.strip() if arg else "any"
        if not ensure_pkg("tcpdump", "tcpdump"):
            print(error("tcpdump could not be installed.")); return
        print(info(f"Starting tcpdump on interface '{iface}'..."))
        print(warning("Press Ctrl+C to stop capture."))
        out_file = os.path.expanduser("~/storage/shared/zepton-capture.pcap")
        try:
            os.system(f"tcpdump -i {iface} -w {out_file}")
        except KeyboardInterrupt:
            pass
        print(success(f"Capture saved to {out_file}"))
        log_event("network", f"capture {iface}", f"Saved to {out_file}")
    
    # ============================================================
    # CRYPTO MODULE
    # ============================================================
    def do_hash(self, arg):
        if self.current_module != "crypto":
            print(error("'hash' is a crypto module command. Use 'use crypto' first.")); return
        if not arg:
            print(error("Usage: hash <text>")); return
        text = arg.strip()
        import hashlib
        md5 = hashlib.md5(text.encode()).hexdigest()
        sha1 = hashlib.sha1(text.encode()).hexdigest()
        sha256 = hashlib.sha256(text.encode()).hexdigest()
        print(f"{Colors.BOLD}Input:{Colors.RESET}  {text}")
        print(f"{Colors.BOLD}MD5:{Colors.RESET}    {Colors.CYAN}{md5}{Colors.RESET}")
        print(f"{Colors.BOLD}SHA1:{Colors.RESET}   {Colors.CYAN}{sha1}{Colors.RESET}")
        print(f"{Colors.BOLD}SHA256:{Colors.RESET} {Colors.CYAN}{sha256}{Colors.RESET}")
        try:
            import bcrypt
            bhash = bcrypt.hashpw(text.encode(), bcrypt.gensalt()).decode()
            print(f"{Colors.BOLD}Bcrypt:{Colors.RESET} {Colors.CYAN}{bhash}{Colors.RESET}")
        except ImportError:
            print(warning("bcrypt not installed. Run: pip install bcrypt"))
        log_event("crypto", f"hash {text[:20]}...", f"MD5: {md5}")
    
    def do_crack(self, arg):
        if self.current_module != "crypto":
            print(error("'crack' is a crypto module command. Use 'use crypto' first.")); return
        if not arg:
            print(error("Usage: crack <hash> [wordlist-path]")); return
        parts = arg.split()
        target_hash = parts[0]
        wordlist = parts[1] if len(parts) > 1 else "/data/data/com.termux/files/usr/share/wordlists/rockyou.txt"
        if not os.path.exists(wordlist):
            print(warning("Wordlist not found. Using tiny built-in list..."))
            wordlist = None
        
        print(info(f"Attempting to crack hash: {target_hash}"))
        print(warning("This will be SLOW on a phone. Only for educational/authorized testing."))
        
        import hashlib
        if wordlist and os.path.exists(wordlist):
            try:
                with open(wordlist, "rb") as f:
                    for line in f:
                        word = line.strip()
                        for algo in [hashlib.md5, hashlib.sha1, hashlib.sha256]:
                            if algo(word).hexdigest() == target_hash:
                                print(success(f"CRACKED! [{algo.__name__}] Password: {word.decode()}"))
                                log_event("crypto", f"crack {target_hash}", f"Cracked: {word.decode()}")
                                return
            except KeyboardInterrupt:
                print(warning("Interrupted by user."))
                return
        else:
            common = ["password", "123456", "admin", "root", "termux", "zepton", "letmein", "qwerty", "password123", "123456789"]
            for word in common:
                for algo in [hashlib.md5, hashlib.sha1, hashlib.sha256]:
                    if algo(word.encode()).hexdigest() == target_hash:
                        print(success(f"CRACKED! [{algo.__name__}] Password: {word}"))
                        log_event("crypto", f"crack {target_hash}", f"Cracked: {word}")
                        return
        print(error("Hash not cracked with available wordlist."))
        log_event("crypto", f"crack {target_hash}", "Failed")
    
    def do_encode(self, arg):
        if self.current_module != "crypto":
            print(error("'encode' is a crypto module command. Use 'use crypto' first.")); return
        if not arg:
            print(error("Usage: encode <text> [base64|url|hex]")); return
        parts = shlex.split(arg)
        text = parts[0]
        method = parts[1].lower() if len(parts) > 1 else "base64"
        if method == "base64":
            import base64
            out = base64.b64encode(text.encode()).decode()
        elif method == "url":
            out = urllib.parse.quote(text)
        elif method == "hex":
            out = text.encode().hex()
        else:
            print(error("Methods: base64, url, hex")); return
        print(f"{Colors.BOLD}Input:{Colors.RESET}  {text}")
        print(f"{Colors.BOLD}Output:{Colors.RESET} {Colors.CYAN}{out}{Colors.RESET}")
        log_event("crypto", f"encode {method}", out[:50])
    
    def do_decode(self, arg):
        if self.current_module != "crypto":
            print(error("'decode' is a crypto module command. Use 'use crypto' first.")); return
        if not arg:
            print(error("Usage: decode <text> [base64|url|hex]")); return
        parts = shlex.split(arg)
        text = parts[0]
        method = parts[1].lower() if len(parts) > 1 else "base64"
        try:
            if method == "base64":
                import base64
                out = base64.b64decode(text).decode()
            elif method == "url":
                out = urllib.parse.unquote(text)
            elif method == "hex":
                out = bytes.fromhex(text).decode()
            else:
                print(error("Methods: base64, url, hex")); return
            print(f"{Colors.BOLD}Input:{Colors.RESET}  {text}")
            print(f"{Colors.BOLD}Output:{Colors.RESET} {Colors.CYAN}{out}{Colors.RESET}")
            log_event("crypto", f"decode {method}", out[:50])
        except Exception as e:
            print(error(f"Decode failed: {e}"))
    
    # ============================================================
    # DISTRO MODULE
    # ============================================================
    def do_list(self, arg):
        if self.current_module != "distro":
            print(error("'list' is a distro module command. Use 'use distro' first.")); return
        if not ensure_pkg("proot-distro", "proot-distro"):
            print(error("proot-distro is required.")); return
        print(info("Installed distros:"))
        out = run_shell("proot-distro list")
        print(out if out.strip() else warning("No distros installed."))
    
    def do_install(self, arg):
        if self.current_module != "distro":
            print(error("'install' is a distro module command. Use 'use distro' first.")); return
        if not arg:
            print(error("Usage: install <distro-name>"))
            print(info("Common: ubuntu, debian, archlinux, alpine, fedora")); return
        if not ensure_pkg("proot-distro", "proot-distro"):
            print(error("proot-distro is required.")); return
        distro = arg.strip().lower()
        print(info(f"Installing {distro}... This may take a while."))
        run_shell(f"proot-distro install {distro}")
        print(success(f"Installation of {distro} complete! Use 'login {distro}' to enter."))
    
    def do_login(self, arg):
        if self.current_module != "distro":
            print(error("'login' is a distro module command. Use 'use distro' first.")); return
        if not arg:
            print(error("Usage: login <distro-name>")); return
        distro = arg.strip().lower()
        print(info(f"Logging into {distro}..."))
        print(warning("Type 'exit' to return to Zepton."))
        os.system(f"proot-distro login {distro}")
        print(info(f"Left {distro} environment."))
    
    def do_remove(self, arg):
        if self.current_module != "distro":
            print(error("'remove' is a distro module command. Use 'use distro' first.")); return
        if not arg:
            print(error("Usage: remove <distro-name>")); return
        distro = arg.strip().lower()
        confirm = input(warning(f"Really remove {distro}? [y/N]: "))
        if confirm.lower() == "y":
            run_shell(f"proot-distro remove {distro}")
            print(success(f"Removed {distro}."))
        else:
            print(info("Cancelled."))
    
    def do_backup(self, arg):
        if self.current_module != "distro":
            print(error("'backup' is a distro module command. Use 'use distro' first.")); return
        if not arg:
            print(error("Usage: backup <distro-name> [filename]")); return
        parts = arg.split()
        distro = parts[0]
        filename = parts[1] if len(parts) > 1 else f"{distro}-backup.tar.gz"
        path = f"/data/data/com.termux/files/usr/var/lib/proot-distro/installed-rootfs/{distro}"
        if not os.path.exists(path):
            print(error(f"Distro {distro} not found.")); return
        out_path = os.path.expanduser(f"~/storage/shared/{filename}")
        print(info(f"Backing up {distro} to {out_path}..."))
        run_shell(f"tar -czf {out_path} -C {path} .")
        print(success(f"Backup saved to {out_path}"))
    
    def do_restore(self, arg):
        if self.current_module != "distro":
            print(error("'restore' is a distro module command. Use 'use distro' first.")); return
        parts = arg.split()
        if len(parts) < 2:
            print(error("Usage: restore <filename> <distro-name>")); return
        filename = parts[0]
        distro = parts[1]
        file_path = os.path.expanduser(f"~/storage/shared/{filename}")
        if not os.path.exists(file_path):
            print(error(f"Backup file not found: {file_path}")); return
        dest = f"/data/data/com.termux/files/usr/var/lib/proot-distro/installed-rootfs/{distro}"
        os.makedirs(dest, exist_ok=True)
        print(info(f"Restoring {distro} from {filename}..."))
        run_shell(f"tar -xzf {file_path} -C {dest}")
        print(success(f"Restored {distro}. Use 'login {distro}' to enter."))
    
    # ============================================================
    # REPORT MODULE
    # ============================================================
    def do_generate(self, arg):
        if self.current_module != "report":
            print(error("'generate' is a report module command. Use 'use report' first.")); return
        filename = arg.strip() if arg else "zepton-report.md"
        path = os.path.expanduser(f"~/storage/shared/{filename}")
        print(info(f"Generating Markdown report to {path}..."))
        
        lines = [
            "# Zepton Security Assessment Report",
            f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Platform:** Termux ({os.environ.get('TERMUX_VERSION', 'unknown')})",
            "\n---\n",
        ]
        
        if not SESSION_LOG:
            lines.append("_No session activity recorded._\n")
        else:
            for entry in SESSION_LOG:
                lines.append(f"## {entry['category'].upper()} — {entry['command']}")
                lines.append(f"- **Time:** {entry['timestamp']}")
                lines.append(f"- **Result:** {entry['result']}")
                lines.append("")
        
        with open(path, "w") as f:
            f.write("\n".join(lines))
        print(success(f"Report saved to {path}"))
    
    def do_save(self, arg):
        if self.current_module != "report":
            print(error("'save' is a report module command. Use 'use report' first.")); return
        filename = arg.strip() if arg else "zepton-session.json"
        path = os.path.expanduser(f"~/storage/shared/{filename}")
        with open(path, "w") as f:
            json.dump(SESSION_LOG, f, indent=2)
        print(success(f"Session log saved to {path} ({len(SESSION_LOG)} events)"))
    
    def do_clear(self, arg):
        if self.current_module != "report":
            print(error("'clear' is a report module command. Use 'use report' first.")); return
        global SESSION_LOG
        SESSION_LOG.clear()
        print(success("Session log cleared."))
    
    def do_status(self, arg):
        if self.current_module != "report":
            print(error("'status' is a report module command. Use 'use report' first.")); return
        print(info(f"Session contains {len(SESSION_LOG)} recorded events."))
        if SESSION_LOG:
            cats = {}
            for e in SESSION_LOG:
                cats[e["category"]] = cats.get(e["category"], 0) + 1
            print_table(["Category", "Events"], [[k, v] for k, v in cats.items()])


def main():
    try:
        ZeptonConsole().cmdloop()
    except KeyboardInterrupt:
        print("\n" + info("Interrupted. Exiting Zepton."))
        sys.exit(0)

if __name__ == "__main__":
    main()
