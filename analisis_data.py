import pandas as pd

# Data mesin UMKM
data_mesin = pd.DataFrame({
    "Nama_Mesin": [
        "Mesin Potong",
        "Mesin Jahit",
        "Mesin Obras"
    ],
    "Daya_Watt": [1000, 500, 750],
    "Durasi_Jam": [2, 4, 2]
})

# Menghitung kebutuhan energi
data_mesin["Energi_Wh"] = (
    data_mesin["Daya_Watt"]
    * data_mesin["Durasi_Jam"]
)

# Menampilkan data
print("DATA MESIN UMKM")
print(data_mesin)

# Menghitung total daya
total_daya = data_mesin["Daya_Watt"].sum()

# Menghitung total energi
total_energi = data_mesin["Energi_Wh"].sum()

print("\nHASIL ANALISIS")
print("Jumlah mesin:", len(data_mesin))
print("Total daya:", total_daya, "Watt")
print("Total energi:", total_energi / 1000, "kWh")