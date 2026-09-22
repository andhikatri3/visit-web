# Website Performance Checker

Cek performa beberapa website otomatis, jadwal fleksibel, pakai Google
PageSpeed Insights API. Hasil disimpan ke `performance_log.csv`.

## Struktur file

| File | Fungsi | Perlu diedit? |
|---|---|---|
| `urls.txt` | Daftar URL yang dicek | ✅ Ya, kalau mau tambah/kurangi link |
| `config.json` | Strategi (mobile/desktop) & jeda antar-request | Opsional |
| `check_performance.py` | Kode utama (baca 2 file di atas) | ❌ Tidak perlu diedit lagi |
| `generate_cron.py` | Bantu bikin jadwal cron otomatis | Dipakai kalau mau ganti frekuensi |
| `.github/workflows/performance-check.yml` | Jadwal otomatis di GitHub Actions | ✅ Ya, kalau mau ganti frekuensi |

## Setup awal (sekali saja)

1. Upload seluruh folder ini ke repo GitHub baru (bisa privat):
   ```bash
   cd performance-checker
   git init
   git add .
   git commit -m "Initial setup"
   git branch -M main
   git remote add origin https://github.com/USERNAME/NAMA-REPO.git
   git push -u origin main
   ```

2. **Buat API key PageSpeed Insights** (gratis, wajib kalau cek lebih dari
   1 URL):
   - https://console.cloud.google.com/apis/credentials
   - Buat project → Enable "PageSpeed Insights API" → Create credentials → API key

3. **Masukkan API key ke GitHub Secrets**:
   - Repo → Settings → Secrets and variables → Actions → New repository secret
   - Name: `PAGESPEED_API_KEY`, Value: (paste key kamu)

## Mengatur jumlah link (urls.txt)

Buka `urls.txt`, tambah/hapus baris URL langsung:

```
https://peunggul.kim.id
https://link-rotator-1.com
https://link-rotator-2.com
```

Baris yang diawali `#` diabaikan (bisa dipakai untuk nonaktifkan sementara
tanpa hapus). Commit & push perubahan, selesai — tidak perlu sentuh kode.

## Mengatur frekuensi pengecekan

Frekuensi diatur lewat jadwal `cron` di
`.github/workflows/performance-check.yml`. Supaya tidak perlu hitung
manual konversi WIB↔UTC, pakai `generate_cron.py`:

```bash
python generate_cron.py 8     # mau 8x sehari
python generate_cron.py 4     # mau 4x sehari
python generate_cron.py 12    # mau 12x sehari
```

Script akan cetak baris `schedule:` yang sudah dikonversi ke UTC dan
disebar merata sepanjang hari. Copy hasilnya, paste ke
`performance-check.yml` menggantikan bagian `schedule:` yang lama, lalu
commit & push.

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

## Menjalankan manual di lokal (opsional, untuk testing)

```bash
pip install requests
export PAGESPEED_API_KEY="isi-api-key-kamu"
python check_performance.py
```

## Catatan

- Jadwal cron GitHub Actions bisa meleset beberapa menit dari waktu pas — wajar untuk free tier.
- Tanpa API key, kemungkinan besar kena error 429 kalau cek lebih dari 1 URL.
- Limit tambahan: 60 request per 100 detik per API key, dan ~240/menit per project — jeda `delay_between_requests_seconds` di `config.json` (default 2 detik) sudah menjaga supaya tidak tabrakan dengan limit ini.
