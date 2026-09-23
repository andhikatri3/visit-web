# Website Performance Checker

Cek performa beberapa website. Hasil disimpan ke `performance_log.csv`.

Ada **dua script**, pakai salah satu sesuai situasi:

| Script | Cara kerja | Kapan dipakai |
|---|---|---|
| `check_performance.py` | Minta server Google (PageSpeed Insights API) yang mengakses situsmu | Situs bisa diakses publik dari internet manapun |
| `check_performance_local.py` | Chrome di komputermu sendiri yang mengakses situsmu (Lighthouse CLI) | Situs cuma bisa diakses dari jaringan Indonesia/lokal — **ini yang dipakai untuk penunggul.kim.id** |

> **Kenapa dua script?** PageSpeed Insights API "menyuruh" server Google
> di luar negeri untuk mengunjungi situsmu — jadi walau script dijalankan
> dari komputer di Indonesia, yang benar-benar mengakses situs tetaplah
> server Google. Kalau situsnya memblokir akses dari luar Indonesia
> (seperti penunggul.kim.id, yang di-hosting di infrastruktur Kementerian
> KOMINFO), request itu akan selalu gagal. `check_performance_local.py`
> memakai Chrome yang jalan langsung di komputermu, jadi request-nya
> benar-benar datang dari jaringan Indonesia.

## Struktur file

| File | Fungsi | Perlu diedit? |
|---|---|---|
| `urls.txt` | Daftar URL yang dicek | ✅ Ya, kalau mau tambah/kurangi link |
| `config.json` | Strategi (mobile/desktop) & jeda antar-request | Opsional |
| `check_performance.py` | Versi PageSpeed API (server Google) | ❌ |
| `check_performance_local.py` | Versi Lighthouse lokal (Chrome kamu) | ❌ |

## Setup untuk check_performance_local.py (dipakai untuk penunggul.kim.id)

1. **Install Node.js** kalau belum ada: https://nodejs.org (pilih versi LTS), restart PowerShell setelah install.
2. **Install Lighthouse CLI** (sekali saja):
   ```powershell
   npm install -g lighthouse
   ```
3. Pastikan **Google Chrome** sudah terinstall di komputer (biasanya sudah ada).
4. Tidak perlu API key untuk script ini — Lighthouse lokal gratis tanpa batas kuota.

## Setup untuk check_performance.py (opsional, kalau nanti ada situs lain yang publik)

**Buat API key PageSpeed Insights** (gratis):
- https://console.cloud.google.com/apis/credentials
- Buat project → Enable "PageSpeed Insights API" → Create credentials → **API key** (bukan OAuth client ID)
- Key akan berformat `AIzaSy...`

## Mengatur jumlah link (urls.txt)

Buka `urls.txt`, tambah/hapus baris URL langsung:

```
https://peunggul.kim.id
https://link-rotator-1.com
https://link-rotator-2.com
```

Baris yang diawali `#` diabaikan (bisa dipakai untuk nonaktifkan sementara
tanpa hapus). Commit & push perubahan, selesai — tidak perlu sentuh kode.

## Cara menjalankan (manual, dari lokal)

**Untuk penunggul.kim.id, pakai `check_performance_local.py`** (tidak
butuh API key):

```powershell
python check_performance_local.py
```

Catatan: versi Lighthouse lokal ini **lebih lambat** dari versi API
(Chrome benar-benar membuka & merender tiap halaman), jadi wajar kalau
satu URL butuh 10-30 detik. Untuk 1 URL x 2 strategi, total waktu
sekitar 1 menit.

---

Kalau nanti ada URL lain yang bisa diakses publik dari internet biasa
(bukan situs pemerintah/lokal), baru pakai versi API:

```powershell
$env:PAGESPEED_API_KEY = "AIzaSy...key-kamu"
python check_performance.py
```

## Menghitung kuota API

Formula: `jumlah URL x jumlah strategi x frekuensi/hari = total request/hari`

Contoh dengan `strategies: ["mobile", "desktop"]` (2 strategi):

| URL | Frekuensi | Request/hari | % dari kuota 25.000 |
|---|---|---|---|
| 10 | 8x | 160 | 0.6% |
| 20 | 8x | 320 | 1.3% |
| 20 | 62x | 2.480 | ~10% |

Kalau mau cek berapa % kuota terpakai untuk kombinasi tertentu, tinggal
kalikan sesuai tabel di atas.

## Melihat hasil

Hasil ada di `performance_log.csv`, ter-update otomatis tiap workflow
jalan (auto-commit ke repo). Kolom `url` membedakan tiap link.

| Kolom | Arti |
|---|---|
| timestamp | Waktu pengecekan |
| url | Link yang dicek |
| strategy | `mobile` atau `desktop` |
| performance_score | Skor performa 0-100 |
| fcp / lcp / cls / speed_index / tbt | Metrik Core Web Vitals |

## Deploy ke VPS (opsional, biar tidak perlu komputer nyala terus)

**Syarat wajib:** VPS harus berlokasi/ber-IP Indonesia, karena masalahnya
sama seperti PageSpeed API/GitHub Actions — kalau IP VPS bukan Indonesia,
request tetap akan gagal walau dijalankan dari server yang menyala 24 jam.
**Test dulu sebelum install apapun:**
```bash
curl -I https://penunggul.kim.id
```
Kalau hasilnya timeout, cari VPS lain. Kalau berhasil (dapat response
HTTP), lanjutkan setup.

**Setup di VPS (Ubuntu/Debian):**
```bash
# Upload folder performance-checker ke VPS (scp, git clone, atau cara lain)
cd performance-checker
chmod +x setup_vps.sh
bash setup_vps.sh
```
Script ini otomatis test akses, lalu install Node.js, Chrome, Lighthouse
CLI, dan Python dependency.

**Jadwalkan otomatis lewat cron** (misal 8x sehari, tiap 3 jam):
```bash
crontab -e
```
Tambahkan baris ini di editor yang terbuka:
```
0 */3 * * * cd /path/ke/performance-checker && python3 check_performance_local.py >> run.log 2>&1
```
Ganti `/path/ke/performance-checker` dengan lokasi folder sebenarnya di
VPS (cek dengan `pwd` saat berada di folder itu). Simpan dan keluar.

Cron di Linux pakai waktu VPS itu sendiri (bukan perlu konversi UTC
manual seperti GitHub Actions), tapi cek dulu timezone VPS-nya:
```bash
timedatectl
```
Kalau bukan `Asia/Jakarta`, bisa diubah dengan:
```bash
sudo timedatectl set-timezone Asia/Jakarta
```

## Catatan

- Install dependency sekali saja: `pip install requests`
- Tanpa API key, kemungkinan besar kena error 429 kalau cek lebih dari 1 URL.
- Limit API: 25.000 request/hari, 60 request per 100 detik per API key — jeda `delay_between_requests_seconds` di `config.json` (default 2 detik) sudah menjaga supaya tidak tabrakan dengan limit ini.
- Kalau ada URL tertentu yang gagal dengan error 400, sementara URL lain berhasil, cek juga apakah URL itu memang bisa diakses normal (bukan halaman error/pindah).
