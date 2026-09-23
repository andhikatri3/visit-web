"""
Cek performa website pakai Lighthouse CLI LOKAL (bukan PageSpeed
Insights API). Bedanya: yang mengakses situsnya adalah Chrome di
komputer kamu sendiri, bukan server Google di luar negeri.

Dipakai kalau situs targetmu hanya bisa diakses dari jaringan
Indonesia (situs pemerintah, intranet, dsb).

Prasyarat:
    1. Install Node.js: https://nodejs.org (pilih versi LTS)
    2. Install Lighthouse CLI (sekali saja): npm install -g lighthouse
    3. Google Chrome sudah terinstall di komputer

Cara pakai:
    python check_performance_local.py

Pengaturan URL dan opsi lain ada di:
    - urls.txt     -> daftar URL yang mau dicek
    - config.json  -> strategi (mobile/desktop) & jeda antar-request
"""

import os
import csv
import json
import time
import shutil
import subprocess
import tempfile
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
URLS_FILE = os.path.join(BASE_DIR, "urls.txt")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
CSV_FILE = os.path.join(BASE_DIR, "performance_log.csv")

DEFAULT_CONFIG = {
    "strategies": ["mobile", "desktop"],
    "delay_between_requests_seconds": 2,
}


def load_urls() -> list:
    if not os.path.isfile(URLS_FILE):
        print(f"File {URLS_FILE} tidak ditemukan.")
        return []
    urls = []
    with open(URLS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def load_config() -> dict:
    if not os.path.isfile(CONFIG_FILE):
        return DEFAULT_CONFIG
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        user_config = json.load(f)
    return {**DEFAULT_CONFIG, **user_config}


def check_lighthouse_installed() -> bool:
    return shutil.which("lighthouse") is not None


def run_lighthouse(url: str, strategy: str) -> dict:
    """Menjalankan Lighthouse CLI dan mem-parsing hasil JSON-nya."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_path = tmp.name

    form_factor_flags = (
        ["--preset=desktop"] if strategy == "desktop" else []
    )

    cmd = [
        "lighthouse",
        url,
        "--output=json",
        f"--output-path={output_path}",
        "--only-categories=performance",
        "--chrome-flags=--headless --disable-gpu --no-sandbox",
        "--quiet",
    ] + form_factor_flags

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
        shell=(os.name == "nt"),  # shell=True cuma dibutuhkan di Windows
    )

    # Lighthouse di Windows kadang exit dengan error walau laporan JSON
    # sudah berhasil dibuat -- errornya cuma terjadi saat proses
    # pembersihan file sementara (biasanya dikunci antivirus/Defender).
    # Jadi kita cek dulu apakah file laporan valid, baru anggap gagal
    # kalau memang tidak ada/rusak.
    report_is_valid = os.path.isfile(output_path) and os.path.getsize(output_path) > 0

    if not report_is_valid:
        raise RuntimeError(
            f"Lighthouse gagal, tidak ada laporan dihasilkan. "
            f"stderr: {(result.stderr or '')[:500]}"
        )

    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        audits = data["audits"]
        categories = data["categories"]

        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "url": url,
            "strategy": strategy,
            "performance_score": round(categories["performance"]["score"] * 100),
            "fcp": audits["first-contentful-paint"]["displayValue"],
            "lcp": audits["largest-contentful-paint"]["displayValue"],
            "cls": audits["cumulative-layout-shift"]["displayValue"],
            "speed_index": audits["speed-index"]["displayValue"],
            "tbt": audits["total-blocking-time"]["displayValue"],
        }
    finally:
        if os.path.isfile(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass  # file temp kita sendiri, aman diabaikan kalau gagal dihapus


def log_to_csv(row: dict) -> None:
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main() -> None:
    if not check_lighthouse_installed():
        print("Lighthouse CLI belum terinstall.")
        print("Install dulu dengan: npm install -g lighthouse")
        print("(Node.js harus sudah terinstall lebih dulu: https://nodejs.org)")
        return

    urls = load_urls()
    config = load_config()

    if not urls:
        print("urls.txt masih kosong atau tidak ditemukan.")
        return

    strategies = config["strategies"]
    delay = config["delay_between_requests_seconds"]

    print(f"Mengecek {len(urls)} URL x {len(strategies)} strategi (bisa agak lama, Lighthouse lokal lebih lambat dari API)...")

    for url in urls:
        for strategy in strategies:
            try:
                result = run_lighthouse(url, strategy)
                log_to_csv(result)
                print(
                    f"[{result['timestamp']}] {url:35s} {strategy:7s} "
                    f"| score={result['performance_score']:>3} "
                    f"| LCP={result['lcp']} | CLS={result['cls']}"
                )
            except subprocess.TimeoutExpired:
                print(f"Timeout mengecek '{url}' ({strategy}) - halaman terlalu lama dimuat atau tidak terjangkau.")
            except RuntimeError as e:
                print(f"Gagal cek '{url}' ({strategy}): {e}")
            except Exception as e:
                print(f"Gagal cek '{url}' ({strategy}): {e}")

            time.sleep(delay)


if __name__ == "__main__":
    main()
