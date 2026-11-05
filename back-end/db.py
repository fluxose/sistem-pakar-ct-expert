
import os
import pymysql
from pymysql.cursors import DictCursor


# Konfigurasi database MySQL
# Sesuaikan jika pengaturan XAMPP di komputer berbeda.
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "sistem_pakar_ctscan")
DB_PORT = int(os.getenv("DB_PORT", "3306"))


def get_connection():
    """
    Membuat koneksi ke database MySQL.

    Mengembalikan:
        Koneksi MySQL dengan hasil query berbentuk dictionary.
    """
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
        connect_timeout=10
    )

    return connection
