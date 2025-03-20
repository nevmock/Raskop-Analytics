import requests

# Tentukan start_date dan end_date
params = {
    "start_date": "2025-03-01",  # Ganti dengan tanggal awal
    "end_date": "2025-03-20"     # Ganti dengan tanggal akhir
}

# Kirim permintaan GET dengan parameter query
response = requests.get("http://okay-hippopotamus-telkomuniversity231-317e9616.koyeb.app/menu_favorites", params=params)
# response = requests.get("http://okay-hippopotamus-telkomuniversity231-317e9616.koyeb.app/sales_performance", params=params)

# Cetak hasil JSON
print(response.json())
