# Panduan awal Bab 7 — Dashboard dan Interpretasi Bisnis

Dokumen ini adalah bahan awal penulisan, bukan teks final. Sesuaikan gaya bahasa dengan laporan dan periksa kembali kecocokan setiap angka dengan tabel/gambar yang dipakai.

## 7.1 Proses Membangun Dashboard

Dashboard dibuat menggunakan Python dan Streamlit untuk menyajikan hasil eksperimen Assignment II dalam tampilan yang dapat ditelusuri melalui beberapa halaman. Data yang ditampilkan berasal dari output eksperimen yang telah disimpan, sehingga aplikasi tidak melatih ulang model atau membangun ulang graf saat dashboard dibuka. Visualisasi meliputi ringkasan dataset, evaluasi model Machine Learning, trade-off kapasitas alert, relasi akun pada graf, pola fraud antarpartisi, serta ringkasan validasi business rules berbasis skenario sintetis.

## 7.2 Interpretasi Bisnis atau Insights yang Diperoleh dari Dashboard

### Insight 1 — Kinerja model dipengaruhi karakteristik fitur dan dataset

Eksperimen LightGBM dengan fitur inti menghasilkan ROC-AUC 0,8873 dan Average Precision 0,3248 pada test set. Setelah fitur saldo sebelum transaksi dan fitur turunannya ditambahkan, ROC-AUC meningkat menjadi 0,9997 dan Average Precision menjadi 0,9994. Peningkatan tersebut tidak dapat langsung ditafsirkan sebagai kemampuan deteksi fraud yang siap diterapkan di bank. Audit dataset menunjukkan bahwa 8.034 dari 8.213 transaksi berlabel fraud memiliki nilai `amount` yang sama dengan `oldbalanceOrg`, sedangkan pola tersebut tidak ditemukan pada transaksi non-fraud. Kondisi ini menunjukkan bahwa model memanfaatkan pola yang sangat khas pada simulator PaySim. Implikasi bisnisnya, pemilihan fitur dan evaluasi model perlu mempertimbangkan asal-usul data serta validasi pada data operasional yang lebih representatif.

### Insight 2 — Kapasitas investigasi berkaitan dengan cakupan deteksi dan false positive

Pada skenario pemeringkatan LightGBM di test set, batas alert sebesar 1% menghasilkan 1.036 alert dan menangkap 1.036 transaksi fraud, atau recall 64,75%. Ketika kapasitas alert dinaikkan menjadi 3%, sebanyak 3.107 alert dihasilkan dan 1.599 transaksi fraud tertangkap, atau recall 99,94%, tetapi terdapat 1.508 false positive. Hasil ini menggambarkan trade-off yang relevan bagi pengelola fraud: peningkatan cakupan deteksi dapat meningkatkan jumlah transaksi yang perlu diperiksa. Angka tersebut merupakan simulasi kapasitas berdasarkan skor pada test set, bukan kebijakan operasional yang telah diterapkan.

### Insight 3 — Relasi antarakun memberi konteks tambahan bagi analisis transaksi

Graph Analytics dilakukan pada 99.416 transaksi sampel dari 6.362.620 transaksi sumber menggunakan sampling sistematis setiap 64 baris. Graf menghasilkan 191.849 node dan 99.416 relasi berarah. Weighted in-degree tertinggi pada sampel adalah 5, sementara weighted out-degree tertinggi adalah 2. Representasi graf membantu memperlihatkan hubungan antar-akun yang tidak dapat dilihat dari satu baris transaksi secara terpisah. Dalam proses bisnis, informasi relasi dapat dipakai sebagai konteks pemeriksaan lanjutan. Namun, degree yang tinggi tidak membuktikan fraud, dan hasil sampel tidak dapat dianggap sebagai gambaran lengkap jaringan transaksi.

## Insight pendukung — Perubahan fraud prevalence antarpartisi

Fraud prevalence pada training set adalah sekitar 0,0951%, validation set 0,4700%, dan test set 1,5448%. Perbedaan proporsi tersebut memperlihatkan bahwa komposisi label dapat berubah pada urutan simulasi yang berbeda. Dalam konteks bisnis, perubahan distribusi seperti ini perlu dipantau karena dapat memengaruhi jumlah alert, beban investigasi, dan relevansi threshold model. Kolom `step` pada PaySim merupakan urutan simulasi, bukan tanggal kalender.

## Catatan batasan yang harus dipertahankan

- PaySim adalah dataset sintetis transaksi mobile money, bukan dataset khusus tarik tunai luar negeri, EDC, atau Base24.
- Metrik model yang sangat tinggi tidak membuktikan performa pada transaksi bank nyata.
- Graph Analytics menggunakan sampel sistematis, bukan keseluruhan transaksi.
- Business rules diperiksa melalui skenario sintetis dan belum menjadi sistem streaming real-time.
- Dashboard merupakan lapisan visualisasi hasil eksperimen, bukan sistem produksi atau layanan notifikasi.
