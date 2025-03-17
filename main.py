from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, field_validator
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import pandas as pd
from datetime import datetime
from fastapi.responses import JSONResponse
import os

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
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")
DB_PORT = os.environ.get("DB_PORT")

try:
    engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

except OperationalError as e:
    db_connected = False


# Model untuk validasi input parameter
class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime
# Fungsi untuk mendapatkan menu favorit
def get_menu_favorites(start_date, end_date):
    query = f"""
        SELECT od.menu_id, m.name AS menu_name, m.image_uri, SUM(od.qty) AS qty
        FROM order_detail od
        JOIN menu m ON od.menu_id = m.id
        JOIN `order` o ON od.order_id = o.id
        JOIN reservasi r ON o.reservasi_id = r.id
        WHERE r.start BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY od.menu_id, m.name, m.image_uri
        ORDER BY qty DESC;
    """
    df = pd.read_sql(query, con=engine)
    return df




# Fungsi untuk mendapatkan performasi penjualan
def get_sales_performance(start_date, end_date):
    query = f"""
        SELECT DATE(r.start) AS sales_date,
               SUM(od.price * od.qty) AS total_sales,
               COUNT(DISTINCT o.id) AS total_orders,
               SUM(od.qty) AS total_items_sold
        FROM order_detail od
        JOIN `order` o ON od.order_id = o.id
        JOIN reservasi r ON o.reservasi_id = r.id
        WHERE r.start BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY sales_date
        ORDER BY sales_date;
    """
    df = pd.read_sql(query, con=engine)
    return df


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
@app.get("/menu_favorites/", responses={
    200: {
        "description": "Menu favorit berdasarkan rentang tanggal",
        "content": {
            "application/json": {
                "example": {
                    "code": 200,
                    "status": "SUCCESS",
                    "recordsTotal": 3,
                    "data": [
                        {"menu_name": "Latte", "qty": 50, "image_uri" : "https://picsum.photos/892/848"},
                        {"menu_name": "Espresso", "qty": 30, "image_uri" : "https://picsum.photos/892/238"},
                        {"menu_name": "Cappuccino", "qty": 20, "image_uri" : "https://picsum.photos/132/248"}
                    ],
                    "error": None
                }
            }
        }
    },
    400: {
        "description": "Kesalahan validasi input",
        "content": {
            "application/json": {
                "example": {
                    "code": 400,
                    "status": "VALIDATION ERROR",
                    "recordsTotal": 0,
                    "data": None,
                    "error": "Invalid date range. Ensure start_date is before end_date."
                }
            }
        }
    },
    500: {
        "description": "Kesalahan koneksi ke database",
        "content": {
            "application/json": {
                "example": {
                    "code": 500,
                    "status": "CONNECTION ERROR",
                    "recordsTotal": 0,
                    "data": None,
                    "error": "Failed to connect to the database."
                }
            }
        }
    }
})
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
        result = get_menu_favorites(start_date, end_date)
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
@app.get("/sales_performance/", responses={
    200: {
        "description": "Performa penjualan berdasarkan rentang tanggal",
        "content": {
            "application/json": {
                "example": {
                    "code": 200,
                    "status": "SUCCESS",
                    "recordsTotal": 2,
                    "data": [
                        {
                            "sales_date": "2024-01-01",
                            "total_sales": 150000.0,
                            "total_orders": 20,
                            "total_items_sold": 100
                        },
                        {
                            "sales_date": "2024-01-02",
                            "total_sales": 120000.0,
                            "total_orders": 15,
                            "total_items_sold": 80
                        }
                    ],
                    "error": None
                }
            }
        }
    },
    400: {
        "description": "Kesalahan validasi input",
        "content": {
            "application/json": {
                "example": {
                    "code": 400,
                    "status": "VALIDATION ERROR",
                    "recordsTotal": 0,
                    "data": None,
                    "error": "Invalid date range. Ensure start_date is before end_date."
                }
            }
        }
    },
    500: {
        "description": "Kesalahan koneksi ke database",
        "content": {
            "application/json": {
                "example": {
                    "code": 500,
                    "status": "CONNECTION ERROR",
                    "recordsTotal": 0,
                    "data": None,
                    "error": "Failed to connect to the database."
                }
            }
        }
    }
})
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
        result = get_sales_performance(start_date, end_date)
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
