#!/bin/bash

# Termux Installation Script for Quwaisploit

echo "[*] Updating Termux packages..."
pkg update -y && pkg upgrade -y

echo "[*] Installing required system dependencies (Python, Git, libpcap, clang)..."
pkg install python git libpcap clang libffi libssl make -y

INSTALL_DIR="$HOME/.quwaisploit"
BIN_QUWAIS="$PREFIX/bin/quwaisploit"
BIN_UNINSTALL="$PREFIX/bin/uninstall_quwaisploit"

echo "[*] Installing Quwaisploit to $INSTALL_DIR..."
if [ -d "$INSTALL_DIR" ]; then
    echo "[*] Removing existing installation..."
    rm -rf "$INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR"

echo "[*] Upgrading pip and installing Python dependencies..."
pip install --upgrade pip

if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    pip install -r "$INSTALL_DIR/requirements.txt"
else
    pip install scapy flask beautifulsoup4 requests colorama
fi

echo "[*] Creating global 'quwaisploit' command..."
cat << 'EOF' > "$BIN_QUWAIS"
#!/bin/bash
cd ~/.quwaisploit
python3 main.py "$@"
EOF
chmod +x "$BIN_QUWAIS"

echo "[*] Creating global 'uninstall_quwaisploit' command..."
cat << 'EOF' > "$BIN_UNINSTALL"
#!/bin/bash
echo "[*] Removing Quwaisploit from Termux..."
rm -rf ~/.quwaisploit
rm -f "$PREFIX/bin/quwaisploit"
rm -f "$PREFIX/bin/uninstall_quwaisploit"
echo "[+] Quwaisploit has been completely uninstalled from Termux."
EOF
chmod +x "$BIN_UNINSTALL"

echo ""
echo "[+] ==================================================="
echo "[+] Quwaisploit successfully installed in Termux!"
echo "[+] You can now run 'quwaisploit' from anywhere in your Termux terminal."
echo "[+] To remove it completely later, simply run 'uninstall_quwaisploit'."
echo "[+] ==================================================="
