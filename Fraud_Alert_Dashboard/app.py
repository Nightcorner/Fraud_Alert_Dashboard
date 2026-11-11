from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"

st.set_page_config(
    page_title="Fraud Alert Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Data loading helpers
# -----------------------------
@st.cache_data(show_spinner=False)
def load_json(relative_path: str) -> dict[str, Any]:
    path = DATA_DIR / relative_path
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_csv(relative_path: str) -> pd.DataFrame:
    path = DATA_DIR / relative_path
    return pd.read_csv(path)


def fmt_int(value: Any) -> str:
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


def fmt_pct(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value) * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return "—"


def metric_card(label: str, value: str, help_text: str | None = None) -> None:
    st.metric(label=label, value=value, help=help_text)


def load_all() -> dict[str, Any]:
    return {
        "audit": load_json("audit/paysim_audit.json"),
        "type_distribution": load_csv("audit/type_distribution.csv"),
        "lgbm": load_json("sklearn/final_test_metrics.json"),
        "lgbm_metrics": load_csv("sklearn/final_test_metrics.csv"),
        "lgbm_split": load_csv("sklearn/temporal_split_summary.csv"),
        "lgbm_budget": load_csv("sklearn/test_alert_budget_metrics.csv"),
        "ablation": load_csv("sklearn/test_feature_ablation_comparison.csv"),
        "lgbm_cm": pd.read_csv(DATA_DIR / "sklearn/confusion_matrix.csv", index_col=0),
        "feature_importance": load_csv("sklearn/feature_importance.csv"),
        "spark": load_json("spark/final_test_metrics.json"),
        "spark_metrics": load_csv("spark/final_test_metrics.csv"),
        "spark_split": load_csv("spark/temporal_split_summary.csv"),
        "spark_budget": load_csv("spark/test_alert_budget_metrics.csv"),
        "spark_cm": pd.read_csv(DATA_DIR / "spark/confusion_matrix.csv", index_col=0),
        "graph": load_json("graph/graph_summary.json"),
        "top_in": load_csv("graph/top50_accounts_by_in_degree.csv"),
        "top_out": load_csv("graph/top50_accounts_by_out_degree.csv"),
        "tests_log": (DATA_DIR / "logs/unit_tests_final.log").read_text(encoding="utf-8"),
    }


try:
    D = load_all()
except Exception as exc:  # show a useful local setup error rather than a traceback
    st.error("Dashboard belum dapat membaca file hasil eksperimen.")
    st.code(str(exc))
    st.info("Pastikan folder data/ berada satu tingkat dengan app.py dan seluruh file dari paket dashboard tetap berada di tempatnya.")
    st.stop()

A = D["audit"]
G = D["graph"]

# -----------------------------
# Sidebar navigation and filters
# -----------------------------
st.sidebar.title("Fraud Analytics")
st.sidebar.caption("PaySim experiment dashboard")
page = st.sidebar.radio(
    "Navigasi",
    ["Ringkasan", "Machine Learning", "Graph Analytics", "Pola Transaksi & Validasi Rules", "Metodologi & Batasan"],
)

st.sidebar.divider()
st.sidebar.caption("Sumber data")
st.sidebar.write("PaySim synthetic financial dataset")
st.sidebar.caption("6.362.620 transaksi · 11 atribut")
st.sidebar.caption("Dataset: Kaggle / PaySim")
st.sidebar.markdown("[Buka sumber dataset](https://www.kaggle.com/datasets/ealaxi/paysim1)")

# -----------------------------
# Header
# -----------------------------
st.title("Fraud Alert Analytics Dashboard")
st.caption("Visualisasi hasil pengolahan data PaySim untuk mendukung analisis fraud dan interpretasi bisnis.")
st.warning(
    "**Konteks penggunaan:** PaySim merupakan dataset sintetis transaksi mobile money. "
    "Dataset ini digunakan untuk eksperimen Machine Learning dan Graph Analytics, "
    "bukan bukti langsung kinerja sistem pada transaksi tarik tunai luar negeri, EDC, atau Base24."
)

# -----------------------------
# Page: Ringkasan
# -----------------------------
if page == "Ringkasan":
    st.subheader("Ikhtisar Dataset")
    fraud_rate = A["fraud_rate_percent"] / 100.0
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total transaksi", fmt_int(A["rows"]))
    with c2:
        metric_card("Transaksi berlabel fraud", fmt_int(A["fraud_count"]))
    with c3:
        metric_card("Fraud prevalence", fmt_pct(fraud_rate, 3))
    with c4:
        metric_card("Jumlah atribut", fmt_int(len(A["columns"])))

    st.divider()
    left, right = st.columns([1.1, 0.9])
    with left:
        st.markdown("#### Distribusi transaksi berdasarkan tipe")
        typ = D["type_distribution"].copy().sort_values("count", ascending=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=typ["type"], x=typ["count"], name="Seluruh transaksi",
            orientation="h", marker_color="#9BB7D4", hovertemplate="%{y}<br>Jumlah: %{x:,}<extra></extra>"
        ))
        fig.add_trace(go.Bar(
            y=typ["type"], x=typ["fraud_count"], name="Transaksi berlabel fraud",
            orientation="h", marker_color="#E07A5F", hovertemplate="%{y}<br>Fraud: %{x:,}<extra></extra>"
        ))
        fig.update_layout(barmode="group", height=350, xaxis_title="Jumlah transaksi", yaxis_title="Tipe transaksi", legend_title="Keterangan", margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Jumlah fraud adalah bagian dari jumlah transaksi pada setiap tipe, bukan kategori yang terpisah.")

    with right:
        st.markdown("#### Komposisi label fraud")
        fraud_by_type = A.get("fraud_by_type", {})
        fraud_df = pd.DataFrame({"Tipe transaksi": list(fraud_by_type.keys()), "Jumlah fraud": list(fraud_by_type.values())})
        if not fraud_df.empty:
            fig2 = px.pie(fraud_df, names="Tipe transaksi", values="Jumlah fraud", hole=0.58,
                          color_discrete_sequence=["#E07A5F", "#3D8B8B"])
            fig2.update_traces(textposition="outside", textinfo="label+percent+value")
            fig2.update_layout(height=350, margin=dict(l=10, r=10, t=20, b=10), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        st.info(
            "Pada dataset PaySim ini, label fraud hanya muncul pada transaksi **CASH_OUT** dan **TRANSFER**. "
            "Temuan ini menggambarkan pola label di simulator, bukan aturan universal untuk transaksi perbankan."
        )

    st.divider()
    st.markdown("#### Tiga insight utama")
    i1, i2, i3 = st.columns(3)
    with i1:
        st.markdown("**1 · Machine Learning**")
        st.write(
            "Model dengan fitur saldo sebelum transaksi menunjukkan metrik sangat tinggi. "
            "Namun, sebagian besar kekuatan prediksi terkait pola khusus generator PaySim, sehingga hasil tidak boleh digeneralisasikan ke bank nyata."
        )
    with i2:
        st.markdown("**2 · Graph Analytics**")
        st.write(
            f"Graf dari {fmt_int(G['sampled_transactions'])} transaksi sampel membentuk "
            f"{fmt_int(G['nodes'])} node dan {fmt_int(G['directed_edges'])} relasi berarah. "
            "Relasi memberi konteks antarakun, tetapi degree bukan bukti fraud."
        )
    with i3:
        st.markdown("**3 · Kapasitas investigasi**")
        st.write(
            "Pada simulasi LightGBM, kapasitas alert 1% menangkap 64,75% fraud; kapasitas 3% menangkap 99,94%, "
            "tetapi menghasilkan 1.508 false positive. Ini memperlihatkan trade-off antara cakupan deteksi dan beban investigasi."
        )

    st.caption("Insight dirangkum dari output eksperimen Assignment II. Lihat menu Machine Learning dan Graph Analytics untuk metrik serta batasan analisis.")

# -----------------------------
# Page: Machine Learning
# -----------------------------
elif page == "Machine Learning":
    st.subheader("Evaluasi Model Machine Learning")
    model_choice = st.selectbox("Pilih model", ["LightGBM", "Spark MLlib Random Forest"], index=0)
    if model_choice == "LightGBM":
        metrics = D["lgbm"]["test_metrics_at_validation_f1_threshold"]
        budget_df = D["lgbm_budget"].copy()
        cm = D["lgbm_cm"]
        model_label = "LightGBM · pre-event balance features"
        model_note = "Threshold dipilih berdasarkan F1 maksimum pada validation set; test set digunakan untuk evaluasi akhir."
    else:
        metrics = D["spark"]["test_metrics_at_validation_threshold"]
        budget_df = D["spark_budget"].copy()
        cm = D["spark_cm"]
        model_label = "Spark MLlib Random Forest · pre-event features"
        model_note = "Threshold dipilih berdasarkan F1 maksimum pada validation set; test set digunakan untuk evaluasi akhir."

    st.caption(model_label)
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: metric_card("ROC-AUC", f"{metrics['roc_auc']:.4f}")
    with m2: metric_card("Average Precision", f"{metrics['average_precision']:.4f}")
    with m3: metric_card("Precision", fmt_pct(metrics["precision"]))
    with m4: metric_card("Recall", fmt_pct(metrics["recall"]))
    with m5: metric_card("F1-score", fmt_pct(metrics["f1"]))
    st.caption(model_note)

    st.warning(
        "**Interpretasi wajib:** hasil sangat tinggi pada model berbasis saldo dipengaruhi pola sintetis PaySim. "
        "Audit menemukan 8.034 dari 8.213 transaksi berlabel fraud memiliki amount yang sama dengan oldbalanceOrg, "
        "sedangkan pola tersebut tidak ditemukan pada transaksi non-fraud. Karena itu, angka ini bukan estimasi performa pada bank nyata."
    )

    cm_left, cm_right = st.columns([0.9, 1.1])
    with cm_left:
        st.markdown("#### Confusion matrix — test set")
        cm_values = cm.to_numpy(dtype=int)
        fig_cm = go.Figure(data=go.Heatmap(
            z=cm_values,
            x=["Prediksi non-fraud", "Prediksi fraud"],
            y=["Aktual non-fraud", "Aktual fraud"],
            text=[[fmt_int(x) for x in row] for row in cm_values],
            texttemplate="%{text}",
            colorscale=[[0, "#EAF1F8"], [1, "#357A82"]],
            showscale=False,
            hovertemplate="%{y}<br>%{x}<br>Jumlah: %{z:,}<extra></extra>",
        ))
        fig_cm.update_layout(height=310, margin=dict(l=10, r=10, t=15, b=10))
        st.plotly_chart(fig_cm, use_container_width=True)
    with cm_right:
        st.markdown("#### Ringkasan hasil pada test set")
        result_rows = [
            ("Jumlah transaksi diuji", metrics["rows"]),
            ("Alert yang dihasilkan", metrics["alerts"]),
            ("True positive", metrics["true_positive"]),
            ("False positive", metrics["false_positive"]),
            ("False negative", metrics["false_negative"]),
            ("Threshold", f"{metrics['threshold']:.6f}"),
        ]
        st.dataframe(pd.DataFrame(result_rows, columns=["Metrik", "Nilai"]), hide_index=True, use_container_width=True)
        st.caption("Metrik di atas berasal dari periode test (step 601–743), setelah threshold ditentukan pada validation set.")

    st.divider()
    st.markdown("#### Trade-off kapasitas alert")
    st.write("Pilih batas kapasitas alert untuk melihat hubungan antara jumlah alert, transaksi fraud yang tertangkap, dan false positive.")
    selected_budget = st.select_slider(
        "Batas alert dari seluruh transaksi test",
        options=sorted(budget_df["alert_budget_percent"].astype(float).unique().tolist()),
        value=3.0,
        format_func=lambda x: f"{x:g}%",
    )
    selected_row = budget_df.loc[budget_df["alert_budget_percent"].astype(float) == float(selected_budget)].iloc[0]
    b1, b2, b3, b4 = st.columns(4)
    with b1: metric_card("Jumlah alert", fmt_int(selected_row["alerts"]))
    with b2: metric_card("Fraud tertangkap", fmt_int(selected_row["true_positive"]))
    with b3: metric_card("False positive", fmt_int(selected_row["false_positive"]))
    with b4: metric_card("Recall", fmt_pct(selected_row["recall"]))

    plot_budget = budget_df.copy()
    fig_budget = go.Figure()
    fig_budget.add_trace(go.Bar(x=plot_budget["alert_budget_percent"], y=plot_budget["true_positive"], name="True positive", marker_color="#3D8B8B"))
    fig_budget.add_trace(go.Bar(x=plot_budget["alert_budget_percent"], y=plot_budget["false_positive"], name="False positive", marker_color="#E6A15C"))
    fig_budget.update_layout(barmode="stack", height=340, xaxis_title="Batas alert (%)", yaxis_title="Jumlah alert", legend_title="Jenis hasil", margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig_budget, use_container_width=True)
    st.caption("Batas kapasitas adalah skenario pemeringkatan berdasarkan skor model pada test set, bukan kebijakan operasional yang sudah diterapkan.")

    st.divider()
    st.markdown("#### Dampak pemilihan fitur pada LightGBM")
    ab = D["ablation"].copy()
    ab_display = ab[["candidate", "test_roc_auc", "test_average_precision", "test_precision", "test_recall", "test_false_positive", "test_false_negative"]].copy()
    ab_display["candidate"] = ab_display["candidate"].map({"pre_event_core": "Fitur inti", "pre_event_balance": "Fitur inti + saldo"}).fillna(ab_display["candidate"])
    st.dataframe(
        ab_display.rename(columns={
            "candidate": "Kandidat fitur", "test_roc_auc": "ROC-AUC", "test_average_precision": "Average Precision",
            "test_precision": "Precision", "test_recall": "Recall", "test_false_positive": "False positive", "test_false_negative": "False negative"
        }).style.format({"ROC-AUC": "{:.4f}", "Average Precision": "{:.4f}", "Precision": "{:.2%}", "Recall": "{:.2%}"}),
        hide_index=True, use_container_width=True,
    )
    st.info(
        "**Insight bisnis:** hasil klasifikasi yang sangat tinggi dapat tampak menarik bagi pengambil keputusan, "
        "tetapi pemilihan fitur harus mempertimbangkan ketersediaan atribut saat alert dibuat dan pola khusus dataset. "
        "Fitur yang memicu performa tinggi perlu diverifikasi pada data transaksi yang lebih representatif."
    )

    st.download_button(
        "Unduh tabel trade-off alert (CSV)",
        data=budget_df.to_csv(index=False).encode("utf-8"),
        file_name=f"alert_budget_{'lightgbm' if model_choice == 'LightGBM' else 'spark_mllib'}.csv",
        mime="text/csv",
    )

# -----------------------------
# Page: Graph Analytics
# -----------------------------
elif page == "Graph Analytics":
    st.subheader("Graph Analytics — Relasi Antarakun")
    g1, g2, g3, g4 = st.columns(4)
    with g1: metric_card("Transaksi sampel", fmt_int(G["sampled_transactions"]))
    with g2: metric_card("Node / akun", fmt_int(G["nodes"]))
    with g3: metric_card("Relasi berarah", fmt_int(G["directed_edges"]))
    with g4: metric_card("Fraud pada sampel", fmt_int(G["sampled_fraud_transactions"]))

    st.info(
        f"Graf dibangun dari **{fmt_int(G['total_rows_in_source'])}** transaksi sumber dengan metode "
        f"**{G['sampling_method']}**. Hasil ini menggambarkan sampel, bukan seluruh jaringan transaksi."
    )

    gl, gr = st.columns([1.2, 0.8])
    with gl:
        st.markdown("#### Akun dengan relasi masuk terbanyak")
        top_n = st.slider("Jumlah akun yang ditampilkan", min_value=5, max_value=20, value=10, step=5)
        top_df = D["top_in"].head(top_n).copy().sort_values("weighted_in_degree", ascending=True)
        fig_in = px.bar(top_df, x="weighted_in_degree", y="account", orientation="h",
                        labels={"weighted_in_degree": "Weighted in-degree", "account": "ID akun"},
                        color="weighted_in_degree", color_continuous_scale=["#BDD7D7", "#357A82"])
        fig_in.update_layout(height=440, coloraxis_showscale=False, margin=dict(l=10, r=10, t=15, b=10))
        st.plotly_chart(fig_in, use_container_width=True)
    with gr:
        st.markdown("#### Ringkasan struktur graf")
        summary_rows = [
            ("Akun pengirim unik", G["unique_source_accounts_sample"]),
            ("Akun penerima unik", G["unique_destination_accounts_sample"]),
            ("Weighted in-degree tertinggi", max(x["weight"] for x in G["weighted_in_degree_top10"])),
            ("Weighted out-degree tertinggi", max(x["weight"] for x in G["weighted_out_degree_top10"])),
        ]
        st.dataframe(pd.DataFrame(summary_rows, columns=["Indikator", "Nilai"]), hide_index=True, use_container_width=True)
        st.markdown("**Contoh akun dengan relasi masuk tertinggi**")
        st.dataframe(D["top_in"].head(10), hide_index=True, use_container_width=True)

    st.warning(
        "**Batas interpretasi:** degree yang tinggi hanya menunjukkan jumlah relasi pada graf sampel. "
        "Hal tersebut tidak membuktikan bahwa akun merupakan pelaku fraud. Pengambilan sampel sistematis juga dapat "
        "menghilangkan atau mengubah pola relasi yang jarang terjadi."
    )
    st.markdown("#### Insight bisnis")
    st.write(
        "Analisis graf dapat membantu analis melihat keterhubungan akun penerima dan pengirim yang tidak terlihat "
        "dari satu transaksi secara terpisah. Dalam penggunaan operasional, akun dengan konektivitas relatif tinggi "
        "dapat menjadi kandidat pemeriksaan lanjutan, tetapi perlu dikombinasikan dengan atribut transaksi, riwayat, "
        "dan verifikasi tambahan. Hasil sampel ini belum dapat digunakan sebagai daftar akun berisiko."
    )
    st.download_button(
        "Unduh daftar akun dengan relasi masuk (CSV)",
        data=D["top_in"].to_csv(index=False).encode("utf-8"),
        file_name="top_accounts_by_in_degree.csv", mime="text/csv",
    )

# -----------------------------
# Page: Transaction patterns and rule tests
# -----------------------------
elif page == "Pola Transaksi & Validasi Rules":
    st.subheader("Pola Transaksi dan Perubahan Antarpartisi")
    split_df = D["lgbm_split"].copy()
    split_df["fraud_rate"] = split_df["fraud_count"] / split_df["rows"]
    split_df["nonfraud_rate"] = split_df["nonfraud_count"] / split_df["rows"]
    split_df["Fraud prevalence"] = split_df["fraud_rate"] * 100

    fig_split = px.bar(split_df, x="partition", y="Fraud prevalence", text=split_df["Fraud prevalence"].map(lambda x: f"{x:.3f}%"),
                       labels={"partition": "Partisi kronologis", "Fraud prevalence": "Fraud prevalence (%)"},
                       color="partition", color_discrete_sequence=["#9BB7D4", "#6C9B9B", "#E07A5F"])
    fig_split.update_layout(height=350, showlegend=False, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig_split, use_container_width=True)
    st.dataframe(
        split_df[["partition", "rows", "fraud_count", "nonfraud_count", "step_min", "step_max", "Fraud prevalence"]].rename(columns={
            "partition": "Partisi", "rows": "Jumlah transaksi", "fraud_count": "Fraud", "nonfraud_count": "Non-fraud", "step_min": "Step awal", "step_max": "Step akhir"
        }).style.format({"Fraud prevalence": "{:.4f}%"}),
        hide_index=True, use_container_width=True,
    )
    st.info(
        "**Insight bisnis:** proporsi fraud pada partisi test lebih tinggi daripada training. "
        "Jika perubahan komposisi serupa terjadi pada data operasional, organisasi perlu memantau perubahan pola "
        "transaksi dan mengevaluasi ulang threshold serta kapasitas tim investigasi. Pada PaySim, step adalah urutan simulasi, bukan tanggal kalender."
    )

    st.divider()
    st.markdown("#### Distribusi label fraud berdasarkan tipe transaksi")
    type_df = D["type_distribution"].copy()
    type_df["fraud_share_of_type"] = type_df["fraud_count"] / type_df["count"]
    type_df["share_of_all_fraud"] = type_df["fraud_count"] / max(int(type_df["fraud_count"].sum()), 1)
    st.dataframe(
        type_df.rename(columns={"type": "Tipe transaksi", "count": "Jumlah transaksi", "fraud_count": "Jumlah fraud", "fraud_share_of_type": "Fraud / tipe", "share_of_all_fraud": "Kontribusi ke seluruh fraud"}).style.format({
            "Fraud / tipe": "{:.3%}", "Kontribusi ke seluruh fraud": "{:.2%}"
        }), hide_index=True, use_container_width=True,
    )

    st.divider()
    st.markdown("#### Validasi business rules berbasis skenario sintetis")
    log_text = D["tests_log"]
    passed = log_text.count(" ... ok")
    failed = log_text.count(" ... FAIL")
    t1, t2, t3 = st.columns(3)
    with t1: metric_card("Pengujian otomatis berhasil", fmt_int(passed))
    with t2: metric_card("Pengujian gagal", fmt_int(failed))
    with t3: metric_card("Status", "LULUS" if failed == 0 and passed > 0 else "Perlu cek")
    st.caption("Pengujian ini memeriksa fungsi fitur dan business rules dengan skenario uji sintetis. Ini bukan pemrosesan seluruh transaksi PaySim dan bukan integrasi real-time.")
    with st.expander("Lihat rincian log pengujian"):
        st.code(log_text, language="text")

# -----------------------------
# Page: Methodology and limitations
# -----------------------------
elif page == "Metodologi & Batasan":
    st.subheader("Metodologi, Definisi, dan Batasan")
    st.markdown("#### Sumber dan cakupan data")
    st.write(
        f"Dataset: **{A['dataset']}**. Data berisi {fmt_int(A['rows'])} baris, "
        f"{len(A['columns'])} kolom, dan rentang step {A['steps_min']}–{A['steps_max']}. "
        "Dataset merupakan data sintetis transaksi mobile money."
    )
    st.markdown("#### Pembagian data Machine Learning")
    st.write("Pembagian dilakukan secara kronologis berdasarkan `step`: training 1–520, validation 521–600, dan test 601–743. Threshold dipilih pada validation set dan dievaluasi pada test set.")
    st.markdown("#### Kebijakan fitur")
    st.write("`isFraud` hanya digunakan sebagai target, bukan fitur. `isFlaggedFraud` serta saldo setelah transaksi dikeluarkan. Fitur saldo sebelum transaksi digunakan pada eksperimen tertentu dengan catatan ketersediaan operasional dan pola sintetisnya.")
    st.markdown("#### Keterbatasan utama")
    limitations = [
        "PaySim tidak memuat atribut negara transaksi, status approved/declined, kanal EDC, atau identitas ATM yang dibutuhkan untuk menguji langsung kasus tarik tunai luar negeri.",
        "Kinerja model pada PaySim tidak membuktikan kinerja pada transaksi bank nyata. Pola amount == oldbalanceOrg sangat kuat pada label fraud simulator.",
        "Graph Analytics menggunakan sampel sistematis setiap 64 baris, bukan seluruh transaksi. Hasilnya bersifat deskriptif.",
        "Graph dibangun dengan NetworkX pada lingkungan eksperimen; tidak ada klaim bahwa pemrosesan graf terdistribusi atau graph database telah diimplementasikan.",
        "Business rules diuji menggunakan fixture sintetis; belum terhubung ke Kafka, Spark Structured Streaming, atau layanan notifikasi produksi.",
        "Visualisasi ini merupakan dashboard analitis dari hasil eksperimen yang tersedia, bukan sistem pemantauan transaksi langsung."
    ]
    for item in limitations:
        st.markdown(f"- {item}")
    st.markdown("#### Definisi singkat")
    st.dataframe(pd.DataFrame([
        ("Precision", "Proporsi alert yang benar-benar berlabel fraud di antara semua alert."),
        ("Recall", "Proporsi transaksi fraud yang berhasil ditandai model."),
        ("ROC-AUC", "Kemampuan model memisahkan dua kelas pada berbagai threshold."),
        ("Average Precision", "Ringkasan kurva precision–recall, relevan untuk kelas yang tidak seimbang."),
        ("In-degree", "Jumlah relasi masuk ke suatu akun dalam graf berarah."),
        ("Out-degree", "Jumlah relasi keluar dari suatu akun dalam graf berarah."),
    ], columns=["Istilah", "Penjelasan"]), hide_index=True, use_container_width=True)

st.sidebar.divider()
st.sidebar.caption("Final Project · Big Data Visualization")
st.sidebar.caption("Dashboard berbasis output Assignment II")
