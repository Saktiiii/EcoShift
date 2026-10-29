import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

from scheduler import buat_jadwal, fmt_jam

st.set_page_config(page_title="EcoShift | Smart Energy", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# Memuat CSS dari file terpisah supaya tampilan tidak bercampur dengan logika program.
with open("style.css", encoding="utf-8") as file:
    css = file.read()

st.markdown(
    f"<style>{css}</style>",
    unsafe_allow_html=True
)

# ---------- DATA ----------
data_awal = pd.DataFrame({
    "Nama Mesin": ["Mesin Potong", "Mesin Jahit", "Mesin Obras"],
    "Daya (Watt)": [1000, 500, 750],
    "Durasi (Jam)": [2.0, 4.0, 2.0]
})
if "data_mesin" not in st.session_state:
    st.session_state.data_mesin = data_awal.copy()
if "batas_daya" not in st.session_state:
    st.session_state.batas_daya = 2000

# Fungsi penjadwalan dipisahkan ke scheduler.py agar lebih mudah dipelajari.
# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("""<div style="padding:12px 0 25px"><div style="font-size:35px">⚡</div><div style="font-size:25px;font-weight:800">EcoShift</div><div style="font-size:11px;color:#A7F3D0">SMART ENERGY MANAGEMENT</div></div>""", unsafe_allow_html=True)
    st.markdown("---")
    halaman = st.radio("NAVIGASI", ["Dashboard", "Manajemen Mesin", "Rekomendasi Jadwal"])
    st.markdown("---")
    st.markdown("### ⚙️ Pengaturan")
    st.session_state.batas_daya = st.number_input("Batas daya operasional (Watt)", min_value=100, max_value=100000, value=int(st.session_state.batas_daya), step=100)
    st.caption("Atur kapasitas daya maksimum yang tersedia untuk seluruh mesin.")
    st.markdown("---")
    st.markdown("<div style='font-size:11px;color:#A7F3D0'>ECOSHIFT v1.1<br>Smart Energy Scheduling</div>", unsafe_allow_html=True)

# ---------- COMMON VALUES ----------
df = st.session_state.data_mesin.copy()
batas_daya = int(st.session_state.batas_daya)
total_daya = int(df["Daya (Watt)"].sum()) if not df.empty else 0
total_energi = float((df["Daya (Watt)"] * df["Durasi (Jam)"]).sum() / 1000) if not df.empty else 0
jumlah_mesin = len(df)
persentase_daya = total_daya / batas_daya * 100 if batas_daya else 0
sisa_daya = batas_daya - total_daya

st.markdown("""<div class="hero"><div style="font-size:12px;letter-spacing:2px;color:#A7F3D0;font-weight:700">SMART ENERGY MANAGEMENT PLATFORM</div><h1>Energy Overview ⚡</h1><p>Pantau penggunaan daya, kelola mesin produksi, dan dapatkan rekomendasi jadwal operasional otomatis.</p></div>""", unsafe_allow_html=True)

# ---------- DASHBOARD ----------
if halaman == "Dashboard":
    st.markdown('<div class="section-title">Ringkasan Operasional</div><div class="section-caption">Informasi utama penggunaan energi berdasarkan data mesin.</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Mesin", f"{jumlah_mesin} Unit")
    c2.metric("Total Daya Terpasang", f"{total_daya:,} W", delta=f"{persentase_daya:.1f}% kapasitas", delta_color="inverse")
    c3.metric("Estimasi Energi", f"{total_energi:.2f} kWh")
    c4.metric("Sisa Kapasitas", f"{sisa_daya:,} W", delta="Tersedia" if sisa_daya >= 0 else "Melebihi batas", delta_color="normal" if sisa_daya >= 0 else "inverse")
    st.markdown('<div class="section-title">Status Kapasitas Listrik</div>', unsafe_allow_html=True)
    if total_daya <= batas_daya:
        st.success(f"Kapasitas total daya terpasang masih dalam batas: {total_daya:,} W dari {batas_daya:,} W.")
    else:
        st.warning(f"Jika seluruh mesin menyala bersamaan, kebutuhan {total_daya:,} W melebihi batas {batas_daya:,} W. Gunakan Rekomendasi Jadwal untuk menyusun waktu operasi.")
    st.progress(min(persentase_daya / 100, 1.0))
    st.caption(f"Pemakaian daya jika semua mesin aktif: {persentase_daya:.1f}%")
    left, right = st.columns([1.5, 1])
    with left:
        st.markdown("### Daya per Mesin")
        if not df.empty:
            fig = px.bar(df, x="Nama Mesin", y="Daya (Watt)", color="Nama Mesin", text="Daya (Watt)", color_discrete_sequence=["#1F7A55", "#39A878", "#91D5B5", "#F4B860"], template="plotly_white")
            fig.update_traces(textposition="outside")
            fig.update_layout(showlegend=False, height=340, margin=dict(l=10,r=10,t=20,b=10), xaxis_title="", yaxis_title="Daya (Watt)")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Belum ada data mesin.")
    with right:
        st.markdown("### Distribusi Daya")
        if not df.empty and total_daya > 0:
            fig = px.pie(df, names="Nama Mesin", values="Daya (Watt)", hole=.65, color_discrete_sequence=["#1F7A55", "#39A878", "#91D5B5", "#F4B860"])
            fig.update_layout(height=340, margin=dict(l=5,r=5,t=20,b=10), legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Data daya belum tersedia.")
    st.markdown("### Ringkasan Mesin")
    if not df.empty:
        ringkasan = df.copy()
        ringkasan["Energi (kWh)"] = (ringkasan["Daya (Watt)"] * ringkasan["Durasi (Jam)"] / 1000).round(2)
        st.dataframe(ringkasan, use_container_width=True, hide_index=True)

# ---------- CRUD MESIN ----------
elif halaman == "Manajemen Mesin":
    st.markdown('<div class="section-title">Manajemen Mesin</div><div class="section-caption">Tambah, lihat, ubah, dan hapus mesin produksi.</div>', unsafe_allow_html=True)
    with st.expander("➕ Tambahkan Mesin Baru", expanded=True):
        with st.form("form_tambah_mesin", clear_on_submit=True):
            nama = st.text_input("Nama mesin", placeholder="Contoh: Mesin Press")
            a, b = st.columns(2)
            daya = a.number_input("Daya mesin (Watt)", min_value=1, max_value=100000, value=500, step=50)
            durasi = b.number_input("Durasi operasional (jam)", min_value=0.5, max_value=24.0, value=2.0, step=0.5)
            tambah = st.form_submit_button("Tambahkan Mesin", use_container_width=True, type="primary")
            if tambah:
                if not nama.strip(): st.error("Nama mesin tidak boleh kosong.")
                elif nama.strip().casefold() in st.session_state.data_mesin["Nama Mesin"].str.casefold().tolist(): st.error("Nama mesin sudah terdaftar.")
                else:
                    st.session_state.data_mesin = pd.concat([st.session_state.data_mesin, pd.DataFrame([{"Nama Mesin":nama.strip(),"Daya (Watt)":int(daya),"Durasi (Jam)":float(durasi)}])], ignore_index=True)
                    st.success("Mesin berhasil ditambahkan."); st.rerun()
    df = st.session_state.data_mesin.copy()
    st.markdown("### Daftar Mesin Terdaftar")
    search = st.text_input("🔎 Cari mesin", placeholder="Ketik nama mesin...")
    shown = df[df["Nama Mesin"].str.contains(search, case=False, na=False)] if search else df
    st.dataframe(shown, use_container_width=True, hide_index=True)
    if not df.empty:
        st.markdown("### Edit atau Hapus Mesin")
        pilihan = st.selectbox("Pilih mesin", df["Nama Mesin"].tolist())
        item = df[df["Nama Mesin"] == pilihan].iloc[0]
        edit_col, delete_col = st.columns([2,1])
        with edit_col:
            with st.form("form_edit_mesin"):
                nama_edit = st.text_input("Nama mesin", value=str(item["Nama Mesin"]))
                daya_edit = st.number_input("Daya (Watt)", min_value=1, max_value=100000, value=int(item["Daya (Watt)"]), step=50)
                durasi_edit = st.number_input("Durasi (Jam)", min_value=0.5, max_value=24.0, value=float(item["Durasi (Jam)"]), step=0.5)
                simpan = st.form_submit_button("💾 Simpan Perubahan", use_container_width=True, type="primary")
                if simpan:
                    nama_lain = df[df["Nama Mesin"] != pilihan]["Nama Mesin"].str.casefold().tolist()
                    if not nama_edit.strip(): st.error("Nama mesin tidak boleh kosong.")
                    elif nama_edit.strip().casefold() in nama_lain: st.error("Nama mesin tersebut sudah digunakan.")
                    else:
                        idx = st.session_state.data_mesin.index[st.session_state.data_mesin["Nama Mesin"] == pilihan][0]
                        st.session_state.data_mesin.loc[idx, ["Nama Mesin", "Daya (Watt)", "Durasi (Jam)"]] = [nama_edit.strip(), int(daya_edit), float(durasi_edit)]
                        st.success("Data mesin berhasil diperbarui."); st.rerun()
        with delete_col:
            st.markdown("#### Hapus Data")
            st.warning(f"Mesin terpilih: {pilihan}")
            konfirmasi = st.checkbox("Saya yakin ingin menghapus mesin ini.")
            if st.button("🗑️ Hapus Mesin", use_container_width=True):
                if konfirmasi:
                    st.session_state.data_mesin = st.session_state.data_mesin[st.session_state.data_mesin["Nama Mesin"] != pilihan].reset_index(drop=True)
                    st.success("Mesin berhasil dihapus."); st.rerun()
                else: st.error("Centang konfirmasi terlebih dahulu.")
    csv = st.session_state.data_mesin.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Download Data Mesin (CSV)", csv, "data_mesin_ecoshift.csv", "text/csv", use_container_width=True)

# ---------- REKOMENDASI JADWAL ----------
elif halaman == "Rekomendasi Jadwal":
    st.markdown('<div class="section-title">Rekomendasi Jadwal Operasional</div><div class="section-caption">Susun jadwal otomatis agar mesin menyelesaikan durasinya tanpa melampaui batas daya yang tersedia.</div>', unsafe_allow_html=True)
    if df.empty:
        st.warning("Belum ada mesin. Tambahkan mesin terlebih dahulu di halaman Manajemen Mesin.")
    else:
        top1, top2, top3 = st.columns(3)
        top1.metric("Mesin yang Dijadwalkan", f"{len(df)} unit")
        top2.metric("Batas Daya", f"{batas_daya:,} W")
        top3.metric("Total Daya Jika Bersamaan", f"{total_daya:,} W", delta="Melebihi batas" if total_daya > batas_daya else "Dalam batas", delta_color="inverse" if total_daya > batas_daya else "normal")
        st.markdown("### Atur Jam Operasional")
        with st.form("form_jadwal"):
            a, b, c = st.columns(3)
            jam_mulai = a.time_input("Jam mulai kerja", value=datetime.strptime("08:00", "%H:%M").time(), step=1800)
            jam_selesai = b.time_input("Batas akhir kerja", value=datetime.strptime("16:00", "%H:%M").time(), step=1800)
            slot = c.selectbox("Ketelitian jadwal", [15, 30, 60], index=1, format_func=lambda x: f"{x} menit")
            st.caption("Setiap mesin dijadwalkan dalam satu blok waktu kontinu. Durasi dibulatkan ke ATAS sesuai slot yang dipilih agar pekerjaan tidak dijadwalkan terlalu singkat.")
            generate = st.form_submit_button("⚡ Buat Rekomendasi Jadwal", type="primary", use_container_width=True)
        if generate:
            # Hapus hasil lama agar tidak tertukar dengan hasil perhitungan terbaru.
            st.session_state.pop("hasil_jadwal", None)
            st.session_state.pop("pesan_jadwal", None)

            with st.spinner("Menghitung jadwal optimal..."):
                hasil, pesan = buat_jadwal(df, batas_daya, jam_mulai, jam_selesai, slot)

            if hasil is None:
                st.error(pesan)
            else:
                st.session_state.hasil_jadwal = hasil
                st.session_state.pesan_jadwal = pesan

        # Ditampilkan di luar `if generate` supaya hasil tidak hilang saat halaman rerun.
        if "hasil_jadwal" in st.session_state:
            hasil = st.session_state.hasil_jadwal
            st.success(st.session_state.pesan_jadwal)

            st.markdown("### Jadwal Operasional")
            st.dataframe(
                hasil[["Nama Mesin", "Mulai", "Selesai", "Daya (Watt)", "Durasi (Jam)"]],
                use_container_width=True,
                hide_index=True,
            )

            # Gantt chart
            base = datetime.combine(datetime.today().date(), datetime.min.time())
            gantt = hasil.copy()
            gantt["Start"] = [base + timedelta(minutes=int(m)) for m in gantt["Mulai (menit)"]]
            gantt["Finish"] = [base + timedelta(minutes=int(m)) for m in gantt["Selesai (menit)"]]

            st.markdown("### Timeline Mesin")
            fig = px.timeline(
                gantt, x_start="Start", x_end="Finish", y="Nama Mesin", color="Nama Mesin",
                color_discrete_sequence=["#1F7A55", "#39A878", "#91D5B5", "#F4B860"],
                template="plotly_white",
            )
            fig.update_yaxes(autorange="reversed", title="")
            fig.update_xaxes(title="", tickformat="%H:%M")
            fig.update_layout(showlegend=False, height=320, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)

            # Cek beban puncak
            puncak = 0
            for t in sorted(set(hasil["Mulai (menit)"])):
                aktif = hasil[(hasil["Mulai (menit)"] <= t) & (hasil["Selesai (menit)"] > t)]
                puncak = max(puncak, int(aktif["Daya (Watt)"].sum()))
            st.caption(f"Beban puncak pada jadwal ini: {puncak:,} W dari batas {batas_daya:,} W.")