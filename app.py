"""
Bali Tourism Intelligence - Dashboard Streamlit
================================================
Membaca hasil pipeline notebook UTS DAM (folder data/processed, data/interim, docs)
dan menampilkannya sebagai dashboard interaktif.

Jalankan:  streamlit run app.py
"""
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Bali Tourism Intelligence", page_icon="🌴", layout="wide")

# ---------------------------------------------------------------- gaya
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem;}
    [data-testid="stMetric"] {background:#f4f7fb; border:1px solid #dbe4ee; border-radius:14px; padding:14px 16px;}
    [data-testid="stMetricLabel"] {color:#5b6b7b;}
    h1, h2, h3 {letter-spacing: -0.3px;}
    </style>
    """,
    unsafe_allow_html=True,
)
WARNA = {"utama": "#1f77b4", "aksen": "#ff7f0e", "hijau": "#2ca02c", "merah": "#d62728"}
NAMA_BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
TEMPLATE = "plotly_white"


def fmt(x):
    """Format angka gaya Indonesia: 1.234.567"""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    return f"{x:,.0f}".replace(",", ".")


# ---------------------------------------------------------------- lokasi data
def cari_base():
    """Cari folder proyek yang berisi data/processed."""
    awal = [Path.cwd(), Path(__file__).resolve().parent]
    kandidat = list(awal)
    for k in awal:
        kandidat += [p for p in k.glob("UTS_*") if p.is_dir()]
    for k in kandidat:
        if (k / "data" / "processed").exists():
            return k
    return Path.cwd()


st.sidebar.title("🌴 Bali Tourism Intelligence")
base_input = st.sidebar.text_input("Folder proyek", value=str(cari_base()),
                                   help="Folder yang berisi data/processed, data/interim, dan docs.")
BASE = Path(base_input)
PROC, INTERIM, DOCS = BASE / "data" / "processed", BASE / "data" / "interim", BASE / "docs"

if not PROC.exists():
    st.error(f"Folder `{PROC}` tidak ditemukan. Isi 'Folder proyek' di sidebar dengan lokasi yang benar.")
    st.stop()


@st.cache_data(show_spinner=False)
def baca_csv(path: str):
    p = Path(path)
    return pd.read_csv(p, encoding="utf-8-sig") if p.exists() else None


def muat(folder: Path, nama: str):
    return baca_csv(str(folder / nama))


# ---------------------------------------------------------------- data
gabung = muat(PROC, "bali_wisnus_cuaca_bulanan.csv")
wisnus = muat(PROC, "wisnus_bulanan_2004_2025.csv")
if wisnus is None and gabung is not None:
    wisnus = gabung[["tahun", "bulan", "kunjungan"]]
wisman_th = muat(PROC, "wisman_tahunan_1969_2025.csv")
wisman_pintu = muat(PROC, "wisman_pintu_masuk_2025.csv")
tpk = muat(PROC, "tpk_hotel_bintang_2025.csv")
kebangsaan = muat(PROC, "wisman_kebangsaan_2019_2024.csv")
t6, t7, t17, t28 = (muat(PROC, f"tabel_{n}_bersih.csv") for n in ("6", "7", "17", "28"))
asosiasi = muat(PROC, "asosiasi_spearman.csv")
cuaca_bln = muat(INTERIM, "cuaca_bulanan.csv")
cuaca_hari = muat(INTERIM, "cuaca_harian.csv")

if wisnus is not None:
    wisnus = wisnus.copy()
    wisnus["tanggal"] = pd.to_datetime(dict(year=wisnus.tahun, month=wisnus.bulan, day=1))


def periode(t):
    return "Pra-pandemi (≤2019)" if t <= 2019 else ("Pandemi-pemulihan (2020-2022)" if t <= 2022 else "Pasca-pemulihan (≥2023)")


def tambah_pandemi(fig, x0="2020-01-01", x1="2022-12-31"):
    fig.add_vrect(x0=x0, x1=x1, fillcolor="grey", opacity=0.15, line_width=0,
                  annotation_text="Pandemi / pemulihan", annotation_position="top left")
    return fig


def butuh(*objek):
    """Hentikan halaman dengan pesan jika ada data yang belum tersedia."""
    if any(o is None for o in objek):
        st.warning("Data untuk halaman ini belum ada di folder proyek. Jalankan notebook sampai selesai dulu.")
        st.stop()


# ---------------------------------------------------------------- fungsi Tabel 17
def tahun_t17(d):
    return sorted({int(m.group(1)) for c in d.columns if (m := re.match(r"^(\d{4})_", str(c)))})


def total_tahun(d, tahun):
    kol = [c for c in d.columns if re.match(rf"^{tahun}_", str(c))]
    if not kol:
        return pd.Series(np.nan, index=d.index)
    return d[kol].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=1)


# ---------------------------------------------------------------- navigasi
HALAMAN = ["🏠 Overview", "📈 Visitor Analytics", "🏝️ Destination Analytics",
           "🌍 Wisatawan Mancanegara", "🌦️ Weather Intelligence", "✅ Data Quality & Provenance"]
halaman = st.sidebar.radio("Menu", HALAMAN)
st.sidebar.markdown("---")
st.sidebar.caption("UTS Data Acquisition & Management · INSTIKI\n\nSumber: Dinas Pariwisata Prov. Bali, BPS Bali, Open-Meteo.")

# =====================================================================
# 1. OVERVIEW
# =====================================================================
if halaman == HALAMAN[0]:
    st.title("🌴 Bali Tourism Intelligence")
    st.caption("Kunjungan wisatawan domestik bulanan × cuaca Bali, 2004-2025 · hasil pipeline akuisisi data")
    butuh(wisnus)

    tahunan = wisnus.groupby("tahun")["kunjungan"].sum()
    th_akhir = int(tahunan.index.max())
    delta = (tahunan.iloc[-1] / tahunan.iloc[-2] - 1) * 100 if len(tahunan) > 1 else None
    rata_bln = wisnus.groupby("bulan")["kunjungan"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Wisnus {th_akhir}", fmt(tahunan.iloc[-1]), f"{delta:+.1f}% vs {th_akhir - 1}" if delta is not None else None)
    c2.metric("Observasi bulanan", fmt(len(wisnus)), f"{int(wisnus.tahun.min())}-{th_akhir}", delta_color="off")
    c3.metric("Tahun puncak", str(int(tahunan.idxmax())), fmt(tahunan.max()), delta_color="off")
    c4.metric("Bulan rata-rata tertinggi", NAMA_BULAN[int(rata_bln.idxmax()) - 1], fmt(rata_bln.max()), delta_color="off")

    c5, c6, c7, c8 = st.columns(4)
    if wisman_th is not None:
        w = wisman_th.dropna(subset=["wisman_bali"]).sort_values("tahun")
        c5.metric(f"Wisman ke Bali {int(w.tahun.iloc[-1])}", fmt(w.wisman_bali.iloc[-1]),
                  f"{w.growth_bali_persen.iloc[-1]:+.1f}%" if pd.notna(w.growth_bali_persen.iloc[-1]) else None)
    if t17 is not None:
        row = t17[t17.jenis_baris == "total_bali"]
        yrs = tahun_t17(t17)
        if not row.empty and yrs:
            tt = {y: total_tahun(row, y).iloc[0] for y in yrs}
            tt = {y: v for y, v in tt.items() if pd.notna(v)}
            ya = max(tt)
            c6.metric(f"Kunjungan ODTW {ya}", fmt(tt[ya]), "objek & daya tarik wisata", delta_color="off")
    if gabung is not None:
        c7.metric("Data cuaca", fmt(len(gabung)) + " bulan", "Open-Meteo · Denpasar", delta_color="off")
    if asosiasi is not None:
        best = asosiasi.loc[asosiasi.rho.abs().idxmax()]
        c8.metric("Asosiasi cuaca terkuat", f"ρ = {best.rho:+.2f}", f"{best.variabel_cuaca}", delta_color="off")

    st.subheader("Tren kunjungan wisatawan domestik")
    fig = px.line(wisnus, x="tanggal", y="kunjungan", template=TEMPLATE, labels={"tanggal": "", "kunjungan": "Kunjungan"})
    fig.update_traces(line_color=WARNA["utama"])
    st.plotly_chart(tambah_pandemi(fig), use_container_width=True)
    st.info("Dashboard ini hanya menampilkan hasil dari berkas yang benar-benar ada di `data/processed`. "
            "Hubungan cuaca-kunjungan bersifat **asosiasi**, bukan sebab-akibat.")

# =====================================================================
# 2. VISITOR ANALYTICS
# =====================================================================
elif halaman == HALAMAN[1]:
    st.title("📈 Visitor Analytics")
    st.caption("Wisatawan domestik bulanan ke Bali (survei Dinas Pariwisata Prov. Bali)")
    butuh(wisnus)

    lo, hi = int(wisnus.tahun.min()), int(wisnus.tahun.max())
    rentang = st.slider("Rentang tahun", lo, hi, (lo, hi))
    d = wisnus[wisnus.tahun.between(*rentang)].copy()
    tahunan = d.groupby("tahun")["kunjungan"].sum().reset_index()
    tahunan["yoy_persen"] = tahunan["kunjungan"].pct_change() * 100

    a, b = st.columns(2)
    with a:
        st.subheader("Tren bulanan")
        fig = px.line(d, x="tanggal", y="kunjungan", template=TEMPLATE, labels={"tanggal": "", "kunjungan": "Kunjungan"})
        fig.update_traces(line_color=WARNA["utama"])
        if rentang[0] <= 2022 and rentang[1] >= 2020:
            tambah_pandemi(fig)
        st.plotly_chart(fig, use_container_width=True)
    with b:
        st.subheader("Total kunjungan per tahun")
        fig = px.bar(tahunan, x="tahun", y="kunjungan", template=TEMPLATE, text_auto=".3s",
                     labels={"tahun": "Tahun", "kunjungan": "Kunjungan"})
        fig.update_traces(marker_color=WARNA["utama"])
        st.plotly_chart(fig, use_container_width=True)

    a, b = st.columns(2)
    with a:
        st.subheader("Pertumbuhan tahunan (YoY)")
        g = tahunan.dropna(subset=["yoy_persen"]).copy()
        g["warna"] = np.where(g.yoy_persen >= 0, "Naik", "Turun")
        fig = px.bar(g, x="tahun", y="yoy_persen", color="warna", template=TEMPLATE,
                     color_discrete_map={"Naik": WARNA["hijau"], "Turun": WARNA["merah"]},
                     labels={"tahun": "Tahun", "yoy_persen": "Pertumbuhan (%)", "warna": ""})
        st.plotly_chart(fig, use_container_width=True)
    with b:
        st.subheader("Perbandingan per periode")
        d["periode_label"] = d["tahun"].map(periode)
        per = d.groupby("periode_label")["kunjungan"].mean().reset_index()
        urut = ["Pra-pandemi (≤2019)", "Pandemi-pemulihan (2020-2022)", "Pasca-pemulihan (≥2023)"]
        per["periode_label"] = pd.Categorical(per["periode_label"], urut, ordered=True)
        fig = px.bar(per.sort_values("periode_label"), x="periode_label", y="kunjungan", template=TEMPLATE,
                     text_auto=".3s", labels={"periode_label": "", "kunjungan": "Rata-rata kunjungan per bulan"})
        fig.update_traces(marker_color=[WARNA["utama"], "#9aa5b1", WARNA["aksen"]][:len(per)])
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Pola musiman")
    st.caption("Indeks musiman = kunjungan bulan ÷ rata-rata bulanan tahun yang sama (menghilangkan tren antar tahun). "
               "2020-2022 dikeluarkan karena terdistorsi pandemi.")
    normal = d[~d.tahun.between(2020, 2022)].copy()
    if normal.empty:
        st.info("Rentang tahun yang dipilih hanya berisi 2020-2022.")
    else:
        normal["indeks_musiman"] = normal["kunjungan"] / normal.groupby("tahun")["kunjungan"].transform("mean")
        pilih = st.multiselect("Tampilkan tahun tertentu (opsional)", sorted(normal.tahun.unique()))
        rerata = normal.groupby("bulan")["indeks_musiman"].mean().reset_index()
        fig = go.Figure()
        for t in pilih:
            x = normal[normal.tahun == t]
            fig.add_trace(go.Scatter(x=[NAMA_BULAN[i - 1] for i in x.bulan], y=x.indeks_musiman, mode="lines",
                                     name=str(t), opacity=0.5))
        fig.add_trace(go.Scatter(x=[NAMA_BULAN[i - 1] for i in rerata.bulan], y=rerata.indeks_musiman, mode="lines+markers",
                                 name="Rata-rata", line=dict(color=WARNA["aksen"], width=4)))
        fig.add_hline(y=1, line_dash="dot", line_color="grey")
        fig.update_layout(template=TEMPLATE, yaxis_title="Indeks musiman (1 = rata-rata tahun)")
        st.plotly_chart(fig, use_container_width=True)
        tinggi, rendah = rerata.loc[rerata.indeks_musiman.idxmax()], rerata.loc[rerata.indeks_musiman.idxmin()]
        c1, c2 = st.columns(2)
        c1.metric("Bulan tertinggi (rata-rata)", NAMA_BULAN[int(tinggi.bulan) - 1], f"indeks {tinggi.indeks_musiman:.2f}", delta_color="off")
        c2.metric("Bulan terendah (rata-rata)", NAMA_BULAN[int(rendah.bulan) - 1], f"indeks {rendah.indeks_musiman:.2f}", delta_color="off")

    with st.expander("Lihat data tabel"):
        st.dataframe(d[["tahun", "bulan", "kunjungan"]], use_container_width=True, hide_index=True)

# =====================================================================
# 3. DESTINATION ANALYTICS
# =====================================================================
elif halaman == HALAMAN[2]:
    st.title("🏝️ Destination Analytics")
    st.caption("Kunjungan ke obyek & daya tarik wisata (ODTW) per kabupaten/kota (Tabel 17). "
               "Hanya ODTW yang tercatat; 2016-2017 tidak dipisah wisnus/wisman.")
    butuh(t17)

    t = t17.copy()
    tahun_opsi = tahun_t17(t)
    for y in tahun_opsi:
        t[f"total_{y}"] = total_tahun(t, y)
    c1, c2 = st.columns(2)
    tahun_pilih = c1.selectbox("Tahun", sorted(tahun_opsi, reverse=True), index=0)
    top_n = c2.slider("Jumlah objek di Top N", 5, 20, 10)
    kol = f"total_{tahun_pilih}"

    objek = t[(t.jenis_baris == "objek") & t[kol].notna() & (t[kol] > 0)].sort_values(kol, ascending=False).reset_index(drop=True)
    if objek.empty:
        st.warning(f"Tidak ada data objek wisata untuk {tahun_pilih}. Coba tahun lain.")
        st.stop()
    objek["kabupaten_kota"] = objek["kabupaten_kota"].astype(str).str.title()

    top = objek.head(top_n)
    c1, c2, c3 = st.columns(3)
    c1.metric("Objek terpopuler", top.objek_wisata.iloc[0], f"{fmt(top[kol].iloc[0])} kunjungan", delta_color="off")
    c2.metric("Total kunjungan seluruh objek", fmt(objek[kol].sum()))
    c3.metric("Jumlah objek tercatat", fmt(len(objek)))

    st.subheader(f"TOP {top_n} objek wisata, {tahun_pilih}")
    kw, kn = f"{tahun_pilih}_wisman", f"{tahun_pilih}_wisnus"
    plot = top.iloc[::-1].copy()
    plot["label"] = plot["objek_wisata"] + " (" + plot["kabupaten_kota"] + ")"
    if kw in t.columns and kn in t.columns:
        fig = go.Figure()
        fig.add_bar(y=plot.label, x=pd.to_numeric(plot[kn], errors="coerce"), name="Wisnus", orientation="h", marker_color=WARNA["utama"])
        fig.add_bar(y=plot.label, x=pd.to_numeric(plot[kw], errors="coerce"), name="Wisman", orientation="h", marker_color=WARNA["aksen"])
        fig.update_layout(barmode="stack", template=TEMPLATE, height=520, xaxis_title="Kunjungan", yaxis_title="")
    else:
        fig = px.bar(plot, y="label", x=kol, orientation="h", template=TEMPLATE, text_auto=".3s",
                     labels={"label": "", kol: "Kunjungan"}, height=520)
        fig.update_traces(marker_color=WARNA["utama"])
    st.plotly_chart(fig, use_container_width=True)

    a, b = st.columns([3, 2])
    with a:
        st.subheader("Peringkat objek wisata")
        rank = pd.DataFrame({"Peringkat": np.arange(1, len(objek) + 1), "Objek Wisata": objek.objek_wisata,
                             "Kabupaten/Kota": objek.kabupaten_kota, f"Kunjungan {tahun_pilih}": objek[kol].astype(int),
                             "Pangsa (%)": (objek[kol] / objek[kol].sum() * 100).round(2)})
        cari = st.text_input("Cari objek wisata")
        if cari:
            rank = rank[rank["Objek Wisata"].str.contains(cari, case=False, na=False)]
        st.dataframe(rank, use_container_width=True, hide_index=True, height=420,
                     column_config={f"Kunjungan {tahun_pilih}": st.column_config.ProgressColumn(
                         format="%d", min_value=0, max_value=int(objek[kol].max()))})
        st.download_button("⬇️ Unduh peringkat (CSV)", rank.to_csv(index=False).encode("utf-8-sig"),
                           f"peringkat_objek_wisata_{tahun_pilih}.csv", "text/csv")
    with b:
        st.subheader("Per kabupaten/kota")
        kab = t[t.jenis_baris == "subtotal_kabupaten"].copy()
        kab["kabupaten_kota"] = kab["kabupaten_kota"].astype(str).str.title()
        kab = kab.groupby("kabupaten_kota", as_index=False)[kol].sum().sort_values(kol)
        fig = px.bar(kab, y="kabupaten_kota", x=kol, orientation="h", template=TEMPLATE, text_auto=".3s",
                     labels={"kabupaten_kota": "", kol: "Kunjungan"})
        fig.update_traces(marker_color=WARNA["utama"])
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Tren total ODTW")
    tot = t[t.jenis_baris == "total_bali"]
    if not tot.empty:
        tren = pd.DataFrame({"tahun": tahun_opsi, "kunjungan": [total_tahun(tot, y).iloc[0] for y in tahun_opsi]}).dropna()
        fig = px.line(tren, x="tahun", y="kunjungan", markers=True, template=TEMPLATE, labels={"tahun": "Tahun", "kunjungan": "Kunjungan"})
        fig.update_traces(line_color=WARNA["utama"])
        st.plotly_chart(fig, use_container_width=True)

    scrape = muat(INTERIM, "scrape_daya_tarik_wisata.csv")
    if scrape is not None and len(scrape):
        with st.expander(f"Hasil web scraping Disparda Bali ({len(scrape)} listing)"):
            st.dataframe(scrape, use_container_width=True, hide_index=True)

# =====================================================================
# 4. WISATAWAN MANCANEGARA
# =====================================================================
elif halaman == HALAMAN[3]:
    st.title("🌍 Wisatawan Mancanegara")
    st.caption("Kedatangan wisman langsung ke Bali (BPS Provinsi Bali & Buku Statistik Pariwisata Bali 2025)")

    tabs = st.tabs(["Tren tahunan", "Pintu masuk 2025", "Negara asal", "TPK hotel 2025"])

    with tabs[0]:
        butuh(wisman_th)
        skala = st.radio("Skala sumbu Y", ["Linear", "Log"], horizontal=True)
        fig = go.Figure()
        fig.add_scatter(x=wisman_th.tahun, y=wisman_th.wisman_bali, name="Bali", line=dict(color=WARNA["utama"], width=3))
        fig.add_scatter(x=wisman_th.tahun, y=wisman_th.wisman_indonesia, name="Indonesia", line=dict(color=WARNA["aksen"], width=2))
        fig.update_layout(template=TEMPLATE, yaxis_title="Wisman (orang)", yaxis_type="log" if skala == "Log" else "linear")
        st.plotly_chart(fig, use_container_width=True)
        w = wisman_th.dropna(subset=["wisman_bali", "wisman_indonesia"]).copy()
        w["pangsa_bali_persen"] = w.wisman_bali / w.wisman_indonesia * 100
        fig = px.area(w, x="tahun", y="pangsa_bali_persen", template=TEMPLATE,
                      labels={"tahun": "Tahun", "pangsa_bali_persen": "Pangsa Bali terhadap Indonesia (%)"})
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        butuh(wisman_pintu)
        d = wisman_pintu.copy()
        d["bulan_nama"] = d.bulan.map(lambda i: NAMA_BULAN[int(i) - 1])
        fig = px.bar(d, x="bulan_nama", y="kunjungan", color="pintu_masuk", barmode="stack", template=TEMPLATE,
                     category_orders={"bulan_nama": NAMA_BULAN}, labels={"bulan_nama": "", "kunjungan": "Wisman", "pintu_masuk": "Pintu masuk"})
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Selisih antara jumlah per pintu dan baris Jumlah di berkas sumber dicatat apa adanya (lihat halaman Data Quality).")

    with tabs[2]:
        sub = st.radio("Sumber", ["Tabel 6: 20 negara pasar utama 2024 vs 2025", "Kebangsaan 2019-2024"], horizontal=True)
        if sub.startswith("Tabel 6"):
            butuh(t6)
            n = t6[t6.jenis_baris == "negara"].sort_values("kunjungan_2025", ascending=False)
            m = n.melt(id_vars="negara", value_vars=["kunjungan_2024", "kunjungan_2025"], var_name="tahun", value_name="kunjungan")
            m["tahun"] = m.tahun.str[-4:]
            fig = px.bar(m, y="negara", x="kunjungan", color="tahun", barmode="group", orientation="h", template=TEMPLATE,
                         height=700, category_orders={"negara": n.negara.tolist()[::-1]},
                         color_discrete_map={"2024": "#9aa5b1", "2025": WARNA["utama"]}, labels={"negara": "", "kunjungan": "Kedatangan"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            butuh(kebangsaan)
            th = st.selectbox("Tahun", sorted(kebangsaan.tahun.unique(), reverse=True))
            n = kebangsaan[(kebangsaan.jenis_baris == "negara") & (kebangsaan.tahun == th)].dropna(subset=["kunjungan"])
            n = n[n.kunjungan > 0].sort_values("kunjungan", ascending=False).head(15).iloc[::-1]
            if n.empty:
                st.info("Tidak ada rincian negara untuk tahun ini (di sumber 2021 hanya memuat total).")
            else:
                fig = px.bar(n, y="negara", x="kunjungan", color="kelompok", orientation="h", template=TEMPLATE, height=520,
                             labels={"negara": "", "kunjungan": "Kedatangan", "kelompok": "Kelompok"})
                st.plotly_chart(fig, use_container_width=True)

    with tabs[3]:
        butuh(tpk)
        d = tpk.copy()
        d["bulan_nama"] = d.bulan.map(lambda i: NAMA_BULAN[int(i) - 1])
        fig = px.line(d, x="bulan_nama", y="tpk_persen", color="kelas_hotel", markers=True, template=TEMPLATE,
                      category_orders={"bulan_nama": NAMA_BULAN}, labels={"bulan_nama": "", "tpk_persen": "TPK (%)", "kelas_hotel": "Kelas hotel"})
        st.plotly_chart(fig, use_container_width=True)

# =====================================================================
# 5. WEATHER INTELLIGENCE
# =====================================================================
elif halaman == HALAMAN[4]:
    st.title("🌦️ Weather Intelligence")
    st.caption("Cuaca historis Denpasar (Open-Meteo, CC BY 4.0) dibandingkan dengan kunjungan wisatawan domestik. "
               "Satu titik lokasi; hasil = asosiasi, bukan sebab-akibat.")
    butuh(gabung)
    g = gabung.copy()
    g["tanggal"] = pd.to_datetime(dict(year=g.tahun, month=g.bulan, day=1))

    tabs = st.tabs(["Suhu & curah hujan", "Hubungan cuaca-kunjungan", "Korelasi Spearman"])

    with tabs[0]:
        a, b = st.columns(2)
        with a:
            fig = px.line(g, x="tanggal", y="suhu_rata2_c", template=TEMPLATE, labels={"tanggal": "", "suhu_rata2_c": "Suhu rata-rata (°C)"})
            fig.update_traces(line_color=WARNA["merah"])
            st.plotly_chart(fig.update_layout(title="Suhu rata-rata bulanan"), use_container_width=True)
        with b:
            fig = px.bar(g, x="tanggal", y="curah_hujan_total_mm", template=TEMPLATE, labels={"tanggal": "", "curah_hujan_total_mm": "Curah hujan (mm)"})
            fig.update_traces(marker_color=WARNA["utama"])
            st.plotly_chart(fig.update_layout(title="Curah hujan bulanan"), use_container_width=True)
        klim = g.groupby("bulan").agg(suhu=("suhu_rata2_c", "mean"), hujan=("curah_hujan_total_mm", "mean")).reset_index()
        fig = go.Figure()
        fig.add_bar(x=[NAMA_BULAN[i - 1] for i in klim.bulan], y=klim.hujan, name="Hujan rata-rata (mm)", marker_color=WARNA["utama"], opacity=0.7)
        fig.add_scatter(x=[NAMA_BULAN[i - 1] for i in klim.bulan], y=klim.suhu, name="Suhu rata-rata (°C)", yaxis="y2",
                        line=dict(color=WARNA["merah"], width=3))
        fig.update_layout(template=TEMPLATE, title="Klimatologi bulanan Denpasar (2004-2025)", yaxis_title="Hujan (mm)",
                          yaxis2=dict(title="Suhu (°C)", overlaying="y", side="right"))
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        c1, c2, c3 = st.columns(3)
        var = c1.selectbox("Variabel cuaca (sumbu X)", ["curah_hujan_total_mm", "hari_hujan", "suhu_rata2_c", "angin_maks_kmh"])
        y = c2.selectbox("Ukuran kunjungan (sumbu Y)", ["indeks_musiman", "kunjungan"])
        normal_saja = c3.checkbox("Hanya tahun normal (tanpa 2020-2022)", value=True)
        d = g[g.periode_normal] if (normal_saja and "periode_normal" in g.columns) else g
        fig = px.scatter(d, x=var, y=y, color="periode", template=TEMPLATE, hover_data=["tahun", "bulan"], opacity=0.75)
        if len(d) > 2:
            k = np.polyfit(d[var], d[y], 1)
            xs = np.linspace(d[var].min(), d[var].max(), 50)
            fig.add_scatter(x=xs, y=k[0] * xs + k[1], mode="lines", name="Garis tren", line=dict(color="black", dash="dash"))
            rho = d[[var, y]].corr(method="spearman").iloc[0, 1]
            st.metric("Korelasi Spearman (ρ)", f"{rho:+.3f}", f"n = {len(d)}", delta_color="off")
        st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        skenario = st.radio("Skenario", ["Semua bulan", "Tahun normal (tanpa 2020-2022)"], horizontal=True)
        d = g if skenario == "Semua bulan" else g[g.periode_normal]
        kolom = [c for c in ["kunjungan", "indeks_musiman", "suhu_rata2_c", "curah_hujan_total_mm", "hari_hujan", "angin_maks_kmh"] if c in d.columns]
        kor = d[kolom].corr(method="spearman")
        fig = px.imshow(kor, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r", template=TEMPLATE, aspect="auto")
        st.plotly_chart(fig, use_container_width=True)
        if asosiasi is not None:
            st.subheader("Hasil analisis di notebook (Spearman + p-value)")
            st.dataframe(asosiasi, use_container_width=True, hide_index=True)
        st.caption("Skenario C di notebook (tahun normal, indeks musiman) paling bersih dari tren tahunan dan efek pandemi. "
                   "Korelasi tidak membuktikan bahwa cuaca menyebabkan perubahan kunjungan.")

# =====================================================================
# 6. DATA QUALITY & PROVENANCE
# =====================================================================
else:
    st.title("✅ Data Quality & Provenance")
    st.caption("Bukti bahwa hasil akuisisi dapat dipertanggungjawabkan: validasi, asal-usul berkas, dan etika data.")

    tabs = st.tabs(["Kualitas & validasi", "Provenance", "Data Ethics Checklist", "Katalog dataset"])

    with tabs[0]:
        vt = muat(PROC, "validasi_tabel_terpilih.csv")
        vk = muat(PROC, "validasi_khusus_tabel.csv")
        vs = muat(PROC, "validasi_silang_wisman.csv")
        vw = muat(PROC, "wisnus_validasi_total_growth.csv")

        if vt is not None:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tabel diproses", len(vt))
            c2.metric("Total baris bersih", fmt(vt.jumlah_baris.sum()))
            c3.metric("Missing value (total)", fmt(vt.missing_value.sum()))
            c4.metric("Baris duplikat", fmt(vt.baris_duplikat.sum()))
            st.subheader("Status validasi tiap tabel")
            st.dataframe(vt, use_container_width=True, hide_index=True)
            fig = px.bar(vt, x="nomor_tabel", y="missing_value", template=TEMPLATE, text_auto=True,
                         labels={"nomor_tabel": "Tabel", "missing_value": "Jumlah missing value"})
            fig.update_traces(marker_color=WARNA["aksen"])
            st.plotly_chart(fig, use_container_width=True)
        if vw is not None:
            st.subheader("Dataset utama: jumlah 12 bulan vs total BALI di sumber")
            if {"jumlah_12_bulan", "total_di_sheet"}.issubset(vw.columns):
                xcol = vw.columns[0]
                fig = go.Figure()
                fig.add_bar(x=vw[xcol], y=vw.jumlah_12_bulan, name="Jumlah 12 bulan (hitung)", marker_color=WARNA["utama"])
                fig.add_scatter(x=vw[xcol], y=vw.total_di_sheet, name="Total di sumber", mode="markers",
                                marker=dict(color=WARNA["aksen"], size=9, symbol="diamond"))
                fig.update_layout(template=TEMPLATE, xaxis_title="Tahun", yaxis_title="Kunjungan")
                st.plotly_chart(fig, use_container_width=True)
                if "total_sesuai" in vw.columns:
                    st.success(f"{int(vw.total_sesuai.sum())} dari {len(vw)} tahun: jumlah 12 bulan = total di sumber.")
            with st.expander("Tabel validasi total & growth"):
                st.dataframe(vw, use_container_width=True, hide_index=True)
        if vs is not None:
            with st.expander("Validasi silang wisman antar-sumber"):
                st.dataframe(vs, use_container_width=True, hide_index=True)
        if vk is not None:
            with st.expander("Pemeriksaan khusus per tabel"):
                st.dataframe(vk, use_container_width=True, hide_index=True)
        if all(x is None for x in (vt, vk, vs, vw)):
            st.warning("Berkas validasi belum ditemukan di data/processed.")

    with tabs[1]:
        prov_path = DOCS / "provenance.json"
        if not prov_path.exists():
            st.warning("docs/provenance.json belum ada.")
        else:
            prov = pd.DataFrame(json.loads(prov_path.read_text(encoding="utf-8")))
            c1, c2, c3 = st.columns(3)
            c1.metric("Jumlah sumber tercatat", len(prov))
            c2.metric("Total ukuran", f"{prov.ukuran_bytes.sum() / 1024 ** 2:.2f} MB")
            c3.metric("Metode akuisisi", prov.metode_akuisisi.nunique())
            fig = px.pie(prov, names="metode_akuisisi", template=TEMPLATE, hole=0.5, title="Metode akuisisi")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(prov[["nama_sumber", "metode_akuisisi", "waktu_akses_utc", "lisensi", "ukuran_bytes", "md5"]],
                         use_container_width=True, hide_index=True)

            if st.button("🔍 Verifikasi MD5 berkas mentah"):
                hasil = []
                for _, r in prov.iterrows():
                    p = BASE / r["file_lokal"]
                    if p.exists():
                        h = hashlib.md5(p.read_bytes()).hexdigest()
                        hasil.append({"sumber": r["nama_sumber"], "status": "OK" if h == r["md5"] else "BERUBAH"})
                    else:
                        hasil.append({"sumber": r["nama_sumber"], "status": "BERKAS TIDAK ADA"})
                hasil = pd.DataFrame(hasil)
                if (hasil.status == "OK").all():
                    st.success("Semua berkas mentah utuh (MD5 sama dengan catatan provenance).")
                else:
                    st.error("Ada berkas yang berubah atau tidak ditemukan.")
                st.dataframe(hasil, use_container_width=True, hide_index=True)

    with tabs[2]:
        cek = muat(DOCS, "data_ethics_checklist.csv")
        if cek is None:
            st.warning("docs/data_ethics_checklist.csv belum ada.")
        else:
            selesai = int((cek.status == "Selesai").sum())
            st.progress(selesai / len(cek), text=f"{selesai} dari {len(cek)} butir berstatus Selesai")
            for r in cek.itertuples():
                ikon = "✅" if r.status == "Selesai" else "🟡"
                with st.expander(f"{ikon} {r.no}. {r.butir} · {r.status}"):
                    st.write(r.bukti)

    with tabs[3]:
        kat = muat(DOCS, "identifikasi_gabungan_tabel.csv")
        if kat is not None:
            st.dataframe(kat.drop(columns=["nama_kolom"], errors="ignore"), use_container_width=True, hide_index=True)
        kam = muat(DOCS, "data_dictionary_gabungan.csv")
        if kam is not None:
            with st.expander("Data dictionary"):
                st.dataframe(kam, use_container_width=True, hide_index=True)
