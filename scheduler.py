"""Logika rekomendasi jadwal mesin EcoShift.

File ini berisi fungsi yang menghitung jadwal; tampilan Streamlit ada di app.py.
"""
import math
from datetime import time

import pandas as pd


def fmt_jam(total_menit):
    """Ubah jumlah menit sejak tengah malam menjadi teks HH:MM."""
    total_menit = int(total_menit) % (24 * 60)
    jam = total_menit // 60
    menit = total_menit % 60
    return f"{jam:02d}:{menit:02d}"


def buat_jadwal(df_mesin, batas_watt, jam_mulai, jam_selesai, slot_menit=30):
    """Buat jadwal mesin tanpa melampaui batas daya.

    Setiap mesin dijadwalkan dalam satu blok waktu kontinu. OR-Tools mencari
    jadwal dengan waktu selesai keseluruhan secepat mungkin.
    """
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return None, "OR-Tools belum terpasang. Jalankan: python -m pip install ortools"

    if df_mesin.empty:
        return pd.DataFrame(), "Belum ada mesin. Tambahkan mesin terlebih dahulu."

    if batas_watt <= 0:
        return None, "Batas daya harus lebih besar dari 0 watt."

    # Ubah waktu menjadi menit agar mudah dihitung.
    menit_mulai = jam_mulai.hour * 60 + jam_mulai.minute
    menit_selesai = jam_selesai.hour * 60 + jam_selesai.minute
    if menit_selesai <= menit_mulai:
        return None, "Jam selesai harus setelah jam mulai dan dalam hari yang sama."

    total_menit = menit_selesai - menit_mulai
    # Jangan diam-diam memangkas jam operasional ketika tidak pas dengan slot.
    if total_menit % slot_menit != 0:
        return None, f"Rentang jam operasional harus kelipatan {slot_menit} menit. Ubah jam mulai/selesai atau pilih slot lain."

    jumlah_slot = total_menit // slot_menit
    if jumlah_slot <= 0:
        return None, "Rentang jam operasional terlalu pendek."

    model = cp_model.CpModel()
    daftar_mulai = []
    daftar_selesai = []
    interval_mesin = []
    kebutuhan_daya = []
    durasi_slot = []
    data = df_mesin.reset_index(drop=True)

    for indeks, mesin in data.iterrows():
        daya = int(mesin["Daya (Watt)"])
        if daya > batas_watt:
            return None, f"{mesin['Nama Mesin']} membutuhkan {daya:,} W, melebihi batas daya {batas_watt:,} W. Mesin ini tidak bisa dijadwalkan."

        # Bulatkan durasi ke atas agar durasi jadwal tidak kurang dari kebutuhan.
        durasi = max(1, math.ceil(float(mesin["Durasi (Jam)"]) * 60 / slot_menit))
        if durasi > jumlah_slot:
            return None, f"Durasi {mesin['Nama Mesin']} lebih panjang daripada jam operasional."

        mulai = model.NewIntVar(0, jumlah_slot - durasi, f"mulai_{indeks}")
        selesai = model.NewIntVar(durasi, jumlah_slot, f"selesai_{indeks}")
        interval = model.NewIntervalVar(mulai, durasi, selesai, f"interval_{indeks}")

        daftar_mulai.append(mulai)
        daftar_selesai.append(selesai)
        interval_mesin.append(interval)
        kebutuhan_daya.append(daya)
        durasi_slot.append(durasi)

    # Kendala utama: total daya mesin yang aktif bersamaan tidak boleh lewat batas.
    model.AddCumulative(interval_mesin, kebutuhan_daya, int(batas_watt))

    # Tujuan optimasi: menyelesaikan semua mesin secepat mungkin.
    waktu_selesai_terakhir = model.NewIntVar(0, jumlah_slot, "waktu_selesai_terakhir")
    for selesai in daftar_selesai:
        model.Add(waktu_selesai_terakhir >= selesai)
    model.Minimize(waktu_selesai_terakhir)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, "Jadwal tidak ditemukan. Coba perpanjang jam operasional atau periksa durasi dan batas daya."

    hasil = []
    for indeks, mesin in data.iterrows():
        mulai = menit_mulai + solver.Value(daftar_mulai[indeks]) * slot_menit
        selesai = menit_mulai + solver.Value(daftar_selesai[indeks]) * slot_menit
        hasil.append({
            "Nama Mesin": mesin["Nama Mesin"],
            "Mulai": fmt_jam(mulai),
            "Selesai": fmt_jam(selesai),
            "Daya (Watt)": int(mesin["Daya (Watt)"]),
            "Durasi (Jam)": round(durasi_slot[indeks] * slot_menit / 60, 2),
            "Mulai (menit)": mulai,
            "Selesai (menit)": selesai,
        })

    hasil_df = pd.DataFrame(hasil)
    hasil_df = hasil_df.sort_values("Mulai (menit)").reset_index(drop=True)
    status_teks = "optimal" if status == cp_model.OPTIMAL else "solusi layak"
    pesan = f"Jadwal berhasil dibuat. Status: {status_teks}. Targetnya menyelesaikan semua pekerjaan secepat mungkin."
    return hasil_df, pesan
