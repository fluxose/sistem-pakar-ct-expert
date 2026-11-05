
from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path
from datetime import date
from decimal import Decimal
import re
import pymysql

from db import get_connection
from cf_engine import hitung_certainty_factor


# =========================================================
# KONFIGURASI APLIKASI
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "front-end"

app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path=""
)


# Nilai CF terminator yang diperbolehkan
NILAI_TERMINATOR = {0.0, 0.2, 0.4, 0.6, 0.8, 1.0}

# Tingkat reaksi yang diperbolehkan
TINGKAT_VALID = {"cr", "cs", "cb"}


# =========================================================
# FUNGSI BANTU
# =========================================================

def respons_error(pesan, status=400):
    """Membuat respons JSON ketika terjadi kesalahan."""
    return jsonify({
        "status": "error",
        "message": pesan
    }), status


def validasi_cf_user(nilai):
    """
    Memeriksa apakah nilai CF pengguna sesuai dengan
    pilihan terminator yang tersedia.
    """
    if isinstance(nilai, bool):
        return None

    try:
        nilai = float(nilai)
    except (ValueError, TypeError):
        return None

    if not 0 <= nilai <= 1:
        return None

    nilai = round(nilai, 2)

    if nilai not in NILAI_TERMINATOR:
        return None

    return nilai


def ambil_rekomendasi(cursor, kesimpulan):
    """Mengambil rekomendasi berdasarkan tingkat kesimpulan."""

    tingkat = {
        "Ringan": "cr",
        "Sedang": "cs",
        "Berat": "cb"
    }.get(kesimpulan)

    if tingkat is None:
        return []

    cursor.execute(
        """
        SELECT tingkat, tindakan, status_validasi
        FROM rekomendasi
        WHERE tingkat = %s
        """,
        (tingkat,)
    )

    return cursor.fetchall()



def konversi_gejala(data):
    """
    Mengubah data gejala dari MySQL menjadi format
    yang dapat diproses oleh mesin CF.
    """
    hasil = []

    for item in data:
        hasil.append({
            "kode_gejala": item["kode_gejala"],
            "nama_gejala": item["nama_gejala"],
            "tingkat": item["tingkat"],
            "cf_pakar": float(item["cf_pakar"]),
            "kritis": bool(item["kritis"])
        })

    return hasil


def ambil_data_json():
    """Memastikan permintaan membawa JSON berbentuk objek."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return None

    return data

@app.route("/")
def halaman_utama():
    """Menampilkan halaman utama aplikasi."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/api/gejala", methods=["GET"])
def get_gejala():
    """Mengambil seluruh data gejala dari database."""

    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT kode_gejala, nama_gejala,
                       tingkat, cf_pakar, kritis
                FROM gejala
                ORDER BY FIELD(tingkat, 'cr', 'cs', 'cb'),
                         kode_gejala
                """
            )

            data = cursor.fetchall()

            for item in data:
                item["cf_pakar"] = float(item["cf_pakar"])
                item["kritis"] = bool(item["kritis"])

        return jsonify({
            "status": "success",
            "data": data
        })

    except pymysql.MySQLError:
        return respons_error(
            "Tidak dapat mengambil data gejala dari database.",
            500
        )

    finally:
        if connection:
            connection.close()


@app.route("/api/terminator", methods=["GET"])
def get_terminator():
    """Mengambil daftar nilai terminator."""

    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id_terminator, keterangan, nilai
                FROM nilai_terminator
                ORDER BY nilai
                """
            )

            data = cursor.fetchall()

            for item in data:
                item["nilai"] = float(item["nilai"])

        return jsonify({
            "status": "success",
            "data": data
        })

    except pymysql.MySQLError:
        return respons_error(
            "Tidak dapat mengambil data terminator.",
            500
        )

    finally:
        if connection:
            connection.close()


