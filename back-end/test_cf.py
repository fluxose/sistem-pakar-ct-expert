
"""
Pengujian mesin pakar Certainty Factor
Sistem Pakar Reaksi Media Kontras CT-Scan.

Pengujian meliputi kasus T1 sampai T6.
"""

import pytest

from cf_engine import hitung_certainty_factor


# =====================================================
# DATA GEJALA UNTUK PENGUJIAN
# Menggunakan data seed sesuai Fase 1.
# =====================================================

DATA_GEJALA = [
    {
        "kode_gejala": "G01",
        "tingkat": "cr",
        "nama_gejala": "Mual",
        "cf_pakar": 0.8,
        "kritis": False
    },
    {
        "kode_gejala": "G03",
        "tingkat": "cr",
        "nama_gejala": "Urtikaria (gatal)",
        "cf_pakar": 1.0,
        "kritis": False
    },
    {
        "kode_gejala": "G04",
        "tingkat": "cr",
        "nama_gejala": "Kemerahan pada kulit",
        "cf_pakar": 1.0,
        "kritis": False
    },
    {
        "kode_gejala": "G05",
        "tingkat": "cs",
        "nama_gejala": "Pingsan",
        "cf_pakar": 0.6,
        "kritis": False
    },
    {
        "kode_gejala": "G06",
        "tingkat": "cs",
        "nama_gejala": "Muntah",
        "cf_pakar": 0.6,
        "kritis": False
    },
    {
        "kode_gejala": "G09",
        "tingkat": "cs",
        "nama_gejala": "Sesak nafas",
        "cf_pakar": 0.8,
        "kritis": False
    },
    {
        "kode_gejala": "G14",
        "tingkat": "cb",
        "nama_gejala": "Edema paru",
        "cf_pakar": 0.4,
        "kritis": True
    },
    {
        "kode_gejala": "G17",
        "tingkat": "cb",
        "nama_gejala": "Kematian",
        "cf_pakar": 0.0,
        "kritis": True
    }
]


# =====================================================
# T1: MENGUJI GABUNGAN REAKSI RINGAN DAN SEDANG
# =====================================================

def test_T1_kombinasi_ringan_dan_sedang():

    pilihan = {
        "G01": 0.8,
        "G03": 0.8,
        "G04": 0.6,
        "G09": 0.4
    }

    hasil = hitung_certainty_factor(
        DATA_GEJALA,
        pilihan
    )

    assert hasil["persentase"]["cr"] == 97.12
    assert hasil["persentase"]["cs"] == 32.00
    assert hasil["persentase"]["cb"] == 0.00

    assert hasil["kesimpulan"] == "Ringan"
    assert hasil["ada_kritis"] is False


# =====================================================
# T2: SEMUA GEJALA TIDAK DIPILIH
# =====================================================

def test_T2_semua_nilai_nol():

    pilihan = {
        "G01": 0.0,
        "G03": 0.0,
        "G04": 0.0,
        "G05": 0.0,
        "G06": 0.0,
        "G09": 0.0,
        "G14": 0.0,
        "G17": 0.0
    }

    hasil = hitung_certainty_factor(
        DATA_GEJALA,
        pilihan
    )

    assert hasil["persentase"]["cr"] == 0.00
    assert hasil["persentase"]["cs"] == 0.00
    assert hasil["persentase"]["cb"] == 0.00

    assert hasil["kesimpulan"] == "Tidak ada reaksi terdeteksi"
    assert hasil["ada_kritis"] is False


# =====================================================
# T3: DUA GEJALA RINGAN DENGAN CF MAKSIMAL
# =====================================================

def test_T3_cf_ringan_seratus_persen():

    pilihan = {
        "G03": 1.0,
        "G04": 1.0
    }

    hasil = hitung_certainty_factor(
        DATA_GEJALA,
        pilihan
    )

    assert hasil["persentase"]["cr"] == 100.00
    assert hasil["kesimpulan"] == "Ringan"


# =====================================================
# T4: GEJALA KRITIS DENGAN CF POSITIF
# =====================================================

def test_T4_gejala_kritis_cf_positif():

    pilihan = {
        "G14": 1.0
    }

    hasil = hitung_certainty_factor(
        DATA_GEJALA,
        pilihan
    )

    assert hasil["persentase"]["cb"] == 40.00
    assert hasil["kesimpulan"] == "Berat"

    assert hasil["ada_kritis"] is True

    assert hasil["pesan_kritis"] == (
        "PERHATIAN: gejala kritis terdeteksi, "
        "segera hubungi dokter/radiolog"
    )


# =====================================================
# T5: GEJALA KRITIS DENGAN CF PAKAR NOL
# =====================================================

def test_T5_gejala_kritis_cf_nol():

    pilihan = {
        "G17": 1.0
    }

    hasil = hitung_certainty_factor(
        DATA_GEJALA,
        pilihan
    )

    assert hasil["persentase"]["cb"] == 0.00

    assert hasil["kesimpulan"] == (
        "Tidak ada reaksi terdeteksi"
    )

    # Meskipun CF gejala nol, peringatan tetap aktif.
    assert hasil["ada_kritis"] is True

    assert len(hasil["rincian"]) == 1

    assert hasil["rincian"][0]["cf_gejala"] == 0.00


# =====================================================
# T6: KOMBINASI DUA GEJALA SEDANG
# =====================================================

def test_T6_kombinasi_dua_gejala_sedang():

    pilihan = {
        "G05": 0.6,
        "G06": 0.6
    }

    hasil = hitung_certainty_factor(
        DATA_GEJALA,
        pilihan
    )

    assert hasil["persentase"]["cs"] == 59.04

    assert hasil["kesimpulan"] == "Sedang"


# =====================================================
# PENGUJIAN TAMBAHAN: VALIDASI NILAI KEYAKINAN
# =====================================================

@pytest.mark.parametrize(
    "nilai",
    [-0.1, 1.1, "0.8", None, True]
)
def test_nilai_keyakinan_tidak_valid(nilai):

    pilihan = {
        "G01": nilai
    }

    with pytest.raises(ValueError):

        hitung_certainty_factor(
            DATA_GEJALA,
            pilihan
        )


# =====================================================
# PENGUJIAN TAMBAHAN: GEJALA TIDAK DIKENAL
# =====================================================

def test_gejala_tidak_dikenal():

    pilihan = {
        "G99": 0.8
    }

    # Kode G99 tidak ada di DATA_GEJALA.
    # Sistem tidak menghitung gejala yang tidak terdaftar.
    hasil = hitung_certainty_factor(
        DATA_GEJALA,
        pilihan
    )

    assert hasil["kesimpulan"] == (
        "Tidak ada reaksi terdeteksi"
    )
