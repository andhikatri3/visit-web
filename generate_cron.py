"""
Helper untuk generate baris jadwal cron GitHub Actions, sesuai jumlah
pengecekan per hari yang kamu mau. Otomatis disebar merata sepanjang
hari dan dikonversi dari WIB ke UTC (yang dipakai GitHub Actions).

Cara pakai:
    python generate_cron.py 8        # 8x sehari
    python generate_cron.py 12       # 12x sehari
    python generate_cron.py 4        # 4x sehari

Lalu copy-paste hasilnya ke .github/workflows/performance-check.yml,
menggantikan bagian di bawah `schedule:`.

Catatan: granularitas cron di sini per jam, jadi maksimal masuk akal
adalah 24x sehari (tiap jam).
"""

import sys


def generate(freq_per_day: int, start_hour_wib: int = 0) -> None:
    if freq_per_day <= 0 or freq_per_day > 24:
        print("Jumlah harus antara 1-24 (granularitas jadwal ini per jam).")
        return

    interval = 24 / freq_per_day
    print(f"# {freq_per_day}x sehari, disebar tiap ~{interval:.1f} jam")
    print("schedule:")
    for i in range(freq_per_day):
        hour_wib = int(start_hour_wib + i * interval) % 24
        hour_utc = (hour_wib - 7) % 24
        print(f'    - cron: "0 {hour_utc} * * *"  # {hour_wib:02d}:00 WIB')


if __name__ == "__main__":
    freq = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    generate(freq)
