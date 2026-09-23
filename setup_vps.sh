#!/bin/bash
# Setup script untuk VPS Linux (Ubuntu/Debian).
# Jalankan dengan: bash setup_vps.sh
#
# PENTING: pastikan dulu VPS ini bisa akses situs targetmu sebelum
# lanjut install apapun. Test dengan:
#     curl -I https://penunggul.kim.id
# Kalau hasilnya timeout, VPS ini tidak bisa dipakai (lihat README).

set -e

echo "=== 1. Cek dulu apakah VPS ini bisa akses situs target ==="
if curl -sSf -o /dev/null --max-time 10 https://penunggul.kim.id; then
    echo "OK - situs bisa diakses dari VPS ini."
else
    echo "GAGAL - VPS ini TIDAK bisa akses situs target."
    echo "Kemungkinan besar VPS ini bukan IP Indonesia yang di-whitelist."
    echo "Setup dihentikan. Cari VPS dengan lokasi/IP Indonesia."
    exit 1
fi

echo ""
echo "=== 2. Install Node.js (kalau belum ada) ==="
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
else
    echo "Node.js sudah terinstall: $(node --version)"
fi

echo ""
echo "=== 3. Install Google Chrome (dibutuhkan Lighthouse) ==="
if ! command -v google-chrome-stable &> /dev/null; then
    wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo apt-get install -y /tmp/chrome.deb
    rm /tmp/chrome.deb
else
    echo "Chrome sudah terinstall."
fi

echo ""
echo "=== 4. Install Lighthouse CLI ==="
sudo npm install -g lighthouse

echo ""
echo "=== 5. Install Python & dependency ==="
sudo apt-get install -y python3 python3-pip
pip3 install requests --break-system-packages 2>/dev/null || pip3 install requests

echo ""
echo "=== Setup selesai ==="
echo "Test dengan: python3 check_performance_local.py"
