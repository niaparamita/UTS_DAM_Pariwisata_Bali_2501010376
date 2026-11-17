# Data Ethics Checklist

Diperbarui: 2026-11-17 10:07:37 UTC

| No | Butir | Status | Bukti |
|---|---|---|---|
| 1 | Sumber data dan URL dicantumkan | Selesai | 8/8 berkas mentah tercatat di docs/provenance.json (URL, waktu UTC, lisensi, MD5). |
| 2 | Lisensi data diperiksa dan didokumentasikan | Sebagian | Status: Needs verification. Bukti halaman: data/raw/bukti_kepatuhan, ringkasan: docs/bukti_lisensi_tos.csv. |
| 3 | robots.txt dan Terms of Service diperiksa | Sebagian | robots.txt diperiksa (docs/bukti_robots.csv). ToS BELUM dibaca manual (set TOS_DIBACA_MANUAL=True setelah dibaca). |
| 4 | PII diidentifikasi | Selesai | Pemindaian seluruh sheet Excel dan seluruh CSV (docs/pii_scan_semua_sheet.csv): email, telepon, dan kata header PII. |
| 5 | PII dihapus/disamarkan/dinyatakan tidak relevan | Selesai | Dataset utama (wisnus bulanan) hanya angka agregat (tahun, bulan, jumlah). Berkas lain juga agregat statistik; tidak ada data individu. |
| 6 | Data minimization diterapkan | Selesai | Hanya 5 CSV statistik + Tabel 6, 7, 17, 28 yang dibaca/diproses; sheet Excel lain tidak diproses; dari API cuaca hanya suhu, hujan, hari hujan, dan angin yang diambil. |
| 7 | Potensi bias sampel dianalisis | Draf (tinjau ulang) | Wisnus berasal dari survei Dinas Pariwisata (estimasi survei, bukan sensus) sehingga ada galat sampling; wisman hanya yang datang langsung lewat pintu Bali (bukan yang lewat daerah lain); Tabel 7 bertanda data sementara; Tabel 17 hanya ODTW tercatat dan 2016-2017 tidak dipisah wisnus/wisman; cuaca hanya satu titik (Denpasar); 2020-2022 anomali pandemi. |
| 8 | Tujuan penggunaan data dijelaskan | Draf (tinjau ulang) | Tujuan akademik (UTS DAM): latihan akuisisi dan integrasi data; hasil hanya menyimpulkan asosiasi, bukan sebab-akibat; tidak untuk tujuan komersial. |
| 9 | Rencana penyimpanan dan penghapusan data dibuat | Draf (perlu konfirmasi) | Disimpan di Google Drive pribadi mahasiswa; raw tidak diubah; salinan dihapus setelah nilai mata kuliah final (jadwal ini asumsi, konfirmasikan). |