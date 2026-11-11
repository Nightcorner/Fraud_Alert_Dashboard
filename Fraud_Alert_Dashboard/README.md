# Fraud Alert Analytics Dashboard — PaySim

Dashboard analitis untuk Final Project Big Data. Aplikasi menyajikan kembali hasil eksperimen Assignment II dalam bentuk visualisasi interaktif. Aplikasi **tidak menjalankan ulang model** dan **bukan sistem fraud monitoring real-time**.

## Fitur

- Ikhtisar dataset PaySim dan distribusi jenis transaksi.
- Evaluasi LightGBM dan Spark MLlib Random Forest.
- Confusion matrix, metrik klasifikasi, serta simulasi kapasitas alert.
- Graph Analytics dari sampel sistematis 99.416 transaksi.
- Perubahan fraud prevalence pada training, validation, dan test.
- Ringkasan pengujian business rules berbasis skenario sintetis.
- Halaman metodologi dan keterbatasan data.

## Menjalankan di Windows

1. Ekstrak ZIP dashboard ke folder yang mudah ditemukan.
2. Buka Command Prompt atau PowerShell di dalam folder `Fraud_Alert_Dashboard`.
3. Buat virtual environment (opsional, tetapi disarankan):

   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```

4. Instal pustaka:

   ```powershell
   py -m pip install -r requirements.txt
   ```

5. Jalankan dashboard:

   ```powershell
   streamlit run app.py
   ```

6. Browser akan membuka alamat lokal Streamlit (biasanya `http://localhost:8501`).

## Menjalankan di macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

## Struktur folder

- `app.py`: kode dashboard Streamlit.
- `data/audit/`: ringkasan audit PaySim dan distribusi tipe transaksi.
- `data/sklearn/`: metrik LightGBM, confusion matrix, evaluasi threshold, dan feature ablation.
- `data/spark/`: metrik Spark MLlib, confusion matrix, dan alert budget.
- `data/graph/`: ringkasan graf dan akun dengan degree tertinggi pada sampel.
- `data/logs/`: log pengujian otomatis.

## Sumber dataset

PaySim: https://www.kaggle.com/datasets/ealaxi/paysim1

CSV mentah PaySim tidak disertakan. Dashboard menggunakan output eksperimen yang disimpan pada folder `data/` sehingga dashboard dapat dijalankan tanpa mengunduh ulang dan memproses 6,36 juta baris.

## Catatan interpretasi yang wajib dipertahankan

1. PaySim adalah data sintetis transaksi mobile money, bukan data transaksi tarik tunai luar negeri, EDC, atau Base24.
2. Performa model berbasis saldo sangat tinggi karena pola sintetis, termasuk `amount == oldbalanceOrg` pada 8.034 dari 8.213 transaksi berlabel fraud. Jangan menyebut angka tersebut sebagai performa yang sudah terbukti pada bank nyata.
3. Graph Analytics dibuat menggunakan NetworkX pada sampel sistematis setiap 64 baris, sebanyak 99.416 transaksi. Degree akun bukan bukti fraud.
4. Business rules diuji menggunakan skenario sintetis; bukan stream transaksi PaySim atau integrasi real-time.
5. Dashboard ini adalah lapisan visualisasi dan interpretasi hasil eksperimen, bukan sistem produksi atau layanan notifikasi.

## Untuk demonstrasi / deployment

Untuk presentasi lokal, jalankan `streamlit run app.py`. Untuk membagikan dashboard melalui tautan publik, unggah folder proyek ini ke repositori GitHub dan deploy menggunakan Streamlit Community Cloud. Pastikan repositori hanya berisi data eksperimen yang memang boleh dibagikan, bukan informasi akun asli atau kredensial.
