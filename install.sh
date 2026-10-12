#!/bin/bash

# Ensure script is run with root privileges
if [ "$EUID" -ne 0 ]; then
    echo "[-] Please run this installer with root privileges (sudo bash install.sh)."
    exit 1
fi

INSTALL_DIR="/opt/quwaisploit"
BIN_QUWAIS="/usr/local/bin/quwaisploit"
BIN_UNINSTALL="/usr/local/bin/uninstall_quwaisploit"

echo "[*] Installing Quwaisploit system-wide..."

# 1. Copy project files to /opt/quwaisploit
if [ -d "$INSTALL_DIR" ]; then
    echo "[*] Removing existing installation..."
    rm -rf "$INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR"

# 2. Install Python dependencies
echo "[*] Installing Python dependencies..."
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    pip3 install -r "$INSTALL_DIR/requirements.txt"
else
    pip3 install scapy flask beautifulsoup4 requests colorama
fi

# 3. Create global 'quwaisploit' command wrapper
echo "[*] Creating global 'quwaisploit' executable..."
cat << 'EOF' > "$BIN_QUWAIS"
#!/bin/bash
cd /opt/quwaisploit
python3 main.py "$@"
EOF
chmod +x "$BIN_QUWAIS"

# 4. Create global 'uninstall_quwaisploit' command wrapper
echo "[*] Creating global 'uninstall_quwaisploit' command..."
cat << 'EOF' > "$BIN_UNINSTALL"
#!/bin/bash
if [ "$EUID" -ne 0 ]; then
    echo "[-] Please run uninstallation with root privileges (sudo uninstall_quwaisploit)."
    exit 1
fi

echo "[*] Removing Quwaisploit from system..."
rm -rf /opt/quwaisploit
rm -f /usr/local/bin/quwaisploit
rm -f /usr/local/bin/uninstall_quwaisploit
echo "[+] Quwaisploit has been completely uninstalled from your system."
EOF
chmod +x "$BIN_UNINSTALL"

echo ""
echo "[+] ==================================================="
echo "[+] Quwaisploit successfully installed!"
echo "[+] You can now run 'quwaisploit' from anywhere in your terminal."
echo "[+] To remove it completely later, simply run 'sudo uninstall_quwaisploit'."
echo "[+] ==================================================="