@app.route("/api/konsultasi", methods=["POST"])
def buat_konsultasi():
    """
    Menerima data pasien, menghitung CF,
    dan menyimpan hasil konsultasi.
    """

    data = ambil_data_json()

    if data is None:
        return respons_error("Format data JSON tidak valid.")


    no_rm = str(data.get("no_rm", "")).strip()
    nama_pasien = str(data.get("nama_pasien", "")).strip()
    jenis_kelamin = data.get("jenis_kelamin")
    usia = data.get("usia")
    tanggal = data.get("tanggal")

    if not no_rm or not nama_pasien:
        return respons_error(
            "Nomor rekam medis dan nama pasien wajib diisi."
        )

    if jenis_kelamin not in ("L", "P"):
        return respons_error(
            "Jenis kelamin harus L atau P."
        )

    if isinstance(usia, bool) or not isinstance(usia, int):
        return respons_error("Usia harus berupa bilangan bulat.")

    if usia < 0 or usia > 255:
        return respons_error("Usia harus berada pada rentang 0–255.")

    try:
        tanggal_valid = date.fromisoformat(str(tanggal))
    except (ValueError, TypeError):
        return respons_error(
            "Format tanggal tidak valid. Gunakan YYYY-MM-DD."
        )

    pilihan_gejala = data.get("gejala")

    if not isinstance(pilihan_gejala, dict):
        return respons_error(
            "Pilihan gejala harus berbentuk objek JSON."
        )

    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:

            # Ambil seluruh gejala yang terdaftar
            cursor.execute(
                """
                SELECT kode_gejala, nama_gejala,
                       tingkat, cf_pakar, kritis
                FROM gejala
                """
            )

            data_gejala = konversi_gejala(cursor.fetchall())

            kode_terdaftar = {
                item["kode_gejala"] for item in data_gejala
            }

            # Tolak kode gejala yang tidak terdaftar
            kode_dikirim = set(pilihan_gejala.keys())
            kode_tidak_valid = kode_dikirim - kode_terdaftar

            if kode_tidak_valid:
                return respons_error(
                    "Kode gejala tidak terdaftar: "
                    + ", ".join(sorted(kode_tidak_valid))
                )

            # Validasi setiap nilai CF pengguna
            pilihan_valid = {}

            for kode, nilai in pilihan_gejala.items():
                nilai_valid = validasi_cf_user(nilai)

                if nilai_valid is None:
                    return respons_error(
                        f"Nilai terminator untuk {kode} tidak valid."
                    )

                pilihan_valid[kode] = nilai_valid

            

            hasil_cf = hitung_certainty_factor(
                data_gejala,
                pilihan_valid
            )

            

            cf_akhir = hasil_cf["cf_akhir"]

            cursor.execute(
                """
                INSERT INTO konsultasi (
                    no_rm,
                    nama_pasien,
                    usia,
                    jenis_kelamin,
                    tanggal,
                    cf_ringan,
                    cf_sedang,
                    cf_berat,
                    kesimpulan,
                    ada_kritis
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    no_rm,
                    nama_pasien,
                    usia,
                    jenis_kelamin,
                    tanggal_valid,
                    cf_akhir["cr"],
                    cf_akhir["cs"],
                    cf_akhir["cb"],
                    hasil_cf["kesimpulan"],
                    hasil_cf["ada_kritis"]
                )
            )

            id_konsultasi = cursor.lastrowid

            

            for rincian in hasil_cf["rincian"]:
                if rincian["cf_user"] <= 0:
                    continue

                cursor.execute(
                    """
                    INSERT INTO detail_konsultasi (
                        id_konsultasi,
                        kode_gejala,
                        cf_user,
                        cf_gejala
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        id_konsultasi,
                        rincian["kode_gejala"],
                        rincian["cf_user"],
                        rincian["cf_gejala"]
                    )
                )

            # Ambil rekomendasi sesuai kesimpulan
            rekomendasi = ambil_rekomendasi(
                cursor,
                hasil_cf["kesimpulan"]
            )

            connection.commit()

            return jsonify({
                "status": "success",
                "message": "Konsultasi berhasil disimpan.",
                "data": {
                    "id_konsultasi": id_konsultasi,
                    "cf_akhir": hasil_cf["cf_akhir"],
                    "persentase": hasil_cf["persentase"],
                    "kesimpulan": hasil_cf["kesimpulan"],
                    "ada_kritis": hasil_cf["ada_kritis"],
                    "pesan_kritis": hasil_cf["pesan_kritis"],
                    "rincian": hasil_cf["rincian"],
                    "rekomendasi": rekomendasi
                }
            }), 201

    except pymysql.MySQLError as e:
        if connection:
            connection.rollback()

        app.logger.exception("ERROR MYSQL SAAT MENYIMPAN KONSULTASI")

        return respons_error(
            "Terjadi kesalahan saat menyimpan konsultasi ke database: "
            + str(e),
            500
        )

    except Exception:
        if connection:
            connection.rollback()

        app.logger.exception("Kesalahan saat memproses konsultasi.")

        return respons_error(
            "Terjadi kesalahan saat menghitung hasil konsultasi.",
            500
        )

    finally:
        if connection:
            connection.close()




