"""
Script untuk cek performa website secara berkala menggunakan
Google PageSpeed Insights API, lalu menyimpan hasilnya ke CSV.

Pengaturan URL dan opsi lain TIDAK di file ini, tapi di:
    - urls.txt     -> daftar URL yang mau dicek (satu per baris)
    - config.json  -> strategi (mobile/desktop) & jeda antar-request

Cara pakai lokal:
    pip install requests
    python check_performance.py

Bisa juga dijalankan otomatis lewat GitHub Actions (lihat
.github/workflows/performance-check.yml).
"""

import os
import csv
import json
import time
from datetime import datetime

import requests

BASE_DIR = os.path.dirname(__file__)
URLS_FILE = os.path.join(BASE_DIR, "urls.txt")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
CSV_FILE = os.path.join(BASE_DIR, "performance_log.csv")

# API key opsional tapi sangat disarankan (gratis, kuota 25.000/hari).
# Cara dapat key: https://developers.google.com/speed/docs/insights/v5/get-started
API_KEY = os.environ.get("PAGESPEED_API_KEY", "AIzaSyC4LFLmaNk25sh8kSQCZmuxE58mzfcoImk")

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


def get_pagespeed_data(url: str, strategy: str) -> dict:
    api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url": url,
        "strategy": strategy,
        "category": "performance",
    }
    if API_KEY:
        params["key"] = API_KEY

    response = requests.get(api_url, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()

    lighthouse = data["lighthouseResult"]
    audits = lighthouse["audits"]

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "url": url,
        "strategy": strategy,
        "performance_score": round(lighthouse["categories"]["performance"]["score"] * 100),
        "fcp": audits["first-contentful-paint"]["displayValue"],
        "lcp": audits["largest-contentful-paint"]["displayValue"],
        "cls": audits["cumulative-layout-shift"]["displayValue"],
        "speed_index": audits["speed-index"]["displayValue"],
        "tbt": audits["total-blocking-time"]["displayValue"],
    }


def log_to_csv(row: dict) -> None:
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main() -> None:
    urls = load_urls()
    config = load_config()

    if not urls:
        print("urls.txt masih kosong atau tidak ditemukan. Tambahkan minimal 1 URL dulu.")
        return

    strategies = config["strategies"]
    delay = config["delay_between_requests_seconds"]

    print(f"Mengecek {len(urls)} URL x {len(strategies)} strategi = {len(urls) * len(strategies)} request...")

    for url in urls:
        for strategy in strategies:
            try:
                result = get_pagespeed_data(url, strategy)
                log_to_csv(result)
                print(
                    f"[{result['timestamp']}] {url:35s} {strategy:7s} "
                    f"| score={result['performance_score']:>3} "
                    f"| LCP={result['lcp']} | CLS={result['cls']}"
                )
            except Exception as e:
                print(f"Gagal cek '{url}' ({strategy}): {e}")

            time.sleep(delay)


if __name__ == "__main__":
    main()
