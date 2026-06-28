"""Utility functions for Zepton."""
import subprocess
import shutil
import os
import json
from datetime import datetime
from core.colors import *

# Session log for report generation
SESSION_LOG = []

def log_event(category, command, result):
    """Log an event for report generation."""
    SESSION_LOG.append({
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "command": command,
        "result": result
    })

def check_cmd(cmd):
    return shutil.which(cmd) is not None

def run_shell(cmd, capture=True, silent=False, timeout=300):
    try:
        if silent:
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return ""
        result = subprocess.run(cmd, shell=True, capture_output=capture, text=True, timeout=timeout)
        return result.stdout + result.stderr if capture else ""
    except subprocess.TimeoutExpired:
        return error("Command timed out.")
    except Exception as e:
        return error(f"Error: {e}")

def ensure_pkg(pkg, apt_name=None):
    if check_cmd(pkg):
        return True
    apt = apt_name or pkg
    print(warning(f"{pkg} not found. Installing {apt}..."))
    run_shell(f"pkg install -y {apt}", silent=True)
    return check_cmd(pkg)

def print_table(headers, rows):
    if not rows:
        print(warning("No data to display."))
        return
    col_widths = [max(len(str(h)), max((len(str(r[i])) for r in rows), default=0)) + 2 for i, h in enumerate(headers)]
    sep = "+" + "+".join(["-" * w for w in col_widths]) + "+"
    print(f"\n{Colors.DIM}{sep}{Colors.RESET}")
    header_line = "|" + "|".join([f" {Colors.BOLD}{Colors.CYAN}{headers[i]:^{col_widths[i]-2}}{Colors.RESET} " for i in range(len(headers))]) + "|"
    print(header_line)
    print(f"{Colors.DIM}{sep}{Colors.RESET}")
    for row in rows:
        row_line = "|" + "|".join([f" {str(row[i]):^{col_widths[i]-2}} " for i in range(len(row))]) + "|"
        print(row_line)
    print(f"{Colors.DIM}{sep}{Colors.RESET}\n")

def is_termux():
    return "TERMUX_VERSION" in os.environ or os.path.exists("/data/data/com.termux/files/usr/bin")

def get_wordlist(name="common"):
    """Return path to a built-in wordlist or create a tiny one."""
    wordlist_dir = os.path.expanduser("~/.zepton/wordlists")
    os.makedirs(wordlist_dir, exist_ok=True)
    
    if name == "subdomains":
        path = os.path.join(wordlist_dir, "subdomains.txt")
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write("\n".join([
                    "www","mail","ftp","localhost","webmail","smtp","pop","ns1","webdisk",
                    "ns2","cpanel","whm","autodiscover","autoconfig","ns","mx","mobile",
                    "api","blog","dev","test","staging","admin","portal","secure","vpn",
                    "remote","host","web","cloud","server","app","shop","store","support",
                    "help","docs","wiki","git","cdn","static","assets","media","img",
                    "video","download","upload","files","backup","db","sql","mysql",
                    "postgres","redis","mongo","elastic","kibana","grafana","prometheus",
                    "jenkins","gitlab","github","jira","confluence","slack","discord"
                ]))
        return path
    
    elif name == "dirs":
        path = os.path.join(wordlist_dir, "dirs.txt")
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write("\n".join([
                    "admin","login","dashboard","api","config",".env",".git",".htaccess",
                    "robots.txt","sitemap.xml","wp-admin","wp-content","wp-includes",
                    "phpmyadmin","adminer","db","backup","uploads","files","images",
                    "css","js","assets","static","media","temp","tmp","test","dev",
                    "staging","old","new","v1","v2","api/v1","api/v2","graphql",
                    "swagger","api-docs","debug","console","shell","exec","cmd",
                    ".svn",".hg",".DS_Store",".well-known","cgi-bin","server-status",
                    "phpinfo.php","info.php","test.php","shell.php","cmd.php"
                ]))
        return path
    
    return None
                  
