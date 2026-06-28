#!/data/data/com.termux/files/usr/bin/env python3
"""Zepton — Termux Swiss Army Knife
   Launch: python zepton.py
"""
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from core.console import main

if __name__ == "__main__":
    main()
  