@app.route("/api/konsultasi", methods=["GET"])
def get_riwayat():
    """
    Menampilkan riwayat konsultasi.
    Mendukung pencarian berdasarkan nama atau nomor RM.
    """

    keyword = request.args.get("q", "").strip()

    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id_konsultasi,
                    no_rm,
                    nama_pasien,
                    usia,
                    jenis_kelamin,
                    tanggal,
                    kesimpulan,
                    cf_ringan,
                    cf_sedang,
                    cf_berat
                FROM konsultasi
                WHERE nama_pasien LIKE %s
                   OR no_rm LIKE %s
                ORDER BY tanggal DESC, id_konsultasi DESC
                """,
                (f"%{keyword}%", f"%{keyword}%")
            )

            data = cursor.fetchall()

            for item in data:
                item["cf_ringan"] = float(item["cf_ringan"])
                item["cf_sedang"] = float(item["cf_sedang"])
                item["cf_berat"] = float(item["cf_berat"])

                if item["tanggal"]:
                    item["tanggal"] = item["tanggal"].isoformat()

        return jsonify({
            "status": "success",
            "data": data
        })

    except pymysql.MySQLError:
        return respons_error(
            "Tidak dapat mengambil riwayat konsultasi.",
            500
        )

    finally:
        if connection:
            connection.close()




@app.route("/api/konsultasi/<int:id_konsultasi>", methods=["GET"])
def get_detail_konsultasi(id_konsultasi):
    """Menampilkan detail hasil konsultasi berdasarkan ID."""

    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT *
                FROM konsultasi
                WHERE id_konsultasi = %s
                """,
                (id_konsultasi,)
            )

            konsultasi = cursor.fetchone()

            if not konsultasi:
                return respons_error(
                    "Data konsultasi tidak ditemukan.",
                    404
                )

            # Ambil detail gejala yang dipilih
            cursor.execute(
                """
                SELECT
                    d.kode_gejala,
                    g.nama_gejala,
                    g.tingkat,
                    g.cf_pakar,
                    g.kritis,
                    d.cf_user,
                    d.cf_gejala
                FROM detail_konsultasi d
                JOIN gejala g
                    ON d.kode_gejala = g.kode_gejala
                WHERE d.id_konsultasi = %s
                ORDER BY g.kode_gejala
                """,
                (id_konsultasi,)
            )

            rincian = cursor.fetchall()

            # Ambil rekomendasi sesuai kesimpulan
            rekomendasi = ambil_rekomendasi(
                cursor,
                konsultasi["kesimpulan"]
            )

            # Konversi tipe data agar aman dikirim sebagai JSON
            for kolom in (
                "cf_ringan",
                "cf_sedang",
                "cf_berat"
            ):
                konsultasi[kolom] = float(konsultasi[kolom])

            konsultasi["tanggal"] = (
                konsultasi["tanggal"].isoformat()
                if konsultasi["tanggal"] else None
            )

            for item in rincian:
                item["cf_pakar"] = float(item["cf_pakar"])
                item["cf_user"] = float(item["cf_user"])
                item["cf_gejala"] = float(item["cf_gejala"])
                item["kritis"] = bool(item["kritis"])

            return jsonify({
                "status": "success",
                "data": {
                    "konsultasi": konsultasi,
                    "rincian": rincian,
                    "rekomendasi": rekomendasi
                }
            })

    except pymysql.MySQLError:
        return respons_error(
            "Tidak dapat mengambil detail konsultasi.",
            500
        )

    finally:
        if connection:
            connection.close()



