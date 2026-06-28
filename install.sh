#!/data/data/com.termux/files/usr/bin/bash
# Zepton Installer for Termux
set -e

Z_DIR="$HOME/zepton"
BIN_DIR="/data/data/com.termux/files/usr/bin"

echo "[+] Installing Zepton..."

if ! command -v python3 &> /dev/null; then
    echo "[*] Installing python..."
    pkg install -y python
fi

mkdir -p "$Z_DIR"

SCRIPT_SRC="$(cd "$(dirname "$0")" && pwd)"
cp -r "$SCRIPT_SRC"/* "$Z_DIR/" 2>/dev/null || true

chmod +x "$Z_DIR/zepton.py"

rm -f "$BIN_DIR/zepton"
ln -s "$Z_DIR/zepton.py" "$BIN_DIR/zepton"

echo "[+] Zepton installed!"
echo "[*] Type 'zepton' to launch."

