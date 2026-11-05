
"""
Mesin Pakar Sistem Penentuan Tingkat Reaksi
Media Kontras CT-Scan menggunakan metode Certainty Factor.

File ini berdiri sendiri dan tidak bergantung pada Flask
maupun database.
"""


# Urutan tingkat reaksi dari ringan sampai berat.
TINGKAT_REAKSI = {
    "cr": "Ringan",
    "cs": "Sedang",
    "cb": "Berat"
}

# Prioritas digunakan jika dua tingkat memiliki CF yang sama.
PRIORITAS_TINGKAT = {
    "cr": 1,
    "cs": 2,
    "cb": 3
}


def validasi_cf_user(cf_user: float) -> None:
    """
    Memastikan nilai keyakinan pengguna berada pada 0 sampai 1.
    """
    if not isinstance(cf_user, (int, float)) or isinstance(cf_user, bool):
        raise ValueError("CF pengguna harus berupa angka.")

    if not 0 <= cf_user <= 1:
        raise ValueError("CF pengguna harus antara 0 dan 1.")


def hitung_cf_gejala(cf_pakar: float, cf_user: float) -> float:
    """
    Menghitung CF satu gejala.

    Rumus:
    CF gejala = CF pakar x CF pengguna
    """
    validasi_cf_user(cf_user)

    if not isinstance(cf_pakar, (int, float)) or isinstance(cf_pakar, bool):
        raise ValueError("CF pakar harus berupa angka.")

    if not 0 <= cf_pakar <= 1:
        raise ValueError("CF pakar harus antara 0 dan 1.")

    return cf_pakar * cf_user


def kombinasi_cf(cf_lama: float, cf_baru: float) -> float:
    """
    Menggabungkan dua nilai CF dalam tingkat reaksi yang sama.

    Rumus:
    CF combine = CF lama + CF baru x (1 - CF lama)
    """
    return cf_lama + (cf_baru * (1 - cf_lama))


def hitung_certainty_factor(
    data_gejala: list,
    pilihan_gejala: dict
) -> dict:
    """
    Menghitung tingkat reaksi media kontras CT-Scan.

    Parameter:
    - data_gejala:
      Daftar data gejala dari database.

    - pilihan_gejala:
      Dictionary berisi kode gejala dan CF pengguna.
      Contoh: {"G01": 0.8, "G03": 1.0}

    Hasil:
    - CF akhir setiap tingkat.
    - Persentase setiap tingkat.
    - Kesimpulan.
    - Status gejala kritis.
    - Rincian perhitungan setiap gejala.
    """

    # Validasi format pilihan gejala.
    if not isinstance(pilihan_gejala, dict):
        raise ValueError("Pilihan gejala harus berupa dictionary.")

    # Menyiapkan nilai awal CF untuk setiap tingkat.
    hasil_cf = {
        "cr": 0.0,
        "cs": 0.0,
        "cb": 0.0
    }

    # Menyimpan rincian perhitungan setiap gejala.
    rincian = []

    # Penanda jika ditemukan gejala kritis.
    ada_kritis = False

    # Menyimpan kode gejala agar tidak ada kode duplikat.
    kode_terdaftar = set()

    # Memeriksa setiap gejala yang tersedia.
    for gejala in data_gejala:

        kode = gejala["kode_gejala"]

        # Memastikan tidak ada kode gejala ganda.
        if kode in kode_terdaftar:
            raise ValueError(f"Kode gejala {kode} duplikat.")

        kode_terdaftar.add(kode)

        # Mengambil nilai keyakinan pengguna.
        cf_user = pilihan_gejala.get(kode, 0.0)

        validasi_cf_user(cf_user)

        # Gejala dengan nilai 0 tidak memengaruhi perhitungan.
        if cf_user == 0:
            continue

        # Mengambil informasi gejala.
        tingkat = gejala["tingkat"]
        cf_pakar = gejala["cf_pakar"]
        kritis = bool(gejala["kritis"])

        # Memastikan tingkat reaksi valid.
        if tingkat not in TINGKAT_REAKSI:
            raise ValueError(f"Tingkat reaksi {tingkat} tidak valid.")

        # Menghitung CF gejala.
        cf_gejala = hitung_cf_gejala(
            cf_pakar,
            cf_user
        )

        # Menggabungkan CF berdasarkan tingkat reaksi.
        hasil_cf[tingkat] = kombinasi_cf(
            hasil_cf[tingkat],
            cf_gejala
        )

        # Safety override:
        # Gejala kritis tetap memicu peringatan meskipun
        # CF gejalanya bernilai nol.
        if kritis:
            ada_kritis = True

        # Menyimpan rincian perhitungan.
        rincian.append({
            "kode_gejala": kode,
            "nama_gejala": gejala["nama_gejala"],
            "tingkat": tingkat,
            "cf_pakar": round(cf_pakar, 4),
            "cf_user": round(cf_user, 4),
            "cf_gejala": round(cf_gejala, 4)
        })

    # Mengubah hasil CF menjadi empat angka desimal.
    hasil_cf = {
        tingkat: round(nilai, 4)
        for tingkat, nilai in hasil_cf.items()
    }

    # Menghitung persentase setiap tingkat.
    persentase = {
        tingkat: round(nilai * 100, 2)
        for tingkat, nilai in hasil_cf.items()
    }

    # Memeriksa apakah seluruh nilai CF adalah nol.
    if all(nilai == 0 for nilai in hasil_cf.values()):
        kesimpulan = "Tidak ada reaksi terdeteksi"

    else:
        # Mencari nilai CF tertinggi.
        cf_tertinggi = max(hasil_cf.values())

        # Mengambil semua tingkat yang memiliki nilai tertinggi.
        kandidat = [
            tingkat
            for tingkat, nilai in hasil_cf.items()
            if nilai == cf_tertinggi
        ]

        # Jika seri, pilih tingkat yang lebih berat.
        tingkat_terpilih = max(
            kandidat,
            key=lambda tingkat: PRIORITAS_TINGKAT[tingkat]
        )

        kesimpulan = TINGKAT_REAKSI[tingkat_terpilih]

    # Menghasilkan seluruh hasil perhitungan.
    return {
        "cf_akhir": hasil_cf,
        "persentase": persentase,
        "kesimpulan": kesimpulan,
        "ada_kritis": ada_kritis,
        "pesan_kritis": (
            "PERHATIAN: gejala kritis terdeteksi, "
            "segera hubungi dokter/radiolog"
            if ada_kritis else None
        ),
        "rincian": rincian
    }