@app.route("/api/gejala", methods=["POST"])
def tambah_gejala():
    """Menambahkan data gejala baru."""

    data = ambil_data_json()

    if data is None:
        return respons_error("Format data JSON tidak valid.")

    kode = str(data.get("kode_gejala", "")).strip().upper()
    nama = str(data.get("nama_gejala", "")).strip()
    tingkat = data.get("tingkat")
    kritis = data.get("kritis")
    cf_pakar = data.get("cf_pakar")

    if not re.fullmatch(r"G\d{2,}", kode):
        return respons_error(
            "Kode gejala harus menggunakan format G01, G02, dan seterusnya."
        )

    if not nama:
        return respons_error("Nama gejala wajib diisi.")

    if tingkat not in TINGKAT_VALID:
        return respons_error("Tingkat harus cr, cs, atau cb.")

    if not isinstance(kritis, bool):
        return respons_error("Status kritis harus berupa true atau false.")

    if isinstance(cf_pakar, bool):
        return respons_error("Nilai CF pakar tidak valid.")

    try:
        cf_pakar = float(cf_pakar)
    except (ValueError, TypeError):
        return respons_error("Nilai CF pakar harus berupa angka.")

    if not 0 <= cf_pakar <= 1:
        return respons_error("Nilai CF pakar harus antara 0 sampai 1.")

    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO gejala (
                    kode_gejala,
                    nama_gejala,
                    tingkat,
                    cf_pakar,
                    kritis
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (kode, nama, tingkat, cf_pakar, kritis)
            )

        connection.commit()

        return jsonify({
            "status": "success",
            "message": "Gejala berhasil ditambahkan."
        }), 201

    except pymysql.err.IntegrityError:
        if connection:
            connection.rollback()

        return respons_error(
            "Kode gejala sudah digunakan atau data masih terkait dengan riwayat.",
            409
        )

    except pymysql.MySQLError:
        if connection:
            connection.rollback()

        return respons_error(
            "Gagal menambahkan gejala.",
            500
        )

    finally:
        if connection:
            connection.close()




@app.route("/api/gejala/<kode_gejala>", methods=["PUT"])
def ubah_gejala(kode_gejala):
    """Mengubah informasi gejala berdasarkan kode."""

    data = ambil_data_json()

    if data is None:
        return respons_error("Format data JSON tidak valid.")

    nama = str(data.get("nama_gejala", "")).strip()
    tingkat = data.get("tingkat")
    kritis = data.get("kritis")
    cf_pakar = data.get("cf_pakar")

    if not nama:
        return respons_error("Nama gejala wajib diisi.")

    if tingkat not in TINGKAT_VALID:
        return respons_error("Tingkat harus cr, cs, atau cb.")

    if not isinstance(kritis, bool):
        return respons_error("Status kritis harus berupa true atau false.")

    if isinstance(cf_pakar, bool):
        return respons_error("Nilai CF pakar tidak valid.")

    try:
        cf_pakar = float(cf_pakar)
    except (ValueError, TypeError):
        return respons_error("Nilai CF pakar harus berupa angka.")

    if not 0 <= cf_pakar <= 1:
        return respons_error("Nilai CF pakar harus antara 0 sampai 1.")

    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE gejala
                SET nama_gejala = %s,
                    tingkat = %s,
                    cf_pakar = %s,
                    kritis = %s
                WHERE kode_gejala = %s
                """,
                (nama, tingkat, cf_pakar, kritis, kode_gejala)
            )

            if cursor.rowcount == 0:
                connection.rollback()

                return respons_error(
                    "Gejala tidak ditemukan atau tidak ada perubahan.",
                    404
                )

        connection.commit()

        return jsonify({
            "status": "success",
            "message": "Gejala berhasil diperbarui."
        })

    except pymysql.MySQLError:
        if connection:
            connection.rollback()

        return respons_error(
            "Gagal memperbarui gejala.",
            500
        )

    finally:
        if connection:
            connection.close()



@app.route("/api/gejala/<kode_gejala>", methods=["DELETE"])
def hapus_gejala(kode_gejala):
    """Menghapus gejala berdasarkan kode."""

    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM gejala
                WHERE kode_gejala = %s
                """,
                (kode_gejala,)
            )

            if cursor.rowcount == 0:
                connection.rollback()

                return respons_error(
                    "Gejala tidak ditemukan.",
                    404
                )

        connection.commit()

        return jsonify({
            "status": "success",
            "message": "Gejala berhasil dihapus."
        })

    except pymysql.err.IntegrityError:
        if connection:
            connection.rollback()

        return respons_error(
            "Gejala tidak dapat dihapus karena sudah digunakan dalam riwayat konsultasi.",
            409
        )

    except pymysql.MySQLError:
        if connection:
            connection.rollback()

        return respons_error(
            "Gagal menghapus gejala.",
            500
        )

    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
