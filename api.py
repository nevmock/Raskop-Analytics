from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, field_validator
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import pandas as pd
from datetime import datetime
from fastapi.responses import JSONResponse

# Inisialisasi FastAPI
app = FastAPI()


# Status koneksi database
db_connected = True
# Tambahkan Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Parameter koneksi database
DB_HOST = "127.0.0.1"
DB_USER = "root"
DB_PASSWORD = "Shadow1794"
DB_NAME = "rasakopi"
DB_PORT = 3307

try:
    engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    # Daftar tabel yang ingin dibaca
    tables = ["menu", "order_detail", "reservasi", "`order`"]  # Ganti dengan nama tabel di database

    # Membaca tabel ke dalam DataFrame
    dataframes = {}
    for table in tables:
        query = f"SELECT * FROM {table}"
        dataframes[table] = pd.read_sql(query, con=engine)

    # Load data
    menu = dataframes["menu"]
    order_detail = dataframes["order_detail"]
    reservasi = dataframes["reservasi"]
    order = dataframes["`order`"]

    # Transformasi data untuk analisis
    filter_menu = menu[['id', 'name', 'category']].rename(columns={'id': 'menu_id', 'name': 'menu_name'})
    filter_order = order[['id', 'reservasi_id', 'order_by']].rename(columns={'id': 'order_id'})
    filter_reservasi = reservasi[['id', 'start']].rename(columns={'start': 'date', 'id': 'reservasi_id'})

    menu_fav_by_date = pd.merge(order_detail, filter_menu, how='left', on='menu_id')
    menu_fav_by_date = pd.merge(menu_fav_by_date, filter_order, how='left', on='order_id')
    menu_fav_by_date = pd.merge(menu_fav_by_date, filter_reservasi, how='left', on='reservasi_id')
    menu_fav_by_date['date'] = pd.to_datetime(menu_fav_by_date['date'], format='%Y-%m-%d %H:%M:%S')

except OperationalError as e:
    db_connected = False


# Model untuk validasi input parameter
class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime
# Fungsi untuk mendapatkan menu favorit
def get_menu_favorites(data, start_date, end_date):
    filtered_data = data[
        (data["date"] >= pd.to_datetime(start_date)) & 
        (data["date"] <= pd.to_datetime(end_date))
    ]
    aggregated_data = (
        filtered_data.groupby("menu_name")["qty"]
        .sum()
        .reset_index()
        .sort_values(by="qty", ascending=False)
    )
    return aggregated_data

# Fungsi untuk mendapatkan performasi penjualan
def get_sales_performance(data, start_date, end_date):
    # Filter data berdasarkan rentang tanggal
    filtered_data = data[
        (data["date"] >= pd.to_datetime(start_date)) & 
        (data["date"] <= pd.to_datetime(end_date))
    ]
    # Agregasi data
    aggregated_data = (
        filtered_data.groupby(filtered_data["date"].dt.date)
        .agg(
            total_sales=("price", "sum"),  # Total pendapatan
            total_orders=("order_id", "nunique"),  # Total jumlah pesanan unik
            total_items_sold=("qty", "sum")  # Total jumlah item terjual
        )
        .reset_index()
        .rename(columns={"date": "sales_date"})
    )
    return aggregated_data

# Custom exception handler untuk validasi input
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "code": 400,
            "status": "VALLIDATION ERROR",
            "recordsTotal": 0,
            "data": None,
            "error": str(exc)
        },
    )

# Endpoint untuk menu favorit
@app.get("/menu_favorites/")
def menu_favorites(params: DateRange = Depends()):
    if not db_connected:
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "status": "CONNECTION ERROR",
                "recordsTotal": 0,
                "data": None,
                "error": "Failed to connect to the database.",
            },
        )
    try:
        start_date = params.start_date
        end_date = params.end_date
        result = get_menu_favorites(menu_fav_by_date, start_date, end_date)
        return {
            "code": 200,
            "status": "SUCCESS",
            "recordsTotal": len(result),
            "data": result.to_dict(orient="records"),
            "error": None
        }
    except RequestValidationError as rve:
        return JSONResponse(
            status_code=400,
            content={
                "code": 400,
                "status": "VALIDATION ERROR",
                "recordsTotal": 0,
                "data": None,
                "error": str(rve),
            },
        )
    except Exception as e:
        return {
            "code": 500,
            "status": "CONNECTION ERROR",
            "recordsTotal": 0,
            "data": None,
            "error": str(e)
        }

# Endpoint untuk Dashboard Performasi Penjualan
@app.get("/sales_performance/")
def sales_performance(params: DateRange = Depends()):
    if not db_connected:
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "status": "CONNECTION ERROR",
                "recordsTotal": 0,
                "data": None,
                "error": "Failed to connect to the database.",
            },
        )
    try:
        start_date = params.start_date
        end_date = params.end_date
        result = get_sales_performance(menu_fav_by_date, start_date, end_date)
        return {
            "code": 200,
            "status": "SUCCESS",
            "recordsTotal": len(result),
            "data": result.to_dict(orient="records"),
            "error": None
        }
    except RequestValidationError as rve:
        return JSONResponse(
            status_code=400,
            content={
                "code": 400,
                "status": "VALIDATION ERROR",
                "recordsTotal": 0,
                "data": None,
                "error": str(rve),
            },
        )
    except Exception as e:
        return {
            "code": 500,
            "status": "CONNECTION ERROR",
            "recordsTotal": 0,
            "data": None,
            "error": str(e)
        }
