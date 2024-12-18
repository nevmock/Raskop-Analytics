# Gunakan image Python yang ringan
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Tentukan direktori kerja di dalam container
WORKDIR /app

# Salin semua file ke dalam direktori kerja
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ekspos port 8080 (atau sesuaikan dengan port yang Anda gunakan di aplikasi)
EXPOSE 8080

# Perintah untuk menjalankan aplikasi
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
